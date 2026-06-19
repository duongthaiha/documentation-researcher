"""Trigger the FSI coverage evaluation on Azure AI Foundry (cloud evaluation).

This runner uses the **Foundry SDK** (``azure-ai-projects``) together with the
project's OpenAI-compatible evals client to:

1. Register the FSI coverage logic as a **code-based custom evaluator** in the
   Foundry project (the topic vocabulary is sourced from
   :mod:`doc_reviewer.eval.fsi_coverage_evaluator`, keeping a single source of
   truth).
2. Upload the ``fsi_customer_eval.jsonl`` dataset as inline eval data.
3. Create an evaluation and a run, optionally including built-in quality
   evaluators (relevance / coherence).
4. Poll the run to completion and print per-criterion scores plus an aggregate
   summary. Results are also visible in the Foundry portal.

Authentication uses :class:`~azure.identity.DefaultAzureCredential` (Azure CLI /
VS Code / managed identity). Set ``AZURE_TOKEN_CREDENTIALS=prod`` in production.

Environment variables:
    AZURE_AI_PROJECT_ENDPOINT        Foundry project endpoint (required).
    AZURE_AI_MODEL_DEPLOYMENT_NAME   Model deployment for built-in/LLM evaluators
                                     (default: gpt-4o).

Usage::

    python -m doc_reviewer.eval.run_foundry_eval
    python -m doc_reviewer.eval.run_foundry_eval --builtins --threshold 0.7
    python -m doc_reviewer.eval.run_foundry_eval --dataset path/to/data.jsonl

Requires the optional ``eval`` dependencies::

    pip install "doc-reviewer[eval]"   # or: pip install azure-ai-projects openai
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from doc_reviewer.eval.fsi_coverage_evaluator import TOPIC_PATTERNS

load_dotenv()

EVALUATOR_NAME = "fsi_coverage_evaluator"
DEFAULT_DATASET = (
    Path(__file__).resolve().parent / "dataset" / "fsi_customer_eval.jsonl"
)
DEFAULT_THRESHOLD = 0.7
DEFAULT_DEPLOYMENT = "gpt-4o"


# ---------------------------------------------------------------------------
# Custom evaluator code (runs in Foundry's sandbox)
# ---------------------------------------------------------------------------
def build_evaluator_code(threshold: float) -> str:
    """Generate the self-contained ``grade(sample, item)`` code for Foundry.

    The topic patterns are serialized from the local single source of truth so
    the cloud evaluator and the local evaluator stay in sync.
    """
    # json.dumps produces a Python-literal-compatible dict (strings/lists only),
    # with backslashes correctly escaped for the embedded regex patterns.
    patterns_literal = json.dumps(TOPIC_PATTERNS, indent=4)
    # NOTE: the Foundry/AOAI Python grader sandbox forbids the ``compile``
    # builtin, so we must NOT use ``re.compile`` here — call ``re.search`` with
    # the ``re.IGNORECASE`` flag directly instead.
    return (
        "import re\n\n"
        f"TOPIC_PATTERNS = {patterns_literal}\n\n"
        f"THRESHOLD = {threshold!r}\n\n"
        "def _detect(text):\n"
        "    if not text:\n"
        "        return set()\n"
        "    found = set()\n"
        "    for topic, patterns in TOPIC_PATTERNS.items():\n"
        "        for p in patterns:\n"
        "            if re.search(p, text, re.IGNORECASE):\n"
        "                found.add(topic)\n"
        "                break\n"
        "    return found\n\n"
        "def _norm(topics):\n"
        "    if topics is None:\n"
        "        return set()\n"
        "    if isinstance(topics, str):\n"
        "        return {p for p in re.split(r'[,;\\s]+', topics.strip()) if p}\n"
        "    return {str(t).strip() for t in topics if str(t).strip()}\n\n"
        "def grade(sample, item) -> dict:\n"
        "    expected = _norm(item.get('expected_topics'))\n"
        "    if not expected and item.get('ground_truth'):\n"
        "        expected = _detect(item.get('ground_truth'))\n"
        "    detected = _detect(item.get('response', ''))\n"
        "    matched = sorted(expected & detected)\n"
        "    missing = sorted(expected - detected)\n"
        "    total = len(expected)\n"
        "    score = (len(matched) / total) if total else 0.0\n"
        "    return {\n"
        "        'fsi_coverage_score': round(score, 4),\n"
        "        'passed': bool(total) and score >= THRESHOLD,\n"
        "        'matched_count': len(matched),\n"
        "        'expected_count': total,\n"
        "        'missing_topics': ', '.join(missing) if missing else 'none',\n"
        "    }\n"
    )


def build_python_grader_source(threshold: float) -> str:
    """Generate an OpenAI **Python grader** script that returns a float score.

    Unlike the catalog evaluator (which returns a dict of metrics), an OpenAI
    Python grader's ``grade(sample, item)`` must return a single numeric score.
    This is sent inline with the run, so it always uses this exact compile-free
    code — avoiding any catalog version-resolution ambiguity.
    """
    patterns_literal = json.dumps(TOPIC_PATTERNS, indent=4)
    # The sandbox forbids the ``compile`` builtin, so use ``re.search`` directly.
    return (
        "import re\n\n"
        f"TOPIC_PATTERNS = {patterns_literal}\n\n"
        "def _detect(text):\n"
        "    if not text:\n"
        "        return set()\n"
        "    found = set()\n"
        "    for topic, patterns in TOPIC_PATTERNS.items():\n"
        "        for p in patterns:\n"
        "            if re.search(p, text, re.IGNORECASE):\n"
        "                found.add(topic)\n"
        "                break\n"
        "    return found\n\n"
        "def _norm(topics):\n"
        "    if topics is None:\n"
        "        return set()\n"
        "    if isinstance(topics, str):\n"
        "        return {p for p in re.split(r'[,;\\s]+', topics.strip()) if p}\n"
        "    return {str(t).strip() for t in topics if str(t).strip()}\n\n"
        "def grade(sample, item) -> float:\n"
        "    expected = _norm(item.get('expected_topics'))\n"
        "    if not expected and item.get('ground_truth'):\n"
        "        expected = _detect(item.get('ground_truth'))\n"
        "    detected = _detect(item.get('response', ''))\n"
        "    total = len(expected)\n"
        "    if not total:\n"
        "        return 0.0\n"
        "    return round(len(expected & detected) / total, 4)\n"
    )


def register_evaluator(project_client: Any, threshold: float) -> str:
    """Register (version) the FSI coverage code-based evaluator in Foundry.

    Returns the evaluator name to reference in testing criteria.
    """
    from azure.ai.projects.models import (
        CodeBasedEvaluatorDefinition,
        EvaluatorCategory,
        EvaluatorMetric,
        EvaluatorMetricDirection,
        EvaluatorMetricType,
        EvaluatorType,
        EvaluatorVersion,
    )

    definition = CodeBasedEvaluatorDefinition(
        code_text=build_evaluator_code(threshold),
        data_schema={
            "type": "object",
            "properties": {
                "response": {"type": "string"},
                "expected_topics": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "ground_truth": {"type": "string"},
            },
            "required": ["response"],
        },
        metrics={
            "fsi_coverage_score": EvaluatorMetric(
                type=EvaluatorMetricType.CONTINUOUS,
                desirable_direction=EvaluatorMetricDirection.INCREASE,
                min_value=0.0,
                max_value=1.0,
            ),
            "passed": EvaluatorMetric(type=EvaluatorMetricType.BOOLEAN),
        },
    )

    # In azure-ai-projects 2.x (GA) the evaluator catalog operations live under
    # the ``beta`` namespace.
    evaluator = project_client.beta.evaluators.create_version(
        name=EVALUATOR_NAME,
        evaluator_version=EvaluatorVersion(
            evaluator_type=EvaluatorType.CUSTOM,
            categories=[EvaluatorCategory.QUALITY],
            display_name="FSI Question Coverage",
            description=(
                "Fraction of expected FSI compliance/security topics covered by "
                "the customer agent's clarifying questions."
            ),
            definition=definition,
        ),
    )
    version = getattr(evaluator, "version", "?")
    print(f"✅ Registered evaluator '{EVALUATOR_NAME}' (version {version})")
    return EVALUATOR_NAME


def load_dataset(path: Path) -> list[dict[str, Any]]:
    """Load JSONL eval records."""
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if not records:
        raise ValueError(f"No records found in dataset: {path}")
    return records


def build_data_source(records: list[dict[str, Any]]) -> Any:
    """Build an inline JSONL data source from the eval records."""
    from openai.types.evals.create_eval_jsonl_run_data_source_param import (
        CreateEvalJSONLRunDataSourceParam,
        SourceFileContent,
        SourceFileContentContent,
    )

    return CreateEvalJSONLRunDataSourceParam(
        type="jsonl",
        source=SourceFileContent(
            type="file_content",
            content=[
                SourceFileContentContent(item=record, sample={})
                for record in records
            ],
        ),
    )


def build_data_source_config() -> Any:
    """Describe the dataset item schema for the eval."""
    from openai.types.eval_create_params import DataSourceConfigCustom

    return DataSourceConfigCustom(
        type="custom",
        item_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "query": {"type": "string"},
                "context": {"type": "string"},
                "response": {"type": "string"},
                "ground_truth": {"type": "string"},
                "expected_topics": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "quality_label": {"type": "string"},
            },
            "required": ["response"],
        },
        include_sample_schema=False,
    )


def build_testing_criteria(
    threshold: float, deployment: str, include_builtins: bool
) -> list[dict[str, Any]]:
    """Build the testing criteria.

    The custom FSI coverage metric is sent as an inline OpenAI **Python grader**
    so the exact (compile-free) code runs every time, independent of any catalog
    evaluator version.
    """
    criteria: list[dict[str, Any]] = [
        {
            "type": "python",
            "name": "fsi_coverage",
            "source": build_python_grader_source(threshold),
            "pass_threshold": threshold,
        }
    ]

    if include_builtins:
        for builtin in ("relevance", "coherence"):
            criteria.append(
                {
                    "type": "azure_ai_evaluator",
                    "name": builtin,
                    "evaluator_name": f"builtin.{builtin}",
                    "data_mapping": {
                        "query": "{{item.query}}",
                        "response": "{{item.response}}",
                    },
                    "initialization_parameters": {"deployment_name": deployment},
                }
            )

    return criteria


def _poll_run(openai_client: Any, eval_id: str, run_id: str, *, interval: float, timeout: float) -> Any:
    """Poll an eval run until it reaches a terminal state or times out."""
    terminal = {"completed", "failed", "cancelled", "canceled"}
    deadline = time.monotonic() + timeout
    run = openai_client.evals.runs.retrieve(eval_id=eval_id, run_id=run_id)
    while run.status not in terminal:
        if time.monotonic() > deadline:
            print(f"⏱️  Timed out after {timeout:.0f}s (last status: {run.status})")
            break
        time.sleep(interval)
        run = openai_client.evals.runs.retrieve(eval_id=eval_id, run_id=run_id)
        print(f"   status: {run.status}")
    return run


def _print_results(openai_client: Any, eval_id: str, run_id: str) -> None:
    """Fetch and summarize per-item evaluation results."""
    output_items = list(
        openai_client.evals.runs.output_items.list(eval_id=eval_id, run_id=run_id)
    )
    if not output_items:
        print("No output items returned.")
        return

    print("\n--- Per-item results ---")
    scores: dict[str, list[float]] = {}
    for item in output_items:
        for result in getattr(item, "results", []) or []:
            name = getattr(result, "name", "?")
            score = getattr(result, "score", None)
            if isinstance(score, (int, float)):
                scores.setdefault(name, []).append(float(score))
            print(f"  {name}: score={score} passed={getattr(result, 'passed', '?')}")

    if scores:
        print("\n--- Aggregate (mean score by criterion) ---")
        for name, values in scores.items():
            print(f"  {name}: n={len(values)} avg={sum(values) / len(values):.3f}")


def run(
    *,
    dataset: Path,
    eval_name: str,
    deployment: str,
    threshold: float,
    include_builtins: bool,
    register_catalog: bool,
    poll_interval: float,
    timeout: float,
) -> int:
    """Execute the cloud evaluation end to end. Returns a process exit code."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
    if not endpoint:
        print("ERROR: AZURE_AI_PROJECT_ENDPOINT is required. See .env.example.")
        return 1

    records = load_dataset(dataset)
    print(f"Loaded {len(records)} records from {dataset}")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    ):
        # The run uses an inline Python grader (below). Optionally also publish the
        # evaluator to the Foundry catalog for reuse in the portal.
        if register_catalog:
            try:
                register_evaluator(project_client, threshold)
            except Exception as exc:  # best-effort; not required for the run
                print(f"⚠️  Catalog registration skipped ({type(exc).__name__}: {exc})")

        openai_client = project_client.get_openai_client()

        eval_object = openai_client.evals.create(
            name=eval_name,
            data_source_config=build_data_source_config(),
            testing_criteria=build_testing_criteria(
                threshold, deployment, include_builtins
            ),
        )
        print(f"Created eval '{eval_name}' (id: {eval_object.id})")

        run_obj = openai_client.evals.runs.create(
            eval_id=eval_object.id,
            name=f"{eval_name}-run",
            data_source=build_data_source(records),
        )
        print(f"Started run (id: {run_obj.id}); polling for completion...")

        run_obj = _poll_run(
            openai_client,
            eval_object.id,
            run_obj.id,
            interval=poll_interval,
            timeout=timeout,
        )
        print(f"\nFinal status: {run_obj.status}")

        if run_obj.status not in ("completed",):
            error = getattr(run_obj, "error", None)
            if error:
                print(f"Error: {error}")

        _print_results(openai_client, eval_object.id, run_obj.id)

        report_url = getattr(run_obj, "report_url", None)
        if report_url:
            print(f"\nReport: {report_url}")

        if run_obj.status == "completed":
            print("✅ Evaluation completed. View results in the Foundry portal.")
            return 0
        print("⚠️  Evaluation did not complete successfully.")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Trigger the FSI coverage evaluation on Azure AI Foundry."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help=f"Path to the JSONL eval dataset (default: {DEFAULT_DATASET}).",
    )
    parser.add_argument(
        "--name",
        default="FSI Customer Agent Coverage",
        help="Display name for the evaluation.",
    )
    parser.add_argument(
        "--deployment",
        default=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", DEFAULT_DEPLOYMENT),
        help="Model deployment for built-in/LLM evaluators.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Pass threshold for fsi_coverage_score (default: 0.7).",
    )
    parser.add_argument(
        "--builtins",
        action="store_true",
        help="Also run built-in relevance + coherence evaluators.",
    )
    parser.add_argument(
        "--register-catalog",
        action="store_true",
        help="Also publish the evaluator to the Foundry catalog for portal reuse "
        "(the run itself always uses the inline Python grader).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Seconds between run status polls (default: 5).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Max seconds to wait for the run (default: 600).",
    )
    args = parser.parse_args(argv)

    return run(
        dataset=args.dataset,
        eval_name=args.name,
        deployment=args.deployment,
        threshold=args.threshold,
        include_builtins=args.builtins,
        register_catalog=args.register_catalog,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())

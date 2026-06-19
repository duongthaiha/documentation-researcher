"""Validate the FSI customer-agent evaluation dataset.

Checks that ``fsi_customer_eval.jsonl`` is well-formed and Azure AI Foundry
friendly, then runs the reference custom evaluator over every row as a smoke
test.

Run::

    python -m doc_reviewer.eval.validate_dataset
    # or against a different file:
    python -m doc_reviewer.eval.validate_dataset path/to/dataset.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from doc_reviewer.eval.fsi_coverage_evaluator import (
    EXPECTED_TOPICS,
    fsi_coverage_evaluator,
)

REQUIRED_FIELDS = (
    "id",
    "query",
    "context",
    "response",
    "ground_truth",
    "expected_topics",
    "quality_label",
)
VALID_QUALITY_LABELS = {"strong", "partial", "weak"}

DEFAULT_DATASET = (
    Path(__file__).resolve().parent / "dataset" / "fsi_customer_eval.jsonl"
)


def _validate_record(line_no: int, record: dict[str, Any], seen_ids: set[str]) -> list[str]:
    errors: list[str] = []
    prefix = f"line {line_no}"

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"{prefix}: missing required field '{field}'")

    rec_id = record.get("id")
    if isinstance(rec_id, str):
        if rec_id in seen_ids:
            errors.append(f"{prefix}: duplicate id '{rec_id}'")
        seen_ids.add(rec_id)
    elif "id" in record:
        errors.append(f"{prefix}: 'id' must be a string")

    for field in ("query", "context", "response", "ground_truth"):
        value = record.get(field)
        if field in record and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{prefix}: '{field}' must be a non-empty string")

    topics = record.get("expected_topics")
    if "expected_topics" in record:
        if not isinstance(topics, list) or not topics:
            errors.append(f"{prefix}: 'expected_topics' must be a non-empty list")
        else:
            for topic in topics:
                if topic not in EXPECTED_TOPICS:
                    errors.append(
                        f"{prefix}: unknown topic '{topic}' "
                        f"(not in controlled vocabulary)"
                    )

    label = record.get("quality_label")
    if "quality_label" in record and label not in VALID_QUALITY_LABELS:
        errors.append(
            f"{prefix}: 'quality_label' must be one of {sorted(VALID_QUALITY_LABELS)}"
        )

    return errors


def validate(dataset_path: Path) -> int:
    """Validate the dataset. Returns a process exit code (0 == success)."""
    if not dataset_path.exists():
        print(f"ERROR: dataset not found: {dataset_path}")
        return 1

    errors: list[str] = []
    seen_ids: set[str] = set()
    records: list[dict[str, Any]] = []

    with dataset_path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            if not raw.strip():
                errors.append(f"line {line_no}: empty line (JSONL must not contain blanks)")
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON ({exc})")
                continue
            if not isinstance(record, dict):
                errors.append(f"line {line_no}: each line must be a JSON object")
                continue
            errors.extend(_validate_record(line_no, record, seen_ids))
            records.append(record)

    if not records:
        errors.append("dataset contains no records")

    # Smoke test: run the evaluator and report the score distribution. This also
    # surfaces any rows whose sample response does not match its declared label.
    print(f"Validating {dataset_path} ({len(records)} records)\n")
    label_scores: dict[str, list[float]] = {}
    for record in records:
        result = fsi_coverage_evaluator(
            response=record.get("response", ""),
            expected_topics=record.get("expected_topics"),
            ground_truth=record.get("ground_truth"),
            query=record.get("query"),
        )
        label = record.get("quality_label", "unknown")
        label_scores.setdefault(label, []).append(result["fsi_coverage_score"])
        print(
            f"  {record.get('id', '?'):<8} "
            f"[{label:<7}] score={result['fsi_coverage_score']:.2f} "
            f"matched={result['matched_count']}/{result['expected_count']} "
            f"missing={result['missing_topics']}"
        )

    print("\nScore distribution by quality_label:")
    for label in ("strong", "partial", "weak"):
        scores = label_scores.get(label, [])
        if scores:
            avg = sum(scores) / len(scores)
            print(f"  {label:<7}: n={len(scores)} avg={avg:.2f}")

    # Sanity check that labels and scores are consistent in aggregate.
    strong = label_scores.get("strong", [])
    weak = label_scores.get("weak", [])
    if strong and weak:
        avg_strong = sum(strong) / len(strong)
        avg_weak = sum(weak) / len(weak)
        if avg_strong <= avg_weak:
            errors.append(
                f"score sanity check failed: avg strong ({avg_strong:.2f}) "
                f"should exceed avg weak ({avg_weak:.2f})"
            )

    print()
    if errors:
        print(f"FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("OK: dataset is valid and Foundry-ready.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    dataset_path = Path(args[0]).expanduser() if args else DEFAULT_DATASET
    return validate(dataset_path)


if __name__ == "__main__":
    raise SystemExit(main())

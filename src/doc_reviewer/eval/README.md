# FSI Customer Agent — Evaluation Dataset

This folder contains an evaluation dataset and tooling for the **FSI (Financial
Services) customer agent** (`src/doc_reviewer/agents/fsi_customer.py`).

The FSI agent reviews architecture / guidance documentation and **asks** pointed
clarifying questions about gaps in security, regulatory compliance, networking,
data sovereignty, HA/DR, identity, and governance. This dataset measures how well
those questions **cover** the compliance/security topics a strong FSI reviewer is
expected to raise.

## Contents

| File | Purpose |
|------|---------|
| `dataset/fsi_customer_eval.jsonl` | 15-record evaluation dataset (JSONL). |
| `fsi_coverage_evaluator.py` | Reference **custom evaluator** (stdlib only). |
| `validate_dataset.py` | Validates the JSONL and smoke-tests the evaluator. |
| `run_foundry_eval.py` | Triggers the evaluation on **Azure AI Foundry** (cloud). |

## Dataset schema

Newline-delimited JSON (`.jsonl`), UTF-8, one flat JSON object per line — the
format Azure AI Foundry evaluations expect. Each record:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable record id (e.g. `fsi-001`). |
| `query` | string | Instruction + the document excerpt the agent reviews. |
| `context` | string | The FSI reviewer persona / focus areas. |
| `response` | string | A sample FSI agent output (the clarifying questions). |
| `ground_truth` | string | Human-readable description of expected coverage. |
| `expected_topics` | string[] | Controlled-vocabulary topic tags a strong response should cover. |
| `quality_label` | string | `strong` \| `partial` \| `weak` — gives the metric a signal spread. |

The dataset deliberately mixes `strong`, `partial`, and `weak` sample responses so
the custom evaluator produces a meaningful score distribution.

### Controlled topic vocabulary

`expected_topics` values are drawn from a single source of truth,
`EXPECTED_TOPICS` in `fsi_coverage_evaluator.py`:

`pci_dss`, `sox`, `gdpr`, `dora`, `apra_cps234`, `data_residency`,
`network_isolation`, `private_endpoints`, `encryption_at_rest`,
`encryption_in_transit`, `key_rotation`, `zero_trust`, `rpo_rto`,
`high_availability`, `multi_region_failover`, `audit_logging`,
`privileged_access`, `mfa_conditional_access`, `disaster_recovery`,
`data_isolation`.

## Custom evaluator

`fsi_coverage_evaluator.py` scores the fraction of a row's `expected_topics` that
are detected in the agent `response` (via keyword/synonym matching). It returns:

```json
{
  "fsi_coverage_score": 0.75,
  "passed": true,
  "matched_topics": ["gdpr", "data_residency"],
  "missing_topics": ["network_isolation"],
  "extra_topics": [],
  "expected_count": 4,
  "matched_count": 3
}
```

It is dependency-light (standard library only) so it runs locally **and** as an
Azure AI Foundry custom code evaluator.

## Run the evaluation on Azure AI Foundry

`run_foundry_eval.py` triggers a **cloud evaluation** in your Foundry project. It
registers the FSI coverage logic as a code-based custom evaluator (vocabulary
sourced from `fsi_coverage_evaluator.py`), uploads the JSONL, creates and runs the
evaluation, polls to completion, and prints scores. Results also appear in the
Foundry portal.

Install the optional dependencies and authenticate, then run:

```bash
pip install "doc-reviewer[eval]"        # or: pip install azure-ai-projects openai
az login                                 # DefaultAzureCredential

export AZURE_AI_PROJECT_ENDPOINT="https://<resource>.services.ai.azure.com/api/projects/<project>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o"   # used by built-in/LLM evaluators

# Custom FSI coverage evaluator only:
python -m doc_reviewer.eval.run_foundry_eval

# Also include built-in relevance + coherence:
python -m doc_reviewer.eval.run_foundry_eval --builtins --threshold 0.7
```

Key flags: `--dataset <path>`, `--name <eval name>`, `--threshold <0..1>`,
`--builtins`, `--register-catalog` (also publish the evaluator to the Foundry
catalog for portal reuse), `--poll-interval`, `--timeout`. The run itself sends
the FSI coverage logic as an inline OpenAI **Python grader**, so it always uses
the exact compile-free code regardless of catalog state. Authentication uses
`DefaultAzureCredential`; set `AZURE_TOKEN_CREDENTIALS=prod` in production.

> Verified end to end against a live Foundry project: the 15 cloud `fsi_coverage`
> scores match the local validator exactly (avg 0.63), and `--builtins` adds
> `relevance` and `coherence` scores.

## Manual setup in the Foundry portal

If you prefer to wire things up by hand instead of using the runner:

1. Upload `dataset/fsi_customer_eval.jsonl` as an evaluation dataset.
2. Register `fsi_coverage_evaluator.py` as a **custom code evaluator** (the
   `FsiCoverageEvaluator` class / `fsi_coverage_evaluator` function).
3. Configure the column mapping so dataset fields flow into the evaluator:

   ```json
   {
     "response": "${data.response}",
     "expected_topics": "${data.expected_topics}",
     "ground_truth": "${data.ground_truth}",
     "query": "${data.query}"
   }
   ```

To evaluate **live** agent output instead of the pre-populated `response`, map
`response` to the model/agent output column produced by the run and keep
`expected_topics` / `ground_truth` mapped from the dataset.

## Validate locally

```bash
# from the repo root, with the package importable (pip install -e .)
python -m doc_reviewer.eval.validate_dataset
```

This checks the JSONL is well-formed, that all required fields are present, that
every `expected_topics` tag is in the controlled vocabulary, and runs the
evaluator over each row — printing a per-row score and an aggregate distribution
by `quality_label`.

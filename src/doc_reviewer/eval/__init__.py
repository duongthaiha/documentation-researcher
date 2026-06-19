"""Evaluation assets for the documentation-reviewer agents.

Contains evaluation datasets (``dataset/``), a reference custom evaluator
(:mod:`doc_reviewer.eval.fsi_coverage_evaluator`), and a dataset validator
(:mod:`doc_reviewer.eval.validate_dataset`) for use with Azure AI Foundry
evaluations.
"""

from doc_reviewer.eval.fsi_coverage_evaluator import (
    EXPECTED_TOPICS,
    FsiCoverageEvaluator,
    fsi_coverage_evaluator,
)

__all__ = [
    "EXPECTED_TOPICS",
    "FsiCoverageEvaluator",
    "fsi_coverage_evaluator",
]

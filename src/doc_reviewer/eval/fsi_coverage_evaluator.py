"""Reference custom evaluator for the FSI customer agent.

The FSI (Financial Services) customer agent reviews architecture / guidance
documentation and asks pointed clarifying questions about gaps in security,
regulatory compliance, networking, data sovereignty, HA/DR, identity, and
governance.

This module scores how well a given agent *response* (the set of clarifying
questions it asked) covers the compliance/security topics that a strong FSI
reviewer is expected to raise for a given document (the ``expected_topics``).

It is intentionally dependency-light (standard library only) so it can run:

* **Locally** — imported directly or via :mod:`doc_reviewer.eval.validate_dataset`.
* **As an Azure AI Foundry custom code evaluator** — Foundry calls the evaluator
  with column-mapped keyword arguments (``query``, ``response``, ``ground_truth``,
  and any extra ``data.*`` columns such as ``expected_topics``). The ``__call__``
  signature below matches that contract and returns a flat ``dict`` of metrics.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Controlled vocabulary
# ---------------------------------------------------------------------------
# This is the SINGLE SOURCE OF TRUTH for valid ``expected_topics`` tags used by
# the dataset, the validator, and this evaluator. Each tag maps to a list of
# regex keyword patterns; a topic is considered "covered" by a response if any
# of its patterns match (case-insensitive).
TOPIC_PATTERNS: dict[str, list[str]] = {
    "pci_dss": [r"pci[\s-]?dss", r"cardholder data", r"\bcde\b"],
    "sox": [r"\bsox\b", r"sarbanes[\s-]?oxley"],
    "gdpr": [r"\bgdpr\b", r"general data protection"],
    "dora": [r"\bdora\b", r"digital operational resilience"],
    "apra_cps234": [r"apra", r"cps\s?234"],
    "data_residency": [
        r"data residency",
        r"data sovereignty",
        r"data location",
        r"cross[\s-]?border",
        r"in[\s-]?region",
    ],
    "network_isolation": [
        r"network isolation",
        r"network segmentation",
        r"\bvnet\b",
        r"virtual network",
        r"\bsegment(ation|ed)?\b",
    ],
    "private_endpoints": [
        r"private endpoint",
        r"private link",
        r"\bprivatelink\b",
    ],
    "encryption_at_rest": [
        r"encryption at rest",
        r"encrypt(ed|ion)? at rest",
        r"\bcmk\b",
        r"customer[\s-]?managed key",
    ],
    "encryption_in_transit": [
        r"encryption in transit",
        r"in[\s-]?transit",
        r"\btls\b",
        r"\bmtls\b",
    ],
    "key_rotation": [
        r"key rotation",
        r"rotate (the )?keys?",
        r"key management",
        r"key vault",
        r"\bhsm\b",
    ],
    "zero_trust": [r"zero[\s-]?trust"],
    "rpo_rto": [r"\brpo\b", r"\brto\b", r"recovery point", r"recovery time"],
    "high_availability": [
        r"high availability",
        r"\bha\b",
        r"99\.9",
        r"\bsla\b",
        r"uptime",
    ],
    "multi_region_failover": [
        r"multi[\s-]?region",
        r"failover",
        r"region(al)? redundan",
        r"geo[\s-]?redundan",
        r"active[\s-]?active",
        r"active[\s-]?passive",
    ],
    "audit_logging": [
        r"audit (log|trail)",
        r"audit(ing|ability)?",
        r"\blogging\b",
        r"monitor(ing)?",
        r"diagnostic (log|setting)",
    ],
    "privileged_access": [
        r"privileged access",
        r"\bpam\b",
        r"\bpim\b",
        r"just[\s-]?in[\s-]?time",
        r"least privilege",
    ],
    "mfa_conditional_access": [
        r"\bmfa\b",
        r"multi[\s-]?factor",
        r"conditional access",
    ],
    "disaster_recovery": [
        r"disaster recovery",
        r"\bdr\b",
        r"business continuity",
        r"\bbcdr\b",
        r"backup",
    ],
    "data_isolation": [
        r"data isolation",
        r"tenant isolation",
        r"logical isolation",
        r"data segregation",
    ],
}

# Ordered tuple of valid topic tags, used by the dataset and validator.
EXPECTED_TOPICS: tuple[str, ...] = tuple(TOPIC_PATTERNS.keys())

# Pre-compiled patterns for performance.
_COMPILED: dict[str, list[re.Pattern[str]]] = {
    topic: [re.compile(p, re.IGNORECASE) for p in patterns]
    for topic, patterns in TOPIC_PATTERNS.items()
}


def detect_topics(text: str) -> set[str]:
    """Return the set of controlled-vocabulary topics mentioned in ``text``."""
    if not text:
        return set()
    return {
        topic
        for topic, patterns in _COMPILED.items()
        if any(pattern.search(text) for pattern in patterns)
    }


class FsiCoverageEvaluator:
    """Custom evaluator scoring FSI compliance/security question coverage.

    The score is the fraction of ``expected_topics`` that are detected in the
    agent ``response``. A ``threshold`` controls the binary ``passed`` flag.

    Usage as an Azure AI Foundry custom code evaluator::

        from doc_reviewer.eval.fsi_coverage_evaluator import FsiCoverageEvaluator
        evaluator = FsiCoverageEvaluator()

    with a column mapping such as::

        {
            "response": "${data.response}",
            "expected_topics": "${data.expected_topics}",
            "ground_truth": "${data.ground_truth}",
        }
    """

    def __init__(self, *, threshold: float = 0.7) -> None:
        self.threshold = threshold

    def __call__(
        self,
        *,
        response: str,
        expected_topics: list[str] | str | None = None,
        ground_truth: str | None = None,
        query: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        expected = _normalize_topics(expected_topics)

        # Fall back to topics inferred from the ground truth if no explicit
        # expected_topics column is provided.
        if not expected and ground_truth:
            expected = detect_topics(ground_truth)

        detected = detect_topics(response or "")
        matched = sorted(expected & detected)
        missing = sorted(expected - detected)
        # Topics raised by the response that were not in the expected set.
        extra = sorted(detected - expected)

        total = len(expected)
        score = (len(matched) / total) if total else 0.0

        return {
            "fsi_coverage_score": round(score, 4),
            "passed": bool(total) and score >= self.threshold,
            "matched_topics": matched,
            "missing_topics": missing,
            "extra_topics": extra,
            "expected_count": total,
            "matched_count": len(matched),
        }


def _normalize_topics(topics: list[str] | str | None) -> set[str]:
    """Coerce the ``expected_topics`` column into a set of tags."""
    if topics is None:
        return set()
    if isinstance(topics, str):
        # Allow comma/space/semicolon separated strings (Foundry may pass a
        # serialized list as a string depending on column mapping).
        parts = re.split(r"[,;\s]+", topics.strip())
        return {p for p in parts if p}
    return {str(t).strip() for t in topics if str(t).strip()}


# Functional alias — Foundry and local callers can use either the class
# instance or this module-level callable.
_default_evaluator = FsiCoverageEvaluator()


def fsi_coverage_evaluator(
    *,
    response: str,
    expected_topics: list[str] | str | None = None,
    ground_truth: str | None = None,
    query: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Module-level functional wrapper around :class:`FsiCoverageEvaluator`."""
    return _default_evaluator(
        response=response,
        expected_topics=expected_topics,
        ground_truth=ground_truth,
        query=query,
        **kwargs,
    )

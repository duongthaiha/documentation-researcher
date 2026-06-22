"""Single source of truth for the agents that make up the documentation reviewer.

Every agent is a self-contained package under :mod:`doc_reviewer.agents`. This
registry maps logical agent names to their packages so that both the local
orchestrator and the Foundry deployment scaffolding can discover them without
hard-coding paths in multiple places.
"""

from __future__ import annotations

# Customer industries, in the order they should run. ``main.py`` derives the
# CLI ``--industry`` choices from this list.
CUSTOMER_INDUSTRIES: list[str] = ["fsi", "manufacturing", "engineering"]

# Customer-agent industry -> package implementing it.
CUSTOMER_AGENT_PACKAGES: dict[str, str] = {
    "fsi": "doc_reviewer.agents.fsi_customer",
    "manufacturing": "doc_reviewer.agents.manufacturing_customer",
    "engineering": "doc_reviewer.agents.engineering_customer",
}

# All agent packages (customers + research + writer). Used by deploy_all.py.
AGENT_PACKAGES: list[str] = [
    *CUSTOMER_AGENT_PACKAGES.values(),
    "doc_reviewer.agents.research",
    "doc_reviewer.agents.writer",
]


def customer_package(industry: str) -> str:
    """Return the package path for a customer industry, or raise ValueError."""
    try:
        return CUSTOMER_AGENT_PACKAGES[industry]
    except KeyError as exc:
        supported = ", ".join(CUSTOMER_INDUSTRIES)
        raise ValueError(
            f"Unknown industry: {industry}. Supported: {supported}"
        ) from exc

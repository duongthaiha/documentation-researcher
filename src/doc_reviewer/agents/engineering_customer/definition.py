"""Azure AI Foundry prompt-agent definition for the Engineering customer agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from doc_reviewer.agents.engineering_customer.instructions import (
    ENGINEERING_INSTRUCTIONS,
)
from doc_reviewer.config import Settings

if TYPE_CHECKING:
    from azure.ai.projects.models import PromptAgentDefinition

from doc_reviewer.agents.registry import CUSTOMER_FOUNDRY_AGENT_NAMES
FOUNDRY_AGENT_NAME = CUSTOMER_FOUNDRY_AGENT_NAMES["engineering"]
DESCRIPTION = (
    "Engineering lead/platform architect persona that reviews architecture docs "
    "for DevOps, CI/CD, agent versioning, eval gates, rollback and observability."
)


def build_prompt_agent_definition(settings: Settings) -> "PromptAgentDefinition":
    """Build the PromptAgentDefinition for the Engineering customer agent."""
    from azure.ai.projects.models import PromptAgentDefinition

    return PromptAgentDefinition(
        model=settings.customer_model,
        instructions=ENGINEERING_INSTRUCTIONS,
    )

"""Azure AI Foundry prompt-agent definition for the FSI customer agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from doc_reviewer.agents.fsi_customer.instructions import FSI_INSTRUCTIONS
from doc_reviewer.config import Settings

if TYPE_CHECKING:
    from azure.ai.projects.models import PromptAgentDefinition

# Stable name used when creating/versioning the agent in Foundry.
from doc_reviewer.agents.registry import CUSTOMER_FOUNDRY_AGENT_NAMES
FOUNDRY_AGENT_NAME = CUSTOMER_FOUNDRY_AGENT_NAMES["fsi"]
DESCRIPTION = (
    "Financial-services IT Architect/CTO persona that reviews architecture docs "
    "for security, regulatory compliance, network isolation and high availability."
)


def build_prompt_agent_definition(settings: Settings) -> "PromptAgentDefinition":
    """Build the PromptAgentDefinition for the FSI customer agent.

    The ``azure-ai-projects`` import is lazy so the core runtime does not depend
    on the optional deploy package.
    """
    from azure.ai.projects.models import PromptAgentDefinition

    return PromptAgentDefinition(
        model=settings.customer_model,
        instructions=FSI_INSTRUCTIONS,
    )

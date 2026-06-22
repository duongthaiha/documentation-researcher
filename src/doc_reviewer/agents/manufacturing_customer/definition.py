"""Azure AI Foundry prompt-agent definition for the Manufacturing customer agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from doc_reviewer.agents.manufacturing_customer.instructions import (
    MANUFACTURING_INSTRUCTIONS,
)
from doc_reviewer.config import Settings

if TYPE_CHECKING:
    from azure.ai.projects.models import PromptAgentDefinition

FOUNDRY_AGENT_NAME = "manufacturing-customer"
DESCRIPTION = (
    "Manufacturing IT Architect/CTO persona that reviews architecture docs for "
    "edge computing, IoT, OT/IT convergence, low latency and intermittent connectivity."
)


def build_prompt_agent_definition(settings: Settings) -> "PromptAgentDefinition":
    """Build the PromptAgentDefinition for the Manufacturing customer agent."""
    from azure.ai.projects.models import PromptAgentDefinition

    return PromptAgentDefinition(
        model=settings.model_deployment_name,
        instructions=MANUFACTURING_INSTRUCTIONS,
    )

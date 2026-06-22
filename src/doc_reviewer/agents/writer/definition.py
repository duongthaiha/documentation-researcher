"""Azure AI Foundry prompt-agent definition for the Writer agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from doc_reviewer.agents.writer.instructions import WRITER_INSTRUCTIONS
from doc_reviewer.config import Settings

if TYPE_CHECKING:
    from azure.ai.projects.models import PromptAgentDefinition

from doc_reviewer.agents.registry import WRITER_FOUNDRY_AGENT_NAME as FOUNDRY_AGENT_NAME
DESCRIPTION = (
    "Technical writer agent that produces an updated document incorporating the "
    "guidance discovered during the review, preserving the original structure."
)


def build_prompt_agent_definition(settings: Settings) -> "PromptAgentDefinition":
    """Build the PromptAgentDefinition for the Writer agent."""
    from azure.ai.projects.models import PromptAgentDefinition

    return PromptAgentDefinition(
        model=settings.model_deployment_name,
        instructions=WRITER_INSTRUCTIONS,
    )

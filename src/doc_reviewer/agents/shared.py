"""Shared helpers used by the per-agent factories.

Each agent lives in its own folder (``fsi_customer/``, ``research/`` …) and is
structured so it can be run locally via the Microsoft Agent Framework
(:func:`create_chat_client` + ``factory.create_agent``) or deployed to Azure AI
Foundry as a **prompt agent** (``definition.build_prompt_agent_definition``).
"""

from agent_framework.foundry import FoundryChatClient
from azure.core.credentials_async import AsyncTokenCredential

from doc_reviewer.config import Settings


def create_chat_client(
    settings: Settings,
    credential: AsyncTokenCredential,
) -> FoundryChatClient:
    """Create the Foundry chat client shared by every local agent factory."""
    return FoundryChatClient(
        project_endpoint=settings.project_endpoint,
        model=settings.model_deployment_name,
        credential=credential,
    )


# Backwards-compatible alias for the previous private name used in base.py.
_create_chat_client = create_chat_client

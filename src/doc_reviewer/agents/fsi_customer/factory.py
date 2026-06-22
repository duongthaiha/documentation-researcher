"""Local Agent Framework factory for the FSI customer agent."""

from agent_framework import Agent
from azure.core.credentials_async import AsyncTokenCredential

from doc_reviewer.agents.fsi_customer.instructions import FSI_INSTRUCTIONS
from doc_reviewer.agents.shared import create_chat_client
from doc_reviewer.config import Settings

AGENT_NAME = "FSI Customer Agent"


def create_agent(settings: Settings, credential: AsyncTokenCredential) -> Agent:
    """Create the FSI customer agent for a local review run."""
    return Agent(
        create_chat_client(settings, credential),
        name=AGENT_NAME,
        instructions=FSI_INSTRUCTIONS,
    )

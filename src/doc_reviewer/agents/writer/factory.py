"""Local Agent Framework factory for the Writer agent."""

from agent_framework import Agent
from azure.core.credentials_async import AsyncTokenCredential

from doc_reviewer.agents.shared import create_chat_client
from doc_reviewer.agents.writer.instructions import WRITER_INSTRUCTIONS
from doc_reviewer.config import Settings

AGENT_NAME = "Writer Agent"


def create_agent(settings: Settings, credential: AsyncTokenCredential) -> Agent:
    """Create the Writer agent for a local review run."""
    return Agent(
        create_chat_client(settings, credential),
        name=AGENT_NAME,
        instructions=WRITER_INSTRUCTIONS,
    )

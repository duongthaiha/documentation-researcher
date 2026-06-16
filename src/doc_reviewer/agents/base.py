"""Base agent factory for creating chat-backed agents."""

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.core.credentials_async import AsyncTokenCredential

from doc_reviewer.config import Settings


def _create_chat_client(
    settings: Settings,
    credential: AsyncTokenCredential,
) -> FoundryChatClient:
    return FoundryChatClient(
        project_endpoint=settings.project_endpoint,
        model=settings.model_deployment_name,
        credential=credential,
    )


def create_research_agent(
    settings: Settings,
    credential: AsyncTokenCredential,
    mcp_tools: list[MCPStreamableHTTPTool],
) -> Agent:
    """Create the Research agent with MCP tools."""
    from doc_reviewer.agents.research import RESEARCH_INSTRUCTIONS

    return Agent(
        _create_chat_client(settings, credential),
        name="Research Agent",
        instructions=RESEARCH_INSTRUCTIONS,
        tools=mcp_tools,
    )


def create_customer_agent(
    settings: Settings,
    credential: AsyncTokenCredential,
    industry: str,
) -> Agent:
    """Create a customer agent for the given industry."""
    if industry == "fsi":
        from doc_reviewer.agents.fsi_customer import FSI_INSTRUCTIONS

        return Agent(
            _create_chat_client(settings, credential),
            name="FSI Customer Agent",
            instructions=FSI_INSTRUCTIONS,
        )
    elif industry == "manufacturing":
        from doc_reviewer.agents.manufacturing_customer import (
            MANUFACTURING_INSTRUCTIONS,
        )

        return Agent(
            _create_chat_client(settings, credential),
            name="Manufacturing Customer Agent",
            instructions=MANUFACTURING_INSTRUCTIONS,
        )
    else:
        raise ValueError(f"Unknown industry: {industry}. Supported: fsi, manufacturing")


def create_writer_agent(
    settings: Settings,
    credential: AsyncTokenCredential,
) -> Agent:
    """Create the Writer agent."""
    from doc_reviewer.agents.writer import WRITER_INSTRUCTIONS

    return Agent(
        _create_chat_client(settings, credential),
        name="Writer Agent",
        instructions=WRITER_INSTRUCTIONS,
    )

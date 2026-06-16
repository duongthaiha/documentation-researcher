"""Base agent factory for creating agents via FoundryAgent."""

from agent_framework import MCPStreamableHTTPTool
from agent_framework.foundry import FoundryAgent

from doc_reviewer.config import Settings


def create_research_agent(
    settings: Settings,
    workiq_mcp: MCPStreamableHTTPTool,
) -> FoundryAgent:
    """Create the Research agent with MCP tools."""
    from doc_reviewer.agents.research import RESEARCH_INSTRUCTIONS

    return FoundryAgent(
        project_endpoint=settings.project_endpoint,
        name="Research Agent",
        instructions=RESEARCH_INSTRUCTIONS,
        tools=[workiq_mcp],
    )


def create_customer_agent(settings: Settings, industry: str) -> FoundryAgent:
    """Create a customer agent for the given industry."""
    if industry == "fsi":
        from doc_reviewer.agents.fsi_customer import FSI_INSTRUCTIONS

        return FoundryAgent(
            project_endpoint=settings.project_endpoint,
            name="FSI Customer Agent",
            instructions=FSI_INSTRUCTIONS,
        )
    elif industry == "manufacturing":
        from doc_reviewer.agents.manufacturing_customer import (
            MANUFACTURING_INSTRUCTIONS,
        )

        return FoundryAgent(
            project_endpoint=settings.project_endpoint,
            name="Manufacturing Customer Agent",
            instructions=MANUFACTURING_INSTRUCTIONS,
        )
    else:
        raise ValueError(f"Unknown industry: {industry}. Supported: fsi, manufacturing")


def create_writer_agent(settings: Settings) -> FoundryAgent:
    """Create the Writer agent."""
    from doc_reviewer.agents.writer import WRITER_INSTRUCTIONS

    return FoundryAgent(
        project_endpoint=settings.project_endpoint,
        name="Writer Agent",
        instructions=WRITER_INSTRUCTIONS,
    )

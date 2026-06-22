"""Local Agent Framework factory for the Research agent."""

from agent_framework import Agent, MCPStreamableHTTPTool
from azure.core.credentials_async import AsyncTokenCredential

from doc_reviewer.agents.research.instructions import RESEARCH_INSTRUCTIONS
from doc_reviewer.agents.shared import create_chat_client
from doc_reviewer.config import Settings

AGENT_NAME = "Research Agent"


def create_agent(
    settings: Settings,
    credential: AsyncTokenCredential,
    mcp_tools: list[MCPStreamableHTTPTool],
) -> Agent:
    """Create the Research agent for a local review run, wired to MCP tools."""
    return Agent(
        create_chat_client(settings, credential),
        name=AGENT_NAME,
        instructions=RESEARCH_INSTRUCTIONS,
        tools=mcp_tools,
    )

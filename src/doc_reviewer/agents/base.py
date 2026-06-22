"""Backwards-compatible agent factory.

The agent implementations now live in self-contained packages under
:mod:`doc_reviewer.agents` (``fsi_customer/``, ``research/`` …). This module
preserves the original ``create_*`` factory API used by ``orchestrator.py`` by
delegating to each agent package's ``factory.create_agent``.
"""

import importlib

from agent_framework import Agent, MCPStreamableHTTPTool
from azure.core.credentials_async import AsyncTokenCredential

from doc_reviewer.agents.registry import customer_package
from doc_reviewer.agents.shared import _create_chat_client, create_chat_client
from doc_reviewer.config import Settings

__all__ = [
    "create_chat_client",
    "_create_chat_client",
    "create_research_agent",
    "create_customer_agent",
    "create_writer_agent",
]


def create_research_agent(
    settings: Settings,
    credential: AsyncTokenCredential,
    mcp_tools: list[MCPStreamableHTTPTool],
) -> Agent:
    """Create the Research agent with MCP tools."""
    from doc_reviewer.agents.research.factory import create_agent

    return create_agent(settings, credential, mcp_tools)


def create_customer_agent(
    settings: Settings,
    credential: AsyncTokenCredential,
    industry: str,
) -> Agent:
    """Create a customer agent for the given industry."""
    package = customer_package(industry)
    factory = importlib.import_module(f"{package}.factory")
    return factory.create_agent(settings, credential)


def create_writer_agent(
    settings: Settings,
    credential: AsyncTokenCredential,
) -> Agent:
    """Create the Writer agent."""
    from doc_reviewer.agents.writer.factory import create_agent

    return create_agent(settings, credential)

"""Azure AI Foundry prompt-agent definition for the Research agent.

The Research agent uses hosted MCP tools (Microsoft Learn, WorkIQ, GitHub). The
tool server URLs are sourced from :class:`~doc_reviewer.config.Settings` so the
same configuration drives both the local run and the Foundry deployment.

Two things differ for the **hosted** (deployed) agent vs. the local run:

* The agent runs in Foundry's cloud, so it cannot reach MCP servers on
  ``localhost`` / ``127.0.0.1`` / ``host.docker.internal``. Such servers are
  skipped (with a warning) when building the deployed tool set.
* Authenticated MCP servers (GitHub, optionally WorkIQ) must reference a Foundry
  connection (``MCPTool(project_connection_id=...)``); Foundry rejects inline
  auth headers/tokens. Servers without a connection are skipped when hosted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from doc_reviewer.agents.research.instructions import RESEARCH_INSTRUCTIONS
from doc_reviewer.config import Settings

if TYPE_CHECKING:
    from azure.ai.projects.models import MCPTool, PromptAgentDefinition

from doc_reviewer.agents.registry import RESEARCH_FOUNDRY_AGENT_NAME as FOUNDRY_AGENT_NAME
DESCRIPTION = (
    "Technical research agent that answers reviewer questions using Microsoft "
    "Learn, WorkIQ and GitHub MCP tools, with citations."
)

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "host.docker.internal", "::1"}


def _is_cloud_reachable(url: str) -> bool:
    """Return False for URLs a cloud-hosted agent cannot reach (localhost etc.)."""
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return host not in _LOCAL_HOSTS


def build_mcp_tools(settings: Settings) -> "list[MCPTool]":
    """Build the hosted MCP tool definitions for the Research prompt agent.

    Foundry forbids inline auth headers on MCP tools, so authenticated servers
    must be referenced through a Foundry connection (``project_connection_id``).
    Servers that are neither public nor connection-backed — and any server on
    localhost (unreachable from Foundry's cloud) — are skipped with a warning so
    the agent still deploys with whatever tools are usable.
    """
    from azure.ai.projects.models import MCPTool

    # Run tools autonomously (no human approval gate) so the orchestrator's
    # automated review loop is not blocked by mcp_approval_request items.
    no_approval = "never"

    tools: list[MCPTool] = [
        # Microsoft Learn MCP is public / anonymous — always usable when hosted.
        MCPTool(
            server_label="mslearn",
            server_url=settings.ms_learn_mcp_url,
            require_approval=no_approval,
        ),
    ]

    # WorkIQ: prefer a Foundry connection (with its URL); otherwise only if cloud-reachable.
    if settings.workiq_mcp_connection_id:
        tools.append(
            MCPTool(
                server_label="workiq",
                server_url=settings.workiq_mcp_url or None,
                project_connection_id=settings.workiq_mcp_connection_id,
                require_approval=no_approval,
            )
        )
    elif _is_cloud_reachable(settings.workiq_mcp_url):
        tools.append(
            MCPTool(
                server_label="workiq",
                server_url=settings.workiq_mcp_url,
                require_approval=no_approval,
            )
        )
    else:
        print(
            f"⚠️  Skipping WorkIQ MCP for the hosted agent: "
            f"'{settings.workiq_mcp_url}' is not reachable from Foundry's cloud. "
            f"Set WORKIQ_MCP_CONNECTION_ID to a Foundry connection to enable it."
        )

    # GitHub MCP requires auth: provide the server URL plus a Foundry connection
    # that supplies the Authorization header (Foundry rejects inline headers).
    if settings.github_mcp_connection_id:
        tools.append(
            MCPTool(
                server_label="github",
                server_url=settings.github_mcp_url,
                project_connection_id=settings.github_mcp_connection_id,
                require_approval=no_approval,
            )
        )
    else:
        print(
            "⚠️  Skipping GitHub MCP for the hosted agent: authenticated MCP "
            "servers must use a Foundry connection. Set GITHUB_MCP_CONNECTION_ID "
            "to enable it (inline tokens/headers are rejected by Foundry)."
        )

    return tools


def build_prompt_agent_definition(settings: Settings) -> "PromptAgentDefinition":
    """Build the PromptAgentDefinition for the Research agent."""
    from azure.ai.projects.models import PromptAgentDefinition

    return PromptAgentDefinition(
        model=settings.research_model,
        instructions=RESEARCH_INSTRUCTIONS,
        tools=build_mcp_tools(settings),
    )

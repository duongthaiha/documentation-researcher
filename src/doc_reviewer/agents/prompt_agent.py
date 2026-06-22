"""Invoke the documentation-reviewer **prompt agents** deployed to Foundry.

In local mode each agent is constructed from code every run (instructions + tools
are shipped from this repo). When the agents are deployed to Azure AI Foundry as
**prompt agents**, the instructions/model/tools live server-side and the app simply
invokes them **by name** through the project's OpenAI-compatible Responses API.

.. note::
   "Prompt agent" here is the Foundry *agent kind* (declarative instructions +
   model + tools). It is distinct from a Foundry **Hosted Agent**, which is a
   container running custom code — that is what the orchestrator itself is
   deployed as (see :mod:`doc_reviewer.host`). This module is the *client* the
   orchestrator uses to call the prompt agents.

:class:`PromptAgentClient` mirrors the small slice of the Microsoft Agent Framework
``Agent`` interface that :mod:`doc_reviewer.orchestrator` relies on
(``run(prompt, stream=True)`` yielding chunks with ``.text`` and
``await run(prompt)`` returning an object with ``.text``) so the same
conversation loop drives either execution mode.

Requires the optional ``deploy`` dependencies (``azure-ai-projects``) and a
Foundry project where the prompt agents have already been deployed (see
``doc_reviewer.agents.deploy_all``).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator

from doc_reviewer.agents.registry import (
    CUSTOMER_FOUNDRY_AGENT_NAMES,
    RESEARCH_FOUNDRY_AGENT_NAME,
    WRITER_FOUNDRY_AGENT_NAME,
)
from doc_reviewer.config import Settings

if TYPE_CHECKING:
    from azure.ai.projects import AIProjectClient


@dataclass
class _Chunk:
    """Minimal stand-in for an Agent Framework streaming chunk."""

    text: str


@dataclass
class _Result:
    """Minimal stand-in for an Agent Framework run result."""

    text: str


class PromptAgentClient:
    """Invokes a Foundry **prompt agent** via the Responses API.

    The instructions, model, and tools are resolved server-side from the
    deployed agent identified by ``foundry_agent_name``; nothing is sent from
    the client except the prompt.
    """

    def __init__(self, project_client: "AIProjectClient", foundry_agent_name: str):
        self.foundry_agent_name = foundry_agent_name
        # Invoke through the *project-level* Responses endpoint and reference the
        # deployed agent by name in the request body. This stores the response in
        # the project response store (unlike the per-agent sub-endpoint, whose
        # responses are not retrievable project-side), which is required for
        # Foundry continuous evaluation to fetch and grade the response later.
        self._client = project_client.get_openai_client()
        self._agent_reference = {
            "type": "agent_reference",
            "name": foundry_agent_name,
        }

    def run(self, prompt: str, *, stream: bool = False):
        """Run the hosted agent.

        Returns an async iterator of chunks when ``stream=True`` (use
        ``async for``), otherwise a coroutine returning a result (use
        ``await``) — matching the local Agent Framework agent interface.
        """
        if stream:
            return self._run_stream(prompt)
        return self._run_once(prompt)

    async def _run_once(self, prompt: str) -> _Result:
        response = await asyncio.to_thread(
            lambda: self._client.responses.create(
                input=prompt,
                store=True,
                extra_body={"agent_reference": self._agent_reference},
            )
        )
        return _Result(text=response.output_text)

    async def _run_stream(self, prompt: str) -> AsyncIterator[_Chunk]:
        # The OpenAI SDK stream is synchronous; pull each event off in a worker
        # thread so the async orchestrator is never blocked.
        stream = await asyncio.to_thread(
            lambda: self._client.responses.create(
                input=prompt,
                stream=True,
                store=True,
                extra_body={"agent_reference": self._agent_reference},
            )
        )
        iterator = iter(stream)
        sentinel = object()
        while True:
            event = await asyncio.to_thread(next, iterator, sentinel)
            if event is sentinel:
                break
            if getattr(event, "type", None) == "response.output_text.delta":
                yield _Chunk(text=event.delta)


def create_project_client(settings: Settings) -> "AIProjectClient":
    """Create a preview-enabled AIProjectClient for invoking hosted agents.

    The caller owns the returned client and must close it (use it as a context
    manager). ``DefaultAzureCredential`` is used for authentication.
    """
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    return AIProjectClient(
        endpoint=settings.project_endpoint,
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )


def build_prompt_agents(
    project_client: "AIProjectClient",
    industries: list[str],
) -> tuple[PromptAgentClient, list[tuple[str, PromptAgentClient]], PromptAgentClient]:
    """Build prompt-agent clients (research, customers, writer) bound to deployed names.

    Names come from :mod:`doc_reviewer.agents.registry` (a dependency-free
    module) rather than importing each agent package, so the slim hosted
    orchestrator container does not need ``agent_framework``.
    """
    research_agent = PromptAgentClient(project_client, RESEARCH_FOUNDRY_AGENT_NAME)
    writer_agent = PromptAgentClient(project_client, WRITER_FOUNDRY_AGENT_NAME)

    customer_agents: list[tuple[str, PromptAgentClient]] = []
    for industry in industries:
        customer_agents.append(
            (industry, PromptAgentClient(project_client, CUSTOMER_FOUNDRY_AGENT_NAMES[industry]))
        )

    return research_agent, customer_agents, writer_agent

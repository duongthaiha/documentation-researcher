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
import logging
import random
import time
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

logger = logging.getLogger("doc_reviewer")

# Retry transient model rate-limit (429) errors with exponential backoff.
_MAX_RETRIES = 4
_BASE_DELAY_SECONDS = 2.0


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True for model throttling / 429 errors worth retrying."""
    if getattr(exc, "status_code", None) == 429:
        return True
    return "rate limit" in str(exc).lower()


def _retry_after_seconds(exc: Exception, attempt: int) -> float:
    """Backoff delay, honoring a Retry-After header when present."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers:
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except (TypeError, ValueError):
                pass
    # Exponential backoff with jitter.
    return _BASE_DELAY_SECONDS * (2 ** attempt) + random.uniform(0, 1)


def _create_with_retry(create_fn, *, agent_name: str):
    """Call a blocking ``responses.create`` thunk, retrying on rate limits."""
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return create_fn()
        except Exception as exc:  # noqa: BLE001 - re-raised below if not retryable
            if not _is_rate_limit_error(exc) or attempt == _MAX_RETRIES:
                raise
            delay = _retry_after_seconds(exc, attempt)
            logger.warning(
                "Rate limited calling agent '%s' (attempt %d/%d); retrying in "
                "%.1fs.",
                agent_name,
                attempt + 1,
                _MAX_RETRIES,
                delay,
            )
            time.sleep(delay)


def _get_tracer():
    """Return an OpenTelemetry tracer if available, else ``None`` (no-op spans)."""
    try:
        from opentelemetry import trace
    except ImportError:
        return None
    return trace.get_tracer("doc_reviewer.agents.prompt_agent")


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
        tracer = _get_tracer()
        if tracer is None:
            return await self._invoke_once(prompt)
        with tracer.start_as_current_span(f"invoke_agent {self.foundry_agent_name}") as span:
            span.set_attribute("gen_ai.operation.name", "invoke_agent")
            span.set_attribute("gen_ai.agent.name", self.foundry_agent_name)
            result = await self._invoke_once(prompt)
            span.set_attribute("gen_ai.response.output_chars", len(result.text))
            return result

    async def _invoke_once(self, prompt: str) -> _Result:
        response = await asyncio.to_thread(
            _create_with_retry,
            lambda: self._client.responses.create(
                input=prompt,
                store=True,
                extra_body={"agent_reference": self._agent_reference},
            ),
            agent_name=self.foundry_agent_name,
        )
        return _Result(text=response.output_text)

    async def _run_stream(self, prompt: str) -> AsyncIterator[_Chunk]:
        tracer = _get_tracer()
        if tracer is None:
            async for chunk in self._invoke_stream(prompt):
                yield chunk
            return
        with tracer.start_as_current_span(f"invoke_agent {self.foundry_agent_name}") as span:
            span.set_attribute("gen_ai.operation.name", "invoke_agent")
            span.set_attribute("gen_ai.agent.name", self.foundry_agent_name)
            total = 0
            async for chunk in self._invoke_stream(prompt):
                total += len(chunk.text)
                yield chunk
            span.set_attribute("gen_ai.response.output_chars", total)

    async def _invoke_stream(self, prompt: str) -> AsyncIterator[_Chunk]:
        # The OpenAI SDK stream is synchronous; pull each event off in a worker
        # thread so the async orchestrator is never blocked.
        stream = await asyncio.to_thread(
            _create_with_retry,
            lambda: self._client.responses.create(
                input=prompt,
                stream=True,
                store=True,
                extra_body={"agent_reference": self._agent_reference},
            ),
            agent_name=self.foundry_agent_name,
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

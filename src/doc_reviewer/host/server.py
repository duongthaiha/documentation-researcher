"""Responses-protocol server that hosts the doc-reviewer orchestrator in Foundry.

This is the Pro-code **Hosted Agent** entrypoint. It accepts a review request,
runs the existing two-phase orchestration against the already-deployed sub-agent
*prompt agents* (via :func:`doc_reviewer.orchestrator.run_review_hosted`), and
returns the reviewed document.

Request body (sent as the Responses input text) is either:

* a JSON object ``{"document": "...", "industries": ["fsi", ...], "rounds": 3}``
  (``industries``/``rounds`` optional), or
* plain text, which is treated as the document with default industries/rounds.

Because the agent runs in Foundry's cloud, callers send the document **content**
here — not a local file path like the ``doc-reviewer --file`` CLI. See this
package's ``README.md`` ("Invoking when deployed on Azure") for client examples.

The ``azure-ai-agentserver-responses`` library is imported lazily so this module
(and its pure request parser) can be imported and unit-tested without the
preview hosting dependency installed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from doc_reviewer.agents.registry import CUSTOMER_INDUSTRIES
from doc_reviewer.config import Settings
from doc_reviewer.orchestrator import run_review_hosted


@dataclass
class ReviewRequest:
    """A parsed review request."""

    document: str
    industries: list[str]
    rounds: int


def parse_review_request(raw: str, settings: Settings) -> ReviewRequest:
    """Parse the Responses input text into a :class:`ReviewRequest`.

    Accepts a JSON object with ``document``/``industries``/``rounds`` keys, or
    falls back to treating the raw text as the document. Unknown industries are
    dropped; if none remain (or none were given) all supported industries run.
    Defaults for ``rounds`` come from ``settings``.
    """
    industries = list(CUSTOMER_INDUSTRIES)
    rounds = settings.review_rounds
    document = raw or ""

    payload = None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        payload = None

    if isinstance(payload, dict):
        document = payload.get("document") or payload.get("input") or ""

        requested = payload.get("industries")
        if requested:
            if isinstance(requested, str):
                requested = [requested]
            valid = [i for i in requested if i in CUSTOMER_INDUSTRIES]
            industries = valid or list(CUSTOMER_INDUSTRIES)

        if payload.get("rounds") is not None:
            try:
                rounds = int(payload["rounds"])
            except (TypeError, ValueError):
                pass

    return ReviewRequest(
        document=document, industries=industries, rounds=max(1, rounds)
    )


async def run_review_request(req: ReviewRequest, settings: Settings) -> str:
    """Run the hosted review for a parsed request and return the updated doc."""
    _conversation, updated_document = await run_review_hosted(
        settings=settings,
        document_content=req.document,
        industries=req.industries,
        rounds=req.rounds,
        research_dir=settings.research_dir,
    )
    return updated_document


def create_app():
    """Build the Responses hosting app with the review handler registered.

    The hosting library is imported here (not at module import time) so the rest
    of the project does not require the preview ``azure-ai-agentserver-responses``
    package.
    """
    import asyncio

    from azure.ai.agentserver.responses import (
        CreateResponse,
        ResponseContext,
        ResponsesAgentServerHost,
        TextResponse,
    )

    app = ResponsesAgentServerHost()

    @app.response_handler
    async def handler(
        request: "CreateResponse",
        context: "ResponseContext",
        _cancellation_signal: "asyncio.Event",
    ):
        raw = await context.get_input_text() or ""
        settings = Settings.from_env()
        req = parse_review_request(raw, settings)

        if not req.document.strip():
            return TextResponse(
                context,
                request,
                text=(
                    "Error: no document provided. Send the document text, or a "
                    'JSON payload like {"document": "...", "industries": '
                    '["fsi"], "rounds": 3}.'
                ),
            )

        try:
            updated_document = await run_review_request(req, settings)
        except Exception as exc:  # noqa: BLE001 - return a concise error to the caller
            return TextResponse(
                context,
                request,
                text=f"Review failed: {type(exc).__name__}: {exc}",
            )
        return TextResponse(context, request, text=updated_document)

    return app


def run() -> None:
    """Entrypoint: build the app and start the Responses HTTP server."""
    create_app().run()


if __name__ == "__main__":
    run()

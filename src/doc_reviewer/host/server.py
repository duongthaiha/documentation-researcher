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

# Defensive upper bound so an accidentally large `rounds` can't fan out into a
# huge number of agent calls / tokens (calls ≈ 2 * rounds * industries + 1).
_MAX_ROUNDS = 5


@dataclass
class ReviewRequest:
    """A parsed review request."""

    document: str
    industries: list[str]
    rounds: int
    # True when the document came from an explicit JSON ``document``/``input``
    # field (clear review intent); False when it's bare text we're guessing at.
    explicit: bool = False


HELP_TEXT = (
    "👋 Hi! I'm the **documentation reviewer** orchestrator. Send me an "
    "architecture or guidance document and I'll have industry customer agents "
    "(FSI / Manufacturing / Engineering) review it, a research agent answer "
    "their questions, and a writer agent return an improved version.\n\n"
    "Send either:\n"
    "• the document text directly, or\n"
    '• a JSON payload: {"document": "# My architecture...", '
    '"industries": ["fsi"], "rounds": 1}\n\n'
    "`industries` and `rounds` are optional. A real review calls several agents "
    "and takes about a minute per round per industry."
)

_GREETINGS = {
    "hi", "hello", "hey", "yo", "hiya", "hi there", "hello there", "howdy",
    "test", "testing", "ping", "help", "?", "hi!", "hello!", "start",
    "what can you do", "what can you do?", "who are you", "who are you?",
}


def is_trivial_input(raw: str, *, explicit: bool) -> bool:
    """Return True for greetings/short chatter that shouldn't trigger a review.

    Only applies to bare text (``explicit=False``); an explicit JSON ``document``
    is always treated as a real review, however short.
    """
    if explicit:
        return False
    text = (raw or "").strip()
    if not text:
        return True
    lowered = text.lower().strip("!.?")
    if lowered in _GREETINGS:
        return True
    # Too short and single-line to be a document worth a multi-agent review.
    if len(text) < 40 and "\n" not in text:
        return True
    return False


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
    explicit = False

    payload = None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        payload = None

    if isinstance(payload, dict):
        document = payload.get("document") or payload.get("input") or ""
        explicit = bool(document)

        requested = payload.get("industries")
        if requested:
            if isinstance(requested, str):
                requested = [requested]
            # De-duplicate while preserving order so a repeated industry can't
            # double the number of agent calls.
            valid = list(
                dict.fromkeys(i for i in requested if i in CUSTOMER_INDUSTRIES)
            )
            industries = valid or list(CUSTOMER_INDUSTRIES)

        if payload.get("rounds") is not None:
            try:
                rounds = int(payload["rounds"])
            except (TypeError, ValueError):
                pass

    return ReviewRequest(
        document=document,
        industries=industries,
        rounds=max(1, min(rounds, _MAX_ROUNDS)),
        explicit=explicit,
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

    from doc_reviewer.host.observability import (
        configure_foundry_telemetry,
        flush_telemetry,
        get_tracer,
    )

    configure_foundry_telemetry()
    tracer = get_tracer()

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

        # Greetings / short chatter shouldn't trigger an expensive multi-agent
        # review (which would also burn model quota). Answer with usage help.
        if is_trivial_input(raw, explicit=req.explicit) or not req.document.strip():
            return TextResponse(context, request, text=HELP_TEXT)

        try:
            if tracer is not None:
                with tracer.start_as_current_span("doc_review") as span:
                    span.set_attribute("doc_review.industries", ",".join(req.industries))
                    span.set_attribute("doc_review.rounds", req.rounds)
                    span.set_attribute("doc_review.document_chars", len(req.document))
                    updated_document = await run_review_request(req, settings)
                    span.set_attribute(
                        "doc_review.output_chars", len(updated_document)
                    )
            else:
                updated_document = await run_review_request(req, settings)
        except Exception as exc:  # noqa: BLE001 - return a concise error to the caller
            return TextResponse(
                context, request, text=_friendly_error(exc)
            )
        finally:
            # Push buffered telemetry before the sandbox scales to zero.
            flush_telemetry()
        return TextResponse(context, request, text=updated_document)

    return app


def _friendly_error(exc: Exception) -> str:
    """Turn an exception into a concise, actionable message for the caller."""
    text = str(exc)
    if "rate limit" in text.lower() or getattr(exc, "status_code", None) == 429:
        return (
            "⏳ The review hit the model's rate limit (quota) and couldn't "
            "finish. The underlying model deployment is throttled — wait a "
            "moment and try again, reduce `rounds`/`industries`, or raise the "
            "deployment's tokens-per-minute quota in Azure AI Foundry.\n\n"
            f"Details: {type(exc).__name__}: {text}"
        )
    return f"Review failed: {type(exc).__name__}: {text}"


def run() -> None:
    """Entrypoint: build the app and start the Responses HTTP server."""
    create_app().run()


if __name__ == "__main__":
    run()

"""Client CLI that invokes the **deployed** doc-reviewer orchestrator Hosted Agent.

Because the hosted agent runs in Foundry's cloud, it cannot read files on your
machine. This client reads a local document, sends its **content** to the agent
via the Responses API, and writes the reviewed document back to a local file.

Usage::

    # install the client deps (azure-ai-projects, openai) once
    pip install ".[host]"

    export DOC_REVIEWER_AGENT_ENDPOINT="https://ai-account-unf63h5g4tg6u.services.ai.azure.com/api/projects/ai-project-doc-reviewer-orchestrator-dev"
    doc-reviewer-invoke --file "document/Microsoft Foundry adoption across my organization.md" --industry fsi --rounds 1

The endpoint is the project that **hosts the orchestrator agent** (printed by
``azd deploy``), which may differ from ``AZURE_AI_PROJECT_ENDPOINT`` (the project
that hosts the sub-agent prompt agents). Authentication uses
``DefaultAzureCredential`` (run ``az login``); the caller needs Foundry
data-plane roles (e.g. Cognitive Services User + Azure AI Developer) on that
project.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from doc_reviewer.agents.registry import CUSTOMER_INDUSTRIES

DEFAULT_AGENT_NAME = "doc-reviewer-orchestrator"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="doc-reviewer-invoke",
        description=(
            "Invoke the deployed doc-reviewer orchestrator Hosted Agent with the "
            "contents of a local document and save the reviewed result."
        ),
    )
    parser.add_argument(
        "--file", required=True, help="Path to the local document to review (text/Markdown)."
    )
    parser.add_argument(
        "--industry",
        nargs="+",
        choices=list(CUSTOMER_INDUSTRIES),
        help="Industries to review from (default: the agent's default = all).",
    )
    parser.add_argument(
        "--rounds", type=int, help="Number of Q&A rounds (default: the agent's default)."
    )
    parser.add_argument(
        "--output",
        help="Where to write the reviewed document (default: <name>_reviewed<ext>).",
    )
    parser.add_argument(
        "--agent-name",
        default=os.environ.get("DOC_REVIEWER_AGENT_NAME", DEFAULT_AGENT_NAME),
        help=f"Deployed agent name (default: {DEFAULT_AGENT_NAME} or $DOC_REVIEWER_AGENT_NAME).",
    )
    parser.add_argument(
        "--project-endpoint",
        default=os.environ.get("DOC_REVIEWER_AGENT_ENDPOINT", ""),
        help="Project endpoint that hosts the agent (or $DOC_REVIEWER_AGENT_ENDPOINT).",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Wait for the full response instead of streaming output.",
    )
    return parser.parse_args(argv)


def _build_payload(args: argparse.Namespace) -> str:
    document = Path(args.file).expanduser().read_text(encoding="utf-8")
    payload: dict[str, object] = {"document": document}
    if args.industry:
        payload["industries"] = args.industry
    if args.rounds is not None:
        payload["rounds"] = args.rounds
    return json.dumps(payload)


def _agent_base_url(project_endpoint: str, agent_name: str) -> str:
    """Build the OpenAI base URL for a hosted agent's dedicated endpoint."""
    return (
        f"{project_endpoint.rstrip('/')}/agents/{agent_name}"
        "/endpoint/protocols/openai"
    )


def _create_client(project_endpoint: str, agent_name: str):
    # Hosted agents must be called through their *own* agent endpoint (not the
    # project-level Responses endpoint with an agent_reference, which is how
    # prompt agents are invoked). Point the OpenAI SDK at that endpoint and
    # authenticate with an Entra bearer token.
    from azure.identity import DefaultAzureCredential
    from openai import OpenAI

    token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
    return OpenAI(
        base_url=_agent_base_url(project_endpoint, agent_name),
        api_key=token,
        default_query={"api-version": "v1"},
    )


def _invoke(client, payload: str, *, stream: bool) -> str:
    if not stream:
        resp = client.responses.create(input=payload)
        return resp.output_text

    chunks: list[str] = []
    events = client.responses.create(input=payload, stream=True)
    for event in events:
        if getattr(event, "type", None) == "response.output_text.delta":
            print(event.delta, end="", flush=True)
            chunks.append(event.delta)
    print()
    return "".join(chunks)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if not args.project_endpoint:
        print(
            "❌ No agent project endpoint. Pass --project-endpoint or set "
            "DOC_REVIEWER_AGENT_ENDPOINT to the project that hosts the agent "
            "(printed by `azd deploy`).",
            file=sys.stderr,
        )
        sys.exit(1)

    src = Path(args.file).expanduser()
    if not src.is_file():
        print(f"❌ File not found: {src}", file=sys.stderr)
        sys.exit(1)

    output_path = (
        Path(args.output).expanduser()
        if args.output
        else src.with_name(f"{src.stem}_reviewed{src.suffix}")
    )

    print(f"📄 Document: {src}")
    print(f"🤖 Agent: {args.agent_name} @ {args.project_endpoint}")
    print(f"🏭 Industries: {', '.join(args.industry) if args.industry else 'agent default (all)'}")
    print(f"🔄 Rounds: {args.rounds if args.rounds is not None else 'agent default'}")
    print("⏳ Reviewing (this can take ~1 min per round per industry)...\n")

    payload = _build_payload(args)
    client = _create_client(args.project_endpoint, args.agent_name)
    reviewed = _invoke(client, payload, stream=not args.no_stream)

    output_path.write_text(reviewed, encoding="utf-8")
    print(f"\n✅ Reviewed document saved to: {output_path}")


if __name__ == "__main__":
    main()

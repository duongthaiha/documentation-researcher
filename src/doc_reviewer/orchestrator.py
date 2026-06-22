"""Conversation orchestrator for multi-agent document review."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from langfuse import propagate_attributes

from doc_reviewer.config import Settings
from doc_reviewer.research_corpus import (
    find_relevant_research,
    format_research_context,
)


@dataclass
class ConversationMessage:
    """A single message in the conversation."""

    agent_name: str
    content: str


@dataclass
class ReviewSession:
    """Holds the state of a document review session."""

    document_content: str
    industries: list[str]
    rounds: int
    research_dir: Path
    conversation: list[ConversationMessage] = field(default_factory=list)


def _format_conversation_history(conversation: list[ConversationMessage]) -> str:
    """Format conversation history for injection into agent prompts."""
    if not conversation:
        return ""

    lines = ["## Conversation So Far\n"]
    for msg in conversation:
        lines.append(f"**{msg.agent_name}**: {msg.content}\n")

    return "\n".join(lines)


async def run_review(
    settings: Settings,
    document_content: str,
    industries: list[str],
    rounds: int,
    research_dir: Path,
) -> tuple[list[ConversationMessage], str]:
    """Run a full document review session.

    Returns:
        Tuple of (conversation history, updated document content)
    """
    # Imported lazily so the hosted orchestrator container (which only uses the
    # ``run_review_hosted`` path) does not need the heavy ``agent-framework``
    # dependency tree.
    from agent_framework import MCPStreamableHTTPTool
    from azure.identity.aio import DefaultAzureCredential
    from httpx import AsyncClient, Timeout

    from doc_reviewer.agents.base import (
        create_customer_agent,
        create_research_agent,
        create_writer_agent,
    )

    session = ReviewSession(
        document_content=document_content,
        industries=industries,
        rounds=rounds,
        research_dir=research_dir,
    )

    github_http_client = AsyncClient(
        headers={"Authorization": f"Bearer {settings.github_mcp_token}"},
        follow_redirects=True,
        timeout=Timeout(30, read=300),
    )

    async with (
        DefaultAzureCredential() as credential,
        MCPStreamableHTTPTool(
            name="Microsoft Learn MCP",
            url=settings.ms_learn_mcp_url,
            tool_name_prefix="mslearn",
        ) as ms_learn_mcp,
        MCPStreamableHTTPTool(
            name="WorkIQ MCP",
            url=settings.workiq_mcp_url,
            tool_name_prefix="workiq",
        ) as workiq_mcp,
        MCPStreamableHTTPTool(
            name="GitHub MCP",
            url=settings.github_mcp_url,
            tool_name_prefix="github",
            request_timeout=30,
            http_client=github_http_client,
        ) as github_mcp,
    ):
        # Group all traces under one Langfuse session
        session_id = f"doc-review-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        industry_label = "+".join(industries)

        with propagate_attributes(
            session_id=session_id,
            tags=["doc-reviewer", *industries],
            metadata={"industries": industry_label, "rounds": str(rounds)},
        ):
            # Create local agents (instructions + tools shipped from code).
            research_agent = create_research_agent(
                settings,
                credential,
                [ms_learn_mcp, workiq_mcp, github_mcp],
            )
            customer_agents = []
            for industry in industries:
                agent = create_customer_agent(settings, credential, industry)
                customer_agents.append((industry, agent))

            writer_agent = create_writer_agent(settings, credential)

            return await _run_conversation(
                session, research_agent, customer_agents, writer_agent
            )


async def run_review_hosted(
    settings: Settings,
    document_content: str,
    industries: list[str],
    rounds: int,
    research_dir: Path,
) -> tuple[list[ConversationMessage], str]:
    """Run a review against the **prompt agents deployed in Azure AI Foundry**.

    Instead of constructing agents from code, this invokes the already-deployed
    prompt agents by name through the project's Responses API (see
    :mod:`doc_reviewer.agents.prompt_agent`). The instructions, model, and tools
    are resolved server-side, so no local MCP tool wiring is required.
    """
    # Imported lazily so the default (local) path doesn't require azure-ai-projects.
    from doc_reviewer.agents.prompt_agent import (
        build_prompt_agents,
        create_project_client,
    )

    session = ReviewSession(
        document_content=document_content,
        industries=industries,
        rounds=rounds,
        research_dir=research_dir,
    )

    session_id = (
        f"doc-review-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-"
        f"{uuid.uuid4().hex[:6]}"
    )
    industry_label = "+".join(industries)

    with (
        create_project_client(settings) as project_client,
        propagate_attributes(
            session_id=session_id,
            tags=["doc-reviewer", "hosted", *industries],
            metadata={
                "industries": industry_label,
                "rounds": str(rounds),
                "execution": "hosted",
            },
        ),
    ):
        research_agent, customer_agents, writer_agent = build_prompt_agents(
            project_client, industries
        )
        return await _run_conversation(
            session, research_agent, customer_agents, writer_agent
        )


async def _run_conversation(
    session: ReviewSession,
    research_agent,
    customer_agents,
    writer_agent,
) -> tuple[list[ConversationMessage], str]:
    """Drive the two-phase review loop.

    Agent-source agnostic: works with both local Agent Framework agents and
    :class:`~doc_reviewer.agents.prompt_agent.PromptAgentClient` instances, since
    both expose the same ``run(prompt, stream=True)`` / ``await run(prompt)``
    interface.
    """
    rounds = session.rounds

    # Phase 1: Customer Q&A rounds
    print("\n" + "=" * 60)
    print("📋 PHASE 1: Customer Review & Research")
    print("=" * 60)

    for round_num in range(1, rounds + 1):
        print(f"\n--- Round {round_num}/{rounds} ---\n")

        # Each customer agent asks questions
        for industry, customer_agent in customer_agents:
            customer_prompt = _build_customer_prompt(session, round_num)

            print(f"🏢 [{industry.upper()} Customer]: ", end="", flush=True)
            response_text = ""
            async for chunk in customer_agent.run(customer_prompt, stream=True):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    response_text += chunk.text
            print("\n")

            session.conversation.append(
                ConversationMessage(
                    agent_name=f"{industry.upper()} Customer",
                    content=response_text,
                )
            )

            # Research agent answers
            research_prompt = _build_research_prompt(session)

            print("🔬 [Research Agent]: ", end="", flush=True)
            response_text = ""
            async for chunk in research_agent.run(research_prompt, stream=True):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    response_text += chunk.text
            print("\n")

            session.conversation.append(
                ConversationMessage(
                    agent_name="Research Agent",
                    content=response_text,
                )
            )

    # Phase 2: Writer updates the document
    print("\n" + "=" * 60)
    print("✍️  PHASE 2: Document Update")
    print("=" * 60 + "\n")

    writer_prompt = _build_writer_prompt(session)

    print("📝 [Writer Agent]: Updating document...\n")
    result = await writer_agent.run(writer_prompt)
    updated_document = result.text
    print("✅ Document updated successfully.\n")

    return session.conversation, updated_document


def _build_customer_prompt(session: ReviewSession, round_num: int) -> str:
    """Build the prompt for a customer agent's turn."""
    history = _format_conversation_history(session.conversation)

    if round_num == 1 and not session.conversation:
        return (
            f"Please review the following architecture/guidance document and ask "
            f"2-3 specific questions about gaps or missing best practices from your "
            f"industry perspective.\n\n"
            f"## Document to Review\n\n{session.document_content}"
        )
    else:
        return (
            f"Continue reviewing the document. Based on the research answers provided, "
            f"ask 1-2 follow-up questions about remaining gaps or areas that need "
            f"more clarification.\n\n"
            f"## Original Document\n\n{session.document_content}\n\n"
            f"{history}"
        )


def _build_research_prompt(session: ReviewSession) -> str:
    """Build the prompt for the research agent's turn."""
    # Get the last customer question
    last_question = session.conversation[-1]
    history = _format_conversation_history(session.conversation[:-1])
    local_research_context = format_research_context(
        find_relevant_research(session.research_dir, last_question.content)
    )
    local_research_section = (
        f"\n\n{local_research_context}\n\n"
        if local_research_context
        else "\n\n"
    )

    return (
        f"A customer ({last_question.agent_name}) has asked the following questions "
        f"about this architecture document. Research the answers using the local "
        f"research context when provided and your tools, then provide specific, "
        f"actionable guidance.\n\n"
        f"## Original Document\n\n{session.document_content}\n\n"
        f"{history}\n\n"
        f"{local_research_section}"
        f"## Latest Question from {last_question.agent_name}\n\n"
        f"{last_question.content}"
    )


def _build_writer_prompt(session: ReviewSession) -> str:
    """Build the prompt for the writer agent."""
    history = _format_conversation_history(session.conversation)
    industry_label = ", ".join(i.upper() for i in session.industries)

    return (
        f"Below is the original document and the full conversation transcript from "
        f"the review session. The review was conducted from the perspective of the "
        f"following industry/industries: {industry_label}. "
        f"Mark any additions with `<!-- Added based on {industry_label} review -->`. "
        f"Please produce an updated version of the document that "
        f"incorporates the new guidance and best practices identified during the review.\n\n"
        f"## Original Document\n\n{session.document_content}\n\n"
        f"## Review Conversation Transcript\n\n{history}"
    )

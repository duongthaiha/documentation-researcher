"""Conversation orchestrator for multi-agent document review."""

from dataclasses import dataclass, field

from agent_framework import MCPStreamableHTTPTool
from azure.identity.aio import DefaultAzureCredential

from doc_reviewer.agents.base import (
    create_customer_agent,
    create_research_agent,
    create_writer_agent,
)
from doc_reviewer.config import Settings


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
) -> tuple[list[ConversationMessage], str]:
    """Run a full document review session.

    Returns:
        Tuple of (conversation history, updated document content)
    """
    session = ReviewSession(
        document_content=document_content,
        industries=industries,
        rounds=rounds,
    )

    async with (
        DefaultAzureCredential() as credential,
        MCPStreamableHTTPTool(
            name="WorkIQ MCP",
            url=settings.workiq_mcp_url,
        ) as workiq_mcp,
    ):
        # Create agents
        research_agent = create_research_agent(settings, workiq_mcp)
        customer_agents = []
        for industry in industries:
            agent = create_customer_agent(settings, industry)
            customer_agents.append((industry, agent))

        writer_agent = create_writer_agent(settings)

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
                async for chunk in customer_agent.run(
                    customer_prompt, stream=True
                ):
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
                async for chunk in research_agent.run(
                    research_prompt, stream=True
                ):
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
        updated_document = ""
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

    return (
        f"A customer ({last_question.agent_name}) has asked the following questions "
        f"about this architecture document. Research the answers using your tools "
        f"and provide specific, actionable guidance.\n\n"
        f"## Original Document\n\n{session.document_content}\n\n"
        f"{history}\n\n"
        f"## Latest Question from {last_question.agent_name}\n\n"
        f"{last_question.content}"
    )


def _build_writer_prompt(session: ReviewSession) -> str:
    """Build the prompt for the writer agent."""
    history = _format_conversation_history(session.conversation)

    return (
        f"Below is the original document and the full conversation transcript from "
        f"the review session. Please produce an updated version of the document that "
        f"incorporates the new guidance and best practices identified during the review.\n\n"
        f"## Original Document\n\n{session.document_content}\n\n"
        f"## Review Conversation Transcript\n\n{history}"
    )

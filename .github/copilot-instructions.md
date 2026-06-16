# Documentation Reviewer — Copilot Instructions

## Project Purpose

This project implements a multi-agent system that reviews architecture and guidance documentation from industry-specific customer perspectives. It uses the **Microsoft Agent Framework** (`agent-framework-azure-ai`) with Azure OpenAI.

## Architecture

The system operates in two phases:

1. **Phase 1 — Customer Q&A**: Customer agents (representing specific industries) read the document and ask clarifying questions about gaps or missing best practices. A Research agent answers those questions using Microsoft Learn and WorkIQ MCP tools.

2. **Phase 2 — Document Update**: A Writer agent takes the original document plus the full conversation transcript and produces an updated version incorporating the new guidance.

## Agents

### Customer Agents
- **Persona**: IT Architect / CTO at a company in the given industry
- **Behavior**: Pretend to BE the customer. Ask clarifying questions about what's missing, unclear, or insufficient in the documentation. Do NOT answer questions — only ASK them.
- **Industries implemented**:
  - **FSI (Financial Services)**: Focus on security, regulatory compliance (PCI-DSS, SOX, GDPR), network isolation, data sovereignty, encryption, zero-trust, HA (99.99%+)
  - **Manufacturing**: Focus on edge computing, IoT, OT/IT convergence, low-latency, factory floor connectivity, SCADA/ICS security, hybrid cloud, intermittent connectivity
  - **Engineering**: Focus on building agents in Foundry with DevOps practices, CI/CD, prompt/tool versioning, eval gates, observability, rollback, and secure release automation

### Research Agent
- **Role**: Technical researcher
- **Tools**: Microsoft Learn MCP, WorkIQ MCP
- **Behavior**: Answers customer questions with researched best practices, reference architectures, and citations from Microsoft documentation

### Writer Agent
- **Role**: Technical writer
- **Behavior**: Receives the original document + conversation transcript. Produces an updated document with missing guidance incorporated. Preserves original structure and tone.

## Conventions

- **Async-first**: All agent code uses `async/await` and async context managers
- **Environment config**: All secrets/endpoints via environment variables (see `.env.example`)
- **Agent Framework patterns**: Use `FoundryAgent` from `agent_framework.foundry`, `MCPStreamableHTTPTool` for MCP servers
- **Type hints**: Use Python typing throughout (Annotated, Field for tool params)
- **Error handling**: Graceful degradation — if MCP tools fail, agents fall back to LLM knowledge

## Adding a New Industry Agent

1. Create `src/doc_reviewer/agents/<industry>_customer.py`
2. Define the agent's system prompt with industry-specific focus areas
3. Add the industry to `SUPPORTED_INDUSTRIES` in `main.py` and `create_customer_agent()` in `agents/base.py`
4. The orchestrator will automatically pick it up when `--industry <name>` is used

## Running

```bash
doc-reviewer --file path/to/document.md --rounds 3 --industry fsi manufacturing engineering
```

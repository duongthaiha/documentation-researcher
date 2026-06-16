# Documentation Reviewer

A multi-agent system that reviews architecture and guidance documentation from industry-specific customer perspectives, using the [Microsoft Agent Framework](https://pypi.org/project/agent-framework/) with Azure OpenAI.

## How It Works

```
Document → Customer Agents ask questions → Research Agent answers → Writer Agent updates doc
```

**Phase 1 — Customer Q&A:** Industry-specific customer agents (acting as IT Architects/CTOs) read your document and ask pointed questions about gaps and missing best practices. A Research Agent answers using Microsoft Learn and WorkIQ MCP tools.

**Phase 2 — Document Update:** A Writer Agent takes the original document plus the full conversation and produces an updated version with the new guidance incorporated.

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| FSI Customer | CTO at a financial services company. Asks about security, compliance, network isolation. | None (LLM) |
| Manufacturing Customer | CTO at a manufacturer. Asks about edge, IoT, OT/IT convergence. | None (LLM) |
| Research Agent | Answers customer questions with researched best practices. | Microsoft Learn MCP, WorkIQ MCP |
| Writer Agent | Updates the document with new guidance from the review. | None (LLM) |

## Setup

### Prerequisites

- Python 3.11+
- Azure AI Foundry project with a deployed model (e.g., `gpt-4o`)
- WorkIQ MCP server running locally
- Azure CLI authenticated (`az login`)

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `AZURE_AI_PROJECT_ENDPOINT` — Your Azure AI Foundry project endpoint
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` — Model deployment name (default: `gpt-4o`)
- `WORKIQ_MCP_URL` — URL of your WorkIQ MCP server

## Usage

```bash
# Review with all industries (default)
doc-reviewer --file docs/architecture.md

# Review with specific industries
doc-reviewer --file docs/architecture.md --industry fsi

# Custom number of Q&A rounds
doc-reviewer --file docs/architecture.md --rounds 5 --industry fsi manufacturing
```

The updated document is saved as `<original_name>_reviewed.<ext>` in the same directory.

## Adding a New Industry

1. Create `src/doc_reviewer/agents/<industry>_customer.py` with an `<INDUSTRY>_INSTRUCTIONS` string
2. Add the industry to `create_customer_agent()` in `src/doc_reviewer/agents/base.py`
3. Add to `SUPPORTED_INDUSTRIES` in `src/doc_reviewer/main.py`

## Project Structure

```
src/doc_reviewer/
├── main.py              # CLI entry point
├── config.py            # Environment configuration
├── orchestrator.py      # Two-phase conversation orchestrator
├── agents/
│   ├── base.py          # Agent factory
│   ├── research.py      # Research agent (MCP tools)
│   ├── fsi_customer.py  # FSI customer persona
│   ├── manufacturing_customer.py  # Manufacturing customer persona
│   └── writer.py        # Document writer agent
└── document/
    └── loader.py        # Markdown/PDF loader
```

## License

MIT

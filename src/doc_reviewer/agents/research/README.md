# Research Agent

Technical research agent that answers customer questions with researched best
practices and citations. Uses local Markdown research docs plus Microsoft Learn,
WorkIQ, and GitHub MCP tools.

## Files

| File | Purpose |
|------|---------|
| `instructions.py` | `RESEARCH_INSTRUCTIONS` system prompt (single source of truth). |
| `factory.py` | `create_agent(settings, credential, mcp_tools)` — local Agent Framework agent. |
| `definition.py` | `build_prompt_agent_definition(settings)` + `build_mcp_tools(settings)` — Foundry `PromptAgentDefinition` with hosted MCP tools. |
| `agent.yaml` | Declarative metadata (name, description, model, MCP tools, version). |
| `deploy.py` | Publish/version this prompt agent to Foundry. |

## Tools

MCP server URLs are resolved from `Settings` (env vars):
`MS_LEARN_MCP_URL` (default Microsoft Learn), `WORKIQ_MCP_URL`, `GITHUB_MCP_URL`.

## Run locally

Used automatically by the orchestrator during the Q&A phase.

## Deploy to Foundry (prompt agent)

```bash
pip install "doc-reviewer[deploy]"
python -m doc_reviewer.agents.research.deploy            # dry run
python -m doc_reviewer.agents.research.deploy --publish  # publish
```

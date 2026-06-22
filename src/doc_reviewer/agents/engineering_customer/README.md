# Engineering Customer Agent

Engineering lead / platform architect persona building agents on Microsoft
Foundry. Reviews architecture and guidance docs and asks about DevOps, CI/CD,
agent/prompt/tool versioning, eval gates, release safety, rollback, and
observability.

## Files

| File | Purpose |
|------|---------|
| `instructions.py` | `ENGINEERING_INSTRUCTIONS` system prompt (single source of truth). |
| `factory.py` | `create_agent(settings, credential)` — local Agent Framework agent. |
| `definition.py` | `build_prompt_agent_definition(settings)` — Foundry `PromptAgentDefinition`. |
| `agent.yaml` | Declarative metadata (name, description, model, tools, version). |
| `deploy.py` | Publish/version this prompt agent to Foundry. |

## Run locally

```bash
doc-reviewer --file path/to/document.md --industry engineering
```

## Deploy to Foundry (prompt agent)

```bash
pip install "doc-reviewer[deploy]"
python -m doc_reviewer.agents.engineering_customer.deploy            # dry run
python -m doc_reviewer.agents.engineering_customer.deploy --publish  # publish
```

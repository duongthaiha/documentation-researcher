# Writer Agent

Technical writer agent. Receives the original document plus the full review
conversation transcript and produces an updated document with the new guidance
incorporated, preserving the original structure and tone.

## Files

| File | Purpose |
|------|---------|
| `instructions.py` | `WRITER_INSTRUCTIONS` system prompt (single source of truth). |
| `factory.py` | `create_agent(settings, credential)` — local Agent Framework agent. |
| `definition.py` | `build_prompt_agent_definition(settings)` — Foundry `PromptAgentDefinition`. |
| `agent.yaml` | Declarative metadata (name, description, model, tools, version). |
| `deploy.py` | Publish/version this prompt agent to Foundry. |

## Run locally

Used automatically by the orchestrator during the document-update phase.

## Deploy to Foundry (prompt agent)

```bash
pip install "doc-reviewer[deploy]"
python -m doc_reviewer.agents.writer.deploy            # dry run
python -m doc_reviewer.agents.writer.deploy --publish  # publish
```

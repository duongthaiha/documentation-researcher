# FSI Customer Agent

IT Architect / CTO persona at a Tier 1 financial-services institution. Reviews
architecture and guidance docs and asks pointed questions about security,
regulatory compliance (PCI-DSS, SOX, GDPR, DORA), network isolation, data
sovereignty, and high availability.

## Files

| File | Purpose |
|------|---------|
| `instructions.py` | `FSI_INSTRUCTIONS` system prompt (single source of truth). |
| `factory.py` | `create_agent(settings, credential)` — local Agent Framework agent. |
| `definition.py` | `build_prompt_agent_definition(settings)` — Foundry `PromptAgentDefinition`. |
| `agent.yaml` | Declarative metadata (name, description, model, tools, version). |
| `deploy.py` | Publish/version this prompt agent to Foundry. |

## Run locally

Used automatically by the orchestrator:

```bash
doc-reviewer --file path/to/document.md --industry fsi
```

## Deploy to Foundry (prompt agent)

```bash
pip install "doc-reviewer[deploy]"
python -m doc_reviewer.agents.fsi_customer.deploy            # dry run
python -m doc_reviewer.agents.fsi_customer.deploy --publish  # actually publish
```

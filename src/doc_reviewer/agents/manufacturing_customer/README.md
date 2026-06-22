# Manufacturing Customer Agent

IT Architect / CTO persona at a global manufacturer. Reviews architecture and
guidance docs and asks practical questions about edge computing, IoT, OT/IT
convergence, SCADA/ICS security, intermittent connectivity, and low-latency
control loops.

## Files

| File | Purpose |
|------|---------|
| `instructions.py` | `MANUFACTURING_INSTRUCTIONS` system prompt (single source of truth). |
| `factory.py` | `create_agent(settings, credential)` — local Agent Framework agent. |
| `definition.py` | `build_prompt_agent_definition(settings)` — Foundry `PromptAgentDefinition`. |
| `agent.yaml` | Declarative metadata (name, description, model, tools, version). |
| `deploy.py` | Publish/version this prompt agent to Foundry. |

## Run locally

```bash
doc-reviewer --file path/to/document.md --industry manufacturing
```

## Deploy to Foundry (prompt agent)

```bash
pip install "doc-reviewer[deploy]"
python -m doc_reviewer.agents.manufacturing_customer.deploy            # dry run
python -m doc_reviewer.agents.manufacturing_customer.deploy --publish  # publish
```

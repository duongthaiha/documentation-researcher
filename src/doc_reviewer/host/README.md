# Hosted Agent: doc-reviewer orchestrator

This package hosts the **orchestrator** (the two-phase review loop) as an Azure AI
Foundry **Hosted Agent** (Pro-code) using the **Responses** protocol. The
sub-agents (FSI / Manufacturing / Engineering customer, Research, Writer) remain
**prompt agents** and are invoked **by name** — this package just wraps
`run_review_hosted` in a managed Azure endpoint.

```
Client ──(Responses API)──▶ Hosted Agent: doc-reviewer-orchestrator
                                  │  parse {document, industries, rounds}
                                  ▼
                            run_review_hosted(...)  ──by name──▶ prompt agents
                                  ▼
                          reviewed document (TextResponse)
```

## Files

| File | Purpose |
|------|---------|
| `server.py` | Responses handler + pure request parser (`parse_review_request`). |
| `main.py` | azd `--deploy-mode code` entrypoint (`python -m doc_reviewer.host.main`). |
| `requirements.txt` | Preview hosting lib (`azure-ai-agentserver-responses`) + projects SDK. |
| `Dockerfile` | Container image (Python 3.13) that installs the project + host deps. |

## Request contract

Send the Responses input as either JSON or plain text:

```json
{ "document": "# My architecture\n...", "industries": ["fsi", "engineering"], "rounds": 3 }
```

- `industries` / `rounds` are optional (default: all industries, `REVIEW_ROUNDS`).
- Plain text is treated as the document with defaults.
- Response body is the reviewed document.

## Prerequisites

- **Python 3.13+** (Hosted agents require it; the rest of the project supports 3.11+).
- The sub-agents already deployed as prompt agents:
  ```bash
  pip install ".[deploy]"
  doc-reviewer-deploy --publish
  ```
- A Foundry project + `az login`. Container identity needs **Foundry User** /
  project roles to invoke the sub-agents and call models, plus **AcrPull**.
- `azd >= 1.25.3` and the Foundry extension:
  ```bash
  azd ext install microsoft.foundry
  ```
- Configure `.env` (see repo `.env.example`): `AZURE_AI_PROJECT_ENDPOINT`,
  `AZURE_AI_MODEL_DEPLOYMENT_NAME`, etc.

## Deploy with azd (code mode)

Run from this directory (`src/doc_reviewer/host/`):

```bash
azd ai agent init --protocol responses --deploy-mode code   # scaffolds azure.yaml
azd provision                                               # App Insights, etc.
azd ai agent run                                            # local test + inspector
azd ai agent invoke --local '{"document": "# Doc\n...", "rounds": 1}'
azd deploy                                                  # deploy to Foundry
azd ai agent invoke '{"document": "# Doc\n...", "rounds": 1}'
```

> If azd code packaging does not include the parent project, deploy via the
> container path instead (build the `Dockerfile` from the repo root and use
> `azd ai agent init --deploy-mode container`).

## Local smoke test (no azd)

```bash
pip install ".[host]"          # needs Python 3.13
doc-reviewer-host              # starts the Responses server locally
```

## Notes

- The local `research/` corpus is bundled into the image by the Dockerfile (it
  copies the repo). Set `RESEARCH_DIR` if you relocate it.
- Hosted agents are in **preview**; pin the `azure-ai-agentserver-*` beta and use
  a [supported region](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents#region-availability).

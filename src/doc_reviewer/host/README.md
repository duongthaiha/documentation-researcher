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

## Invoking when deployed on Azure (send content, not a file path)

> **Important:** Unlike the local `doc-reviewer --file path/to/doc.md` CLI, the
> hosted agent runs in Foundry's cloud and **cannot read files on your machine**.
> You must read the file locally and send its **text** in the `document` field.
> The response body is the reviewed document — save it yourself.

You also need access to invoke the agent: `az login`, and your identity (or the
caller's) needs **Cognitive Services User** + **Azure AI Developer** (or
equivalent Foundry data-plane roles) on the project hosting the agent.

### Option A — `azd ai agent invoke` (build the payload from a local file)

Use `jq --rawfile` to safely embed the file's content as a JSON string:

```bash
# from the repo root; replace the agent/service name if different
PAYLOAD=$(jq -n --rawfile doc ./docs/architecture.md \
  '{document: $doc, industries: ["fsi"], rounds: 1}')

azd ai agent invoke doc-reviewer-orchestrator "$PAYLOAD" > docs/architecture_reviewed.md
```

For defaults (all industries, `REVIEW_ROUNDS` rounds) you can send the raw text:

```bash
azd ai agent invoke doc-reviewer-orchestrator "$(cat ./docs/architecture.md)"
```

### Option B — Python (OpenAI-compatible Responses API)

Mirrors how the orchestrator itself calls agents by name. Reads a local file,
sends its content, writes the reviewed result back to a local file:

```python
import json
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Project that hosts the orchestrator agent (the deploy output prints this).
PROJECT_ENDPOINT = "https://<account>.services.ai.azure.com/api/projects/<project>"
AGENT_NAME = "doc-reviewer-orchestrator"

src = Path("docs/architecture.md")
payload = json.dumps(
    {"document": src.read_text(encoding="utf-8"), "industries": ["fsi"], "rounds": 1}
)

client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
    allow_preview=True,
).get_openai_client()

resp = client.responses.create(
    input=payload,
    extra_body={"agent_reference": {"type": "agent_reference", "name": AGENT_NAME}},
)

out = src.with_name(f"{src.stem}_reviewed{src.suffix}")
out.write_text(resp.output_text, encoding="utf-8")
print(f"Wrote {out}")
```

To stream progress, add `stream=True` and iterate, collecting
`event.delta` from `response.output_text.delta` events.

### Option C — curl (raw HTTPS)

```bash
ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project>/agents/doc-reviewer-orchestrator/endpoint/protocols/openai/responses?api-version=v1"
TOKEN=$(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)

# Inner = the orchestrator payload; then wrap it as the Responses `input` string.
INNER=$(jq -n --rawfile doc ./docs/architecture.md '{document: $doc, industries: ["fsi"], rounds: 1}')
curl -s "$ENDPOINT" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "$(jq -n --arg inp "$INNER" '{input: $inp}')" \
  | jq -r '.output[].content[]?.text // empty' > docs/architecture_reviewed.md
```

> Tip: large documents are fine in the request body, but the review takes time
> (roughly a minute per round per industry). Keep `rounds` small for quick runs,
> and prefer the Python/streaming option for long documents so you see progress.

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

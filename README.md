# Clarity Engine

Clarity Engine is intent and context infrastructure: it standardizes how we generate clear, testable Context Packets for human–AI and agentic workflows so work stays aligned and auditable.

## Project State
All documented stages through Stage-07.2 are shipped:

| Stage | What ships |
|-------|------------|
| 01 | FastAPI HTTP service (`/healthz`, `/packets/compose`, `/packets/lint`, `/openapi.json?server=`) |
| 02 | Schema expansion (risk flags, allowed actions, evidence requirements), ambiguity detection, GPT Actions OpenAPI |
| 03 | Content-addressed filesystem registry; `POST /packets/register`, `GET /packets`, `GET /packets/{sha}`, `POST /packets/diff`, `GET /packets/{sha}/ancestors` |
| 04 | JCT-compatible `POST /packets/enqueue`; optional `callback_url` transport field |
| 05 | MCP server (`python -m app.mcp_server`) exposing compose/lint/register/get/list/diff/enqueue/check_action |
| 06 | Static browser UI at `/` with Browser / Intent / Diff / Editor tabs |
| 07 | Raw-intent draft intake (`POST /intents/draft`) returning reviewable PCP-lite manifests without registry writes |
| Raw Intent | Separate schema, deterministic tooling, immutable registry, lineage, diff, and HTTP access |
| Grounding | Source-attributed grounding, traceable clarification revisions, and readiness gates |

See `docs/vision/current_reality.md` for the full fact sheet.

## Authoritative Artifacts
These files define how the project operates and must stay in sync.
- `AGENTS.md` — operating guide and constraints for agents contributing to the repo.
- `CONTEXT_PACKET_TEMPLATE.md` — paste-ready Context Packet template aligned with the schema.
- `pcp_lite.schema.json` — machine-readable Project Context Protocol lite (PCP-lite) contract for packet manifests.
- `raw_intent_packet.schema.json` — provenance-preserving contract for ungrounded human intent.
- `packets/examples/context_packet_example.json` — minimal manifest example conforming to the PCP-lite schema.
- `packets/examples/raw_intent_packet_example.json` — canonical Raw Intent Packet example.
- `CLAUDE.md` — project guidance for Claude Code and the commit-per-substage workflow.
- `.github/workflows/ci.yml` — CI pipeline covering tests, packet checks, and import verification.

## Repository Structure
```
clarity-engine/
├── AGENTS.md                       # Rules for contributing agents
├── CLAUDE.md                       # Claude Code guidance
├── CONTEXT_PACKET_TEMPLATE.md      # Paste-ready prompt skeleton
├── pcp_lite.schema.json            # PCP-lite manifest contract
├── requirements.txt                # fastapi, uvicorn, pytest, mcp
├── app/
│   ├── main.py                     # FastAPI app (HTTP endpoints + UI mount)
│   ├── mcp_server.py               # MCP stdio server
│   ├── intent_registry.py          # Immutable Raw Intent Packet store
│   └── registry.py                 # Content-addressed filesystem store
├── tools/                          # compose_packet.py, lint_packet.py
├── packets/
│   ├── examples/                   # Golden manifests
│   └── registry/                   # Runtime packet store (gitignored)
├── ui/                             # Static browser UI (index.html)
├── docs/vision/                    # Stage missions and current_reality
└── .github/workflows/ci.yml
```

## How to Run

### HTTP service + UI
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# UI:       http://127.0.0.1:8000/
# API docs: http://127.0.0.1:8000/docs
# Health:   curl http://127.0.0.1:8000/healthz
```

### Docker Compose
Clarity Engine reserves host port `8010` for containerized local access. Port
`8000` is reserved for NGINX Manager on the host, so Compose maps host
`8010` to container port `8000`.

```bash
docker compose up --build
# UI:       http://127.0.0.1:8010/
# API docs: http://127.0.0.1:8010/docs
# Health:   curl http://127.0.0.1:8010/healthz
```

Runtime packet registry data is bind mounted from `./packets/registry` to
`/app/packets/registry` inside the container so the UI shows the same registered
packets as the host checkout. Generated registry artifacts remain excluded from
git. Raw Intent Packet records are independently bind mounted from
`./packets/intents` to `/app/packets/intents`. The container writes both
registries as UID/GID `1000:1000` by default so records remain editable by the
host user. Set `CLARITY_UID` and `CLARITY_GID` before starting Compose if the
checkout owner uses different numeric IDs.

### Compose / lint over HTTP
```bash
curl -s -X POST http://127.0.0.1:8000/packets/compose \
  -H "Content-Type: application/json" \
  -d @packets/examples/context_packet_example.json

curl -s -X POST http://127.0.0.1:8000/packets/lint \
  -H "Content-Type: application/json" \
  -d @packets/examples/context_packet_example.json
```

### Registry
```bash
curl -s -X POST http://127.0.0.1:8000/packets/register \
  -H "Content-Type: application/json" \
  -d @packets/examples/context_packet_example.json
curl -s http://127.0.0.1:8000/packets
curl -s http://127.0.0.1:8000/packets/<sha>
curl -s http://127.0.0.1:8000/packets/<sha>/ancestors
```

### Enqueue (JCT envelope)
```bash
curl -s -X POST http://127.0.0.1:8000/packets/enqueue \
  -H "Content-Type: application/json" \
  -d @packets/examples/context_packet_example.json
# Returns { task_id, context_sha, mission, manifest, packet_md,
#           allowed_actions, evidence_requirements, risk_flags,
#           callback_url, registered }
```

### MCP server
```bash
python -m app.mcp_server
# stdio transport; exposes 12 tools:
# Mission Packets: compose, lint, register, get, list, diff, enqueue, check_action
# Raw Intents: list, get, lineage, diff
```

### Using the MCP server from Claude Code
The repo ships a project-level `.mcp.json` that registers the Clarity Engine MCP server with Claude Code. On first use, Claude Code will ask you to approve it.

Prerequisite: the venv must exist so the configured command (`.venv/bin/python -m app.mcp_server`) resolves.
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
Then open this repo in Claude Code and approve the server when prompted. The 12
tools become callable directly in-session.

### CLI tools
```bash
python tools/compose_packet.py packets/examples/context_packet_example.json
python tools/lint_packet.py packets/examples/context_packet_example.json

python tools/raw_intent_packet.py lint \
  packets/examples/raw_intent_packet_example.json
python tools/raw_intent_packet.py compose \
  packets/examples/raw_intent_packet_example.json \
  --output-dir /tmp/raw-intent-packet
```

## Raw Intent Packet Contract

Raw Intent Packets preserve original human thought before grounding and are
separate from executable PCP-lite Mission Packets. The accepted `raw_intent`
string is never trimmed or rewritten. Deterministic composition emits
`manifest.json`, `intent.md`, and `intent_sha`.

See `docs/RAW_INTENT_PACKET.md` for field semantics, lifecycle values, identity
rules, persistence behavior, HTTP operations, and current exclusions.

### Raw Intent HTTP API

```bash
# Side-effect-free validation and composition
curl -s -X POST http://127.0.0.1:8000/intents/lint \
  -H "Content-Type: application/json" \
  -d @packets/examples/raw_intent_packet_example.json
curl -s -X POST http://127.0.0.1:8000/intents/compose \
  -H "Content-Type: application/json" \
  -d @packets/examples/raw_intent_packet_example.json

# Explicit persistence and retrieval
curl -s -X POST http://127.0.0.1:8000/intents/register \
  -H "Content-Type: application/json" \
  -d @packets/examples/raw_intent_packet_example.json
curl -s http://127.0.0.1:8000/intents
curl -s http://127.0.0.1:8000/intents/<intent_sha>
curl -s http://127.0.0.1:8000/intents/<intent_sha>/ancestors
```

`POST /intents/diff` accepts `left` and `right`, each an `intent_sha` or inline
Raw Intent Packet manifest. Registered revisions live under
`packets/intents/<intent_sha>/`; override the host runtime root with
`CLARITY_INTENT_REGISTRY_ROOT`.

Registration enforces immutable lineage: roots begin as `captured`, child
revisions must preserve `raw_intent` exactly, and status changes must follow the
documented lifecycle. Corrupt records and broken lineage return explicit errors.

### Grounding and clarification revisions

Grounding appends sourced entries and creates a new immutable child:

```bash
curl -s -X POST http://127.0.0.1:8000/intents/<intent_sha>/grounding \
  -H "Content-Type: application/json" \
  -d '{
    "entries": [{
      "kind": "verified_fact",
      "statement": "The repository contains app/main.py.",
      "sources": ["repo:app/main.py"]
    }],
    "unresolved_gaps": ["Confirm deployment owner."],
    "status": "grounding"
  }'
```

Clarification questions use stable IDs; answers target those IDs:

```bash
curl -s -X POST http://127.0.0.1:8000/intents/<intent_sha>/clarifications \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [{
      "id": "deployment-owner",
      "question": "Who owns deployment?"
    }]
  }'
```

An answer-only request defaults the child status to `grounding`:

```json
{
  "answers": [{
    "id": "deployment-owner",
    "answer": "The platform maintainer."
  }]
}
```

`ready_for_mission` requires at least one sourced structured `verified_fact`,
no open structured clarifications, and no unresolved gaps. Readiness does not
approve, promote, register, or enqueue a Mission Packet.

### Approved Mission Packet promotion

Promotion requires a registered `ready_for_mission` revision, a lint-clean
PCP-lite candidate, explicit human approval, and one verified source location
for every candidate `current_reality` and `constraints` entry:

```bash
curl -s -X POST http://127.0.0.1:8000/intents/<intent_sha>/promote \
  -H "Content-Type: application/json" \
  -d '{
    "mission_packet": {
      "mission": "Ship the bounded improvement.",
      "current_reality": ["The repository contains app/main.py."],
      "constraints": ["Do not build a general-purpose context platform."],
      "acceptance": ["The focused tests pass."],
      "required_artifacts": ["Implementation and tests exist."],
      "failure_modes": ["The change expands beyond the approved scope."],
      "substage_gate": ["Only the bounded improvement is in scope."]
    },
    "approval": {
      "approved": true,
      "approved_by": "Human product owner",
      "reference": "CLARITY-EN-28"
    },
    "grounding_references": [
      {
        "packet_field": "current_reality",
        "packet_index": 0,
        "intent_field": "grounding_entries",
        "intent_index": 0
      },
      {
        "packet_field": "constraints",
        "packet_index": 0,
        "intent_field": "constraints",
        "intent_index": 0
      }
    ]
  }'
```

The operation registers or reuses the Mission Packet, writes an authoritative
link under `packets/links/intent-missions/`, and registers a terminal
`promoted` Raw Intent child. It is retry-safe and never enqueues or executes
work. `GET /intents/<intent_sha>/missions` returns validated linked missions.

Raw Intent MCP access is read-only:

- `list_intents_tool`
- `get_intent_tool`
- `get_intent_lineage_tool`
- `get_intent_missions_tool`
- `diff_intents_tool`

These tools return the same successful payloads as the corresponding HTTP
operations and delegate to the same registry functions. They do not capture,
revise, promote, approve, or retrieve Fluxion, SMI, repository, or chat context.
Browser UI migration remains deferred.

## Raw Intent Intake
Clarity Engine can draft a PCP-lite manifest from one raw human intent without registering or enqueueing it:

```bash
curl -s -X POST http://127.0.0.1:8000/intents/draft \
  -H "Content-Type: application/json" \
  -d '{
    "raw_intent": "I should work on code-server.",
    "context": ["code-server is part of the active dev environment."],
    "constraints": ["Do not change code-server configuration yet."],
    "route": ["SMI", "Clarity Engine", "Infrastructure Registry"]
  }'
```

The intake contract is:
```json
{
  "raw_intent": "I should work on code-server.",
  "context": ["optional known facts"],
  "constraints": ["optional boundaries"],
  "route": ["SMI", "Clarity Engine", "Infrastructure Registry"]
}
```

The response includes `{ ok, errors, warnings, manifest, packet_md, context_sha, registered }`. `registered` is always `false`; send the returned manifest to `/packets/register` only after review.

The browser UI also exposes this flow in the **Intent** tab: write raw intent, add context/constraints/route, draft the mission packet, then register the reviewed draft.

## Constraints
- Deterministic outputs: the same manifest always produces the same `packet_md`, normalized `manifest`, and `context_sha`.
- No outbound network calls. `callback_url` is transport-only data for downstream orchestrators.
- Persistence is filesystem-only under `packets/registry/<sha>/`. No database, no auth.
- Raw Intent persistence is filesystem-only under `packets/intents/<intent_sha>/`.
- Intent-to-mission links are filesystem-only under `packets/links/intent-missions/`.
- Containerized local access uses host port `8010`; host port `8000` is reserved for NGINX Manager.
- Offline CI: tests and packet checks must not require network or secrets.

## Continuous Integration
CI runs on every push and pull request via [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Checks set up Python 3.12, run `pytest`, lint and compose the example manifest, and verify `app.main:app` imports.

## Further Context
- `docs/vision/mission.md` — extended mission and principles
- `docs/vision/architecture.md` — architecture notes and the stage roadmap
- `docs/vision/current_reality.md` — facts-only inventory of what's shipped
- `docs/RAW_INTENT_PACKET.md` — Raw Intent Packet contract and tooling
- `docs/vision/STAGE-0{1,2,3,4,5,6}-MISSION.md` — per-stage plans and gates

## License
Apache License 2.0 (see `LICENSE`).

## Contact
Maintained by **@treksavvy**.

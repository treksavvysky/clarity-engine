# Clarity Engine

Clarity Engine is intent and context infrastructure: it standardizes how we generate clear, testable Context Packets for human–AI and agentic workflows so work stays aligned and auditable.

## Project State
All documented stages (01–06) are shipped:

| Stage | What ships |
|-------|------------|
| 01 | FastAPI HTTP service (`/healthz`, `/packets/compose`, `/packets/lint`, `/openapi.json?server=`) |
| 02 | Schema expansion (risk flags, allowed actions, evidence requirements), ambiguity detection, GPT Actions OpenAPI |
| 03 | Content-addressed filesystem registry; `POST /packets/register`, `GET /packets`, `GET /packets/{sha}`, `POST /packets/diff`, `GET /packets/{sha}/ancestors` |
| 04 | JCT-compatible `POST /packets/enqueue`; optional `callback_url` transport field |
| 05 | MCP server (`python -m app.mcp_server`) exposing compose/lint/register/get/list/diff/enqueue/check_action |
| 06 | Static browser UI at `/` with Browser / Diff / Editor tabs |

See `docs/vision/current_reality.md` for the full fact sheet.

## Authoritative Artifacts
These files define how the project operates and must stay in sync.
- `AGENTS.md` — operating guide and constraints for agents contributing to the repo.
- `CONTEXT_PACKET_TEMPLATE.md` — paste-ready Context Packet template aligned with the schema.
- `pcp_lite.schema.json` — machine-readable contract for packet manifests.
- `packets/examples/context_packet_example.json` — minimal manifest example conforming to the PCP-lite schema.
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
# stdio transport; exposes compose_packet_tool, lint_packet_tool,
# register_packet_tool, get_packet_tool, list_packets_tool,
# diff_packets_tool, enqueue_packet_tool, check_action_tool
```

### CLI tools
```bash
python tools/compose_packet.py packets/examples/context_packet_example.json
python tools/lint_packet.py packets/examples/context_packet_example.json
```

## Constraints
- Deterministic outputs: the same manifest always produces the same `packet_md`, normalized `manifest`, and `context_sha`.
- No outbound network calls. `callback_url` is transport-only data for downstream orchestrators.
- Persistence is filesystem-only under `packets/registry/<sha>/`. No database, no auth.
- Offline CI: tests and packet checks must not require network or secrets.

## Continuous Integration
CI runs on every push and pull request via [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Checks set up Python 3.12, run `pytest`, lint and compose the example manifest, and verify `app.main:app` imports.

## Further Context
- `docs/vision/mission.md` — extended mission and principles
- `docs/vision/architecture.md` — architecture notes and the stage roadmap
- `docs/vision/current_reality.md` — facts-only inventory of what's shipped
- `docs/vision/STAGE-0{1,2,3,4,5,6}-MISSION.md` — per-stage plans and gates

## License
Apache License 2.0 (see `LICENSE`).

## Contact
Maintained by **@treksavvy**.

# GEMINI.md

This file provides guidance to Gemini CLI when working with code in this repository.

## Project Overview

Clarity Engine exists to **reduce the cognitive load between raw human intent and aligned strategic action.** It does not exist to create packets; mission packets are downstream artifacts of clarity, not the definition of clarity itself.

**Current Reality:** Clarity Engine operates as **Clarity Engine Lite**. Going forward, focus strictly on intent salvage and human-first 2.0 design directions, avoiding task-manager drift. All work must align with [docs/vision/current_reality.md](file:///home/architect/cognition/clarity-engine/docs/vision/current_reality.md) and [docs/vision/CLARITY-ENGINE-2.0-DESIGN-DIRECTION.md](file:///home/architect/cognition/clarity-engine/docs/vision/CLARITY-ENGINE-2.0-DESIGN-DIRECTION.md).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload

# Run all tests
pytest -q

# Run a single test
pytest tests/test_app_health.py::test_health_endpoint_returns_ok -v

# Lint a manifest (CLI)
python tools/lint_packet.py packets/examples/context_packet_example.json

# Compose a packet (CLI)
python tools/compose_packet.py packets/examples/context_packet_example.json

# Run in a Docker dev container (bind-mounted source, live reload)
docker compose up -d --build
curl http://localhost:8010/healthz
```

## Architecture

### Dual Interface: CLI Tools + FastAPI

The project provides the same functionality via two interfaces:

1. **CLI Tools** (`tools/`): Deterministic Python scripts for local use
   - `compose_packet.py`: Takes a JSON manifest, emits `packet.md`, `manifest.json`, `context_sha`
   - `lint_packet.py`: Validates manifests against schema, detects vague language and untestable acceptance

2. **FastAPI App** (`app/main.py` v0.2.0): HTTP endpoints that reuse the CLI tool logic
   - `GET /openapi.json?server=<url>` — OpenAPI schema with optional server injection for GPT Actions
   - `GET /docs` — Swagger UI
   - `POST /packets/compose` — returns `{ packet_md, manifest, context_sha }`
   - `POST /packets/lint` — returns `{ ok, errors, warnings }` (warnings don't fail validation)
   - `POST /packets/register` — persists a composed packet in the filesystem registry
   - `GET /packets`, `GET /packets/{sha}`, `GET /packets/{sha}/ancestors` — registry listing, retrieval, and lineage
   - `POST /packets/diff` — compares two manifests or registered packet shas
   - `POST /packets/enqueue` — returns a deterministic JCT-ready task envelope
   - `POST /intents/draft` — returns a deterministic draft PCP-lite manifest from one raw intent without registry writes
   - `GET /healthz` — returns `{ status: "ok" }`
   - `GET /` and `/ui/*` — serve the static browser UI with Browser / Intent / Diff / Editor tabs

The API endpoints import and call functions from `tools/` directly to prevent semantic drift.

3. **MCP Server** (`app/mcp_server.py`): stdio server exposing compose, lint, register, get, list, diff, enqueue, and `check_action` tools.

### Docker Dev Container

`Dockerfile` + `docker-compose.yml` run the FastAPI service in a container for local dev:
- `Dockerfile`: `python:3.12-slim`, installs `requirements.txt`, runs `uvicorn app.main:app --reload` on port 8000.
- `docker-compose.yml`: bind-mounts the whole repo into `/app` so host edits trigger `--reload` live, and publishes the container's 8000 to host port **8010**. `packets/registry/` persists on the host because it's inside the mounted tree — same registry whether the service runs bare-metal or containerized.
- `.dockerignore` excludes `.venv`, `.git`, `__pycache__`, and `packets/registry/` from the build context.
- Not joined to the `codejourney-proxy` network — this service has no public vhost today. Add that network + a proxy entry if it ever needs one.
- The MCP server (`app/mcp_server.py`) is stdio-based and is **not** part of the container; it runs on the host (see `.mcp.json`), same pattern as other repos in this ecosystem.

### Core Contract

- **`pcp_lite.schema.json`**: Project Context Protocol lite (PCP-lite) JSON Schema with required fields + optional fields for risk flags, allowed actions, evidence requirements, packet lineage, and callback transport
- **`CONTEXT_PACKET_TEMPLATE.md`**: Human-readable paste-ready template aligned with schema
- **`AGENTS.md`**: Operating guide defining scope and change rules

### Raw Intent Boundary

Clarity Engine accepts structured PCP-lite manifests for packet operations and exposes `POST /intents/draft` for side-effect-free raw-intent drafting. Raw intent such as `I should work on code-server.` can be submitted as `{ raw_intent, context, constraints, route }`; the endpoint returns a draft manifest plus lint results and preview markdown, but does not register or enqueue the draft.

### Optional Schema Fields

| Field | Type | Purpose |
|-------|------|---------|
| `risk_flags` | enum[] | `high_blast_radius`, `needs_human_signoff`, `missing_info`, `network_required`, `destructive_action`, `secrets_involved`, `external_dependency` |
| `allowed_actions` | enum[] | `git_read`, `git_write`, `filesystem_read`, `filesystem_write`, `http_read`, `http_write`, `docker`, `shell_exec`, `secrets_read`, `database_read`, `database_write` |
| `evidence_requirements` | enum[] | `pr_link`, `commit_sha`, `test_output`, `diff`, `logs`, `screenshot`, `artifact_path`, `api_response` |
| `parent_sha` | string | Links a packet to a registered ancestor for lineage |
| `callback_url` | string | Transport-only callback URL for downstream orchestrators; Clarity Engine never calls it |

### Test Structure

Tests use FastAPI's `TestClient` via the `client` fixture in `conftest.py`. The `example_manifest` fixture loads the golden example from `packets/examples/context_packet_example.json`. Coverage spans CLI compose/lint behavior, ambiguity detection, optional schema fields, registry operations, diffing, lineage, enqueue, MCP parity, and the static UI mount.

## Evolution Policy

Tools and schema may be extended with additive changes following these 2.0 rules:
- **Conversational 5-Question Capture:** UI structures raw intent capture around the 5 questions.
- **4-Step Human-First Output:** Outputs plain-language diagnosis, clarified mission, and ephemeral smallest next move. Detailed packet manifest is secondary background metadata.
- **One-Intent / One-Mission Rule:** A single raw intent maps 1-to-1 with a strategic mission, preventing premature plan decomposition.

## Constraints

- **Decoupled Loops:** Clarity Engine does NOT manage tasks, checklists, or continuous-improvement loops (PDCA/QRCI/Hoshin loops are out-of-scope; handled externally).
- **No Database or Auth:** Persistence is filesystem-only under `packets/registry/<sha>/`. Compose and lint endpoints remain side-effect-free.
- **Deterministic Outputs:** Same input intent compiles to identical outputs.
- **No Network Dependencies:** CI and tests must work offline.
- **Minimal Dependencies:** FastAPI, Uvicorn, pytest, and `mcp` SDK are approved. New deps require a stage-mission note.

## Workflow

- **Commit after each completed task, change, or substage.** Make sure to commit immediately after completing any task or change without waiting for a separate prompt. Use descriptive subject lines (e.g. `Implement Salvage Audit rewrites`) and describe what changed and why in the body. This keeps the history auditable and lets reviewers trace work to its plan in [docs/vision/](file:///home/architect/cognition/clarity-engine/docs/vision/).
- Run the test suite before committing; the suite must be green at every commit on `main`.

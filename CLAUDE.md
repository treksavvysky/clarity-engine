# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clarity Engine provides tools to compose, lint, and emit **Context Packets** — standardized, testable prompts for human–AI and agentic workflows. The project ensures work stays aligned and auditable by producing deterministic, schema-validated packet artifacts.

**Current Stage:** All documented stages (01–06) shipped. HTTP API, MCP server, content-addressed registry, packet diff/lineage, JCT-ready enqueue envelope, and a static browser UI are all in place. See `docs/vision/current_reality.md` for the full inventory.

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
   - `GET /healthz` — returns `{ status: "ok" }`
   - `GET /` and `/ui/*` — serve the static browser UI

The API endpoints import and call functions from `tools/` directly to prevent semantic drift.

3. **MCP Server** (`app/mcp_server.py`): stdio server exposing compose, lint, register, get, list, diff, enqueue, and `check_action` tools.

### Core Contract

- **`pcp_lite.schema.json`**: Project Context Protocol lite (PCP-lite) JSON Schema with required fields + optional fields for risk flags, allowed actions, evidence requirements, packet lineage, and callback transport
- **`CONTEXT_PACKET_TEMPLATE.md`**: Human-readable paste-ready template aligned with schema
- **`AGENTS.md`**: Operating guide defining scope and change rules

### Raw Intent Boundary

Clarity Engine currently accepts structured PCP-lite manifests, not free-form raw intent. Raw intent such as `I should work on code-server.` must first be clarified into a manifest by a human or agent, then passed through lint/compose/register/enqueue. A future additive intake contract may accept `{ raw_intent, context, constraints, route }` and return a draft mission packet.

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

Tools and schema may be extended with additive changes:
- `tools/lint_packet.py` — Add new warnings (no breaking changes to existing validation)
- `tools/compose_packet.py` — Add new rendering (preserve deterministic output)
- `pcp_lite.schema.json` — Add optional fields (required fields need migration)
- `CONTEXT_PACKET_TEMPLATE.md` — Keep aligned with schema

## Constraints

- **No database, auth, or outbound calls**: Persistence is filesystem-only under `packets/registry/<sha>/` (Stage-03+). Compose and lint endpoints remain side-effect-free.
- **Deterministic outputs**: Same manifest input must produce identical outputs
- **No network dependencies**: CI and tests must work offline
- **Minimal dependencies**: FastAPI, Uvicorn, pytest, and the `mcp` SDK (Stage-05+) are approved. New deps require a stage-mission note.

## Workflow

- **Commit after each completed substage or discrete task.** One substage = one commit. Use the Stage-XX.Y label in the subject line (e.g. `Implement Stage-03.2: Packet Diffing`) and describe what changed and why in the body. This keeps the history auditable and lets reviewers trace work to its plan in `docs/vision/`.
- Run the test suite before committing; the suite must be green at every commit on `main`.

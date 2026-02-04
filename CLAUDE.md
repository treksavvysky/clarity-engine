# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clarity Engine provides tools to compose, lint, and emit **Context Packets** — standardized, testable prompts for human–AI and agentic workflows. The project ensures work stays aligned and auditable by producing deterministic, schema-validated packet artifacts.

**Current Stage:** Stage-02 complete — Schema expanded with risk flags, allowed actions, and evidence requirements. Linter includes ambiguity detection. OpenAPI enabled for GPT Actions.

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
   - `GET /healthz` — returns `{ status: "ok" }`

The API endpoints import and call functions from `tools/` directly to prevent semantic drift.

### Core Contract

- **`pcp_lite.schema.json`**: JSON Schema with required fields + optional Stage-02 fields (risk_flags, allowed_actions, evidence_requirements)
- **`CONTEXT_PACKET_TEMPLATE.md`**: Human-readable paste-ready template aligned with schema
- **`AGENTS.md`**: Operating guide defining scope and change rules

### Schema Fields (Stage-02)

| Field | Type | Purpose |
|-------|------|---------|
| `risk_flags` | enum[] | `high_blast_radius`, `needs_human_signoff`, `missing_info`, `network_required`, `destructive_action`, `secrets_involved`, `external_dependency` |
| `allowed_actions` | enum[] | `git_read`, `git_write`, `filesystem_read`, `filesystem_write`, `http_read`, `http_write`, `docker`, `shell_exec`, `secrets_read`, `database_read`, `database_write` |
| `evidence_requirements` | enum[] | `pr_link`, `commit_sha`, `test_output`, `diff`, `logs`, `screenshot`, `artifact_path`, `api_response` |

### Test Structure

Tests use FastAPI's `TestClient` via the `client` fixture in `conftest.py`. The `example_manifest` fixture loads the golden example from `packets/examples/context_packet_example.json`. 15 tests cover endpoints, CLI, ambiguity detection, and Stage-02 fields.

## Evolution Policy

Tools and schema may be extended with additive changes:
- `tools/lint_packet.py` — Add new warnings (no breaking changes to existing validation)
- `tools/compose_packet.py` — Add new rendering (preserve deterministic output)
- `pcp_lite.schema.json` — Add optional fields (required fields need migration)
- `CONTEXT_PACKET_TEMPLATE.md` — Keep aligned with schema

## Constraints

- **Stateless runtime**: No authentication, persistence, or outbound calls
- **Deterministic outputs**: Same manifest input must produce identical outputs
- **No network dependencies**: CI and tests must work offline
- **Minimal dependencies**: Only FastAPI + Uvicorn + pytest are approved

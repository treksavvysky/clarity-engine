# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clarity Engine provides tools to compose, lint, and emit **Context Packets** — standardized, testable prompts for human–AI and agentic workflows. The project ensures work stays aligned and auditable by producing deterministic, schema-validated packet artifacts.

**Current Stage:** Stage-01.3 — Stage-0 artifacts (template, schema, CLI tools) are frozen. The FastAPI boundary exposes `/healthz`, `/packets/compose`, and `/packets/lint`.

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
   - `lint_packet.py`: Validates manifests against `pcp_lite.schema.json`

2. **FastAPI App** (`app/main.py`): HTTP endpoints that reuse the CLI tool logic
   - `POST /packets/compose` — returns `{ packet_md, manifest, context_sha }`
   - `POST /packets/lint` — returns `{ ok: bool, issues: [] }`
   - `GET /healthz` — returns `{ status: "ok" }`

The API endpoints import and call functions from `tools/` directly to prevent semantic drift between CLI and HTTP behavior.

### Core Contract

- **`pcp_lite.schema.json`**: JSON Schema defining required/optional fields for Context Packet manifests
- **`CONTEXT_PACKET_TEMPLATE.md`**: Human-readable paste-ready template for drafting packets
- **`AGENTS.md`**: Operating guide defining scope, frozen artifacts, and change rules

### Test Structure

Tests use FastAPI's `TestClient` via the `client` fixture in `conftest.py`. The `example_manifest` fixture loads the golden example from `packets/examples/context_packet_example.json`.

## Stage-0 Frozen Artifacts

These files must not change without explicit request:
- `CONTEXT_PACKET_TEMPLATE.md`
- `pcp_lite.schema.json`
- `tools/compose_packet.py`
- `tools/lint_packet.py`

## Constraints

- **Stateless runtime**: No authentication, persistence, or outbound calls
- **Deterministic outputs**: Same manifest input must produce identical outputs
- **No network dependencies**: CI and tests must work offline
- **Minimal dependencies**: Only FastAPI + Uvicorn + pytest are approved

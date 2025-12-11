# Stage-01 Mission — HTTP Context Service (FastAPI)

## Mission
Expose Clarity Engine’s existing Context Packet **composition** and **linting** capabilities as a minimal, **stateless local HTTP service** using **FastAPI**, without changing any underlying packet contract, semantics, determinism, or existing CLI tool behavior.

## Intent
Stage-01 adds a thin HTTP transport layer so other tools and agents can invoke the same deterministic compiler/linter logic programmatically, while Clarity Engine remains an **intent/context compiler** (not a workflow runner).

## Invariants (Must Remain True)
- **Determinism:** the same manifest must produce identical `packet_md`, normalized `manifest`, and `context_sha`.
- **Contract-first:** no drift in the packet contract.
- **No semantic changes:** existing composition and lint rules remain exactly as defined in Stage-0.
- **CLI stability:** `tools/compose_packet.py` and `tools/lint_packet.py` must continue to work exactly as in Stage-0.

## Constraints (Stage-01)
- Must not modify:
  - `CONTEXT_PACKET_TEMPLATE.md`
  - `pcp_lite.schema.json`
- Must not break or change behavior of:
  - `tools/compose_packet.py`
  - `tools/lint_packet.py`
- Must not introduce:
  - Authentication
  - Databases or persistence
  - MCP server
  - UI
  - Network calls or secret handling
- Service must remain **stateless**.
- **FastAPI** is the only new runtime framework allowed.

## Stage-01 Scope (What We Add)
A minimal FastAPI app under `app/` that exposes:
- `GET /healthz`
- `POST /packets/compose`
- `POST /packets/lint`

These endpoints must call the **same logic** used by the existing CLI tools.

## Definition of Done (Acceptance)
- `uvicorn app.main:app --reload` starts the service locally.
- `GET /healthz` returns `{ "status": "ok" }`.
- `POST /packets/compose` with the example manifest returns:
  - `packet_md`
  - normalized `manifest`
  - `context_sha`
- `POST /packets/lint` returns:
  - `ok: true` for a valid input
  - `ok: false` with issues for an invalid input
- Existing CLI tools still work exactly as in Stage-0.
- CI remains green.

## Failure Modes
Stage-01 fails if any of the following occur:
- FastAPI app fails to start locally.
- Any regression in CLI behavior.
- Any schema/template drift.
- Any non-deterministic outputs introduced.

## Non-Goals
- No MCP integration.
- No packet storage.
- No UI.
- No orchestration.
- No agent runtime.

## Substage Gate
Proceed only with **Stage-01** (HTTP Context Service). No further orchestration layers until Stage-01 is explicitly complete and verified.

# Stage-01 Substages — Table of Contents

Stage-01 is implemented as small, gated substages. Each substage must pass its acceptance checks before proceeding.

## 01.1 — FastAPI Bootstrap + Health Check
**Objective:** Add `app/main.py` with a minimal FastAPI app and `GET /healthz` returning `{ "status": "ok" }`.  
**Gate:** `uvicorn app.main:app --reload` starts locally; `/healthz` responds correctly; CI can import the app.

## 01.2 — Compose Endpoint (`POST /packets/compose`)
**Objective:** Expose packet composition via HTTP by calling the same compose logic used by the Stage-0 CLI tool(s), returning `packet_md`, normalized `manifest`, and `context_sha`.  
**Gate:** Compose output for the example manifest matches the CLI tool output (no semantic drift, deterministic).

## 01.3 — Lint Endpoint (`POST /packets/lint`)
**Objective:** Expose packet linting via HTTP by calling the same lint logic used by the Stage-0 CLI tool(s), returning `ok` and `issues`.  
**Gate:** Valid example returns `ok: true`; invalid input returns `ok: false` with issues; no CLI regressions.

## 01.4 — Minimal Tests + CI Smoke Checks
**Objective:** Add minimal automated verification for the FastAPI layer (import/health + one golden example path).  
**Gate:** CI remains green; tests are deterministic and do not require network, secrets, or external services.

## 01.5 — Docs & Runbook Updates
**Objective:** Document how to run the HTTP service locally and clarify Stage-01 boundaries (no auth, no persistence, no orchestration).  
**Gate:** Docs reflect actual usage; no changes to Stage-0 contract artifacts.

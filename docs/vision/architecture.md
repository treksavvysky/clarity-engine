# Clarity Engine Architecture

> Stages 01–06 are shipped. Sections below describe the architecture as it exists today; the roadmap further down records the historical staging plan. See `docs/vision/current_reality.md` for the facts-only inventory.

## Overview
Clarity Engine is a contract-driven pipeline that turns missions into reliable Context Packets and exposes them through HTTP, MCP, and browser interfaces.

## Components (Shipped)
- **Packet toolchain (CLI):** `tools/compose_packet.py` and `tools/lint_packet.py` produce `packet.md`, normalized manifests, and `context_sha` deterministically from `pcp_lite.schema.json`.
- **Content-addressed registry:** `app/registry.py` writes `packets/registry/<sha>/{manifest.json,packet.md}` (Stage-03). Overridable via `CLARITY_REGISTRY_ROOT`. Idempotent, append-only at the API surface.
- **Backend runtime (FastAPI):** `app/main.py` serves `/healthz`, `/openapi.json` (with `?server=` injection), `/packets/compose`, `/packets/lint`, `/packets/register`, `/packets/{sha}`, `/packets/{sha}/ancestors`, `/packets`, `/packets/diff`, `/packets/enqueue`, and mounts the static UI at `/` and `/ui/*`. Packet validation uses JSON Schema (not Pydantic) via `tools/lint_packet.py` so CLI and HTTP share the same rules.
- **MCP server:** `app/mcp_server.py` exposes compose, lint, register, get, list, diff, enqueue, and `check_action` as MCP tools over stdio (`python -m app.mcp_server`). All tools delegate to the same modules the HTTP endpoints use.
- **Agentic workflow ties (JCT):** `POST /packets/enqueue` returns a JCT-ready envelope with `task_id === context_sha` and the optional `callback_url` transport field (Clarity Engine never calls it).
- **UI:** `ui/index.html` is a single static page with Browser / Diff / Editor tabs, served by FastAPI. No Node toolchain. A Next.js replacement remains the long-term aspiration and can swap in without backend changes.

## Operating Model
1. Incoming manifests are validated against `pcp_lite.schema.json`.
2. Compose normalizes the manifest and computes a `context_sha` over the canonical JSON.
3. Register (or enqueue) persists `manifest.json` + `packet.md` under `packets/registry/<sha>/` — idempotent on re-register.
4. Agents consume packets over HTTP or MCP; `check_action` gates proposed actions against `allowed_actions`.
5. The UI reads and writes via the same HTTP endpoints.

---

## Future Stages Roadmap

### Stage-02 — Enhanced Linting & Schema Expansion
**Theme:** Make packets smarter and safer before they leave the compiler.

- **02.1 — Ambiguity Detection**
  Add heuristic linting to flag vague language ("maybe", "should", "try to", "if possible") in acceptance criteria and constraints. Warn when acceptance entries lack testable verbs or observable outcomes.

- **02.2 — Risk Flags Field**
  Extend `pcp_lite.schema.json` with a `risk_flags` array (`high_blast_radius`, `needs_human_signoff`, `missing_info`, `network_required`). Linter can auto-populate some flags based on other fields.

- **02.3 — Allowed Actions Field**
  Add `allowed_actions` to schema (e.g., `["git_read", "git_write", "http_read", "docker", "filesystem_write"]`) so downstream agents can validate permissions before acting.

- **02.4 — Evidence Requirements Field**
  Add `evidence_requirements` to schema (e.g., `["pr_link", "test_output", "diff", "logs"]`) to define what proof of work agents must return.

- **02.5 — OpenAPI / Custom GPT Actions**
  Enable `/docs` and `/openapi.json` endpoints (currently disabled). Add rich operation summaries and descriptions optimized for GPT action discovery. Document hosted instance URL for GPT action configuration in custom GPTs.

### Stage-03 — Registry & Packet Operations
**Theme:** Packets become addressable, comparable, and retrievable.

- **03.1 — Packet Registry**
  Implement `packets/` as a content-addressed store keyed by `context_sha`. Endpoints: `GET /packets/{sha}`, `GET /packets` (list).

- **03.2 — Packet Diffing**
  `POST /packets/diff` endpoint to compare two manifests and highlight changes—useful for iterating on intent before execution.

- **03.3 — Packet Versioning**
  Track packet lineage: which packet was derived from which, enabling audit trails.

### Stage-04 — JCT Integration
**Theme:** Packets become executable work units in the orchestration layer.

- **04.1 — Enqueue Shape**
  `POST /packets/enqueue` returns a structure compatible with JCT's `/tasks/enqueue`, including `task_id` derived from `context_sha`.

- **04.2 — Status Callback Hook**
  Optional webhook/callback field in packets for JCT to notify Clarity Engine of execution status.

### Stage-05 — MCP Server
**Theme:** Agents can compose and lint packets natively.

- **05.1 — MCP Tool Exposure**
  Expose `compose_packet` and `lint_packet` as MCP tools for connected agents.

- **05.2 — Agent Permissions Enforcement**
  MCP layer validates agent actions against packet's `allowed_actions` before execution.

### Stage-06 — UI
**Theme:** Human-readable access for browsing, comparing, and reviewing packets.

- **06.1 — Packet Browser**
  List and search packets by project, stage, or hash.

- **06.2 — Diff Viewer**
  Side-by-side comparison of packet versions.

- **06.3 — Manifest Editor**
  Form-based editor with live validation against schema.

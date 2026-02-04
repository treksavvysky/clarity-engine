# Clarity Engine Architecture (Planned)

## Overview
The future architecture centers on a contract-driven pipeline that turns missions into reliable Context Packets and exposes them through agent-friendly interfaces.

## Planned Components
- **Packet toolchain (CLI + services):** Deterministic compose and lint flows that read the shared template and `pcp_lite.schema.json`, producing `packet.md` and normalized manifests by content hash.
- **Context packet registry:** A hashed store under `packets/` that keeps packet markdown and manifests aligned for reproducibility and audit.
- **Backend runtime (FastAPI + MCP server):**
  - FastAPI endpoints to serve packet metadata and retrieval by hash.
  - MCP server surfaces packet composition/linting actions to connected agents.
  - Pydantic models enforce schema compatibility across services.
- **Agentic workflow ties (JCT and peers):** Packets are structured so orchestrators can compose tool calls, enforce constraints, and log decisions without rehydrating full project histories.
- **UI (Next.js-style):** A lightweight React/Next.js front layer for browsing packets, comparing versions, and previewing manifests.

## Operating Model
1. Incoming missions are normalized into manifests that satisfy `pcp_lite.schema.json`.
2. Compose/lint services generate markdown packets and validated manifests, computing a `context_sha` for registry lookups.
3. The MCP server exposes these operations to agents, while FastAPI endpoints provide human-readable access.
4. UI fetches packet metadata and renders packet content for comparison, review, and sharing.

## Stage 0 Note
This architecture is aspirational. Stage 0 only ships documentation, schema, and templates—no FastAPI services, MCP server, registry, or UI are implemented yet.

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

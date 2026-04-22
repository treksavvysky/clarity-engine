# Stage-05 Mission — MCP Server

## Mission
Expose Clarity Engine's deterministic packet operations as **Model Context Protocol (MCP) tools** so connected agents can compose, lint, register, diff, enqueue, and permission-check Context Packets natively — without going through HTTP.

## Intent
Stage-01..04 made packets HTTP-addressable. Stage-05 removes the HTTP hop for agent workflows by surfacing the same logic over stdio MCP. All tool handlers call the **same functions** the FastAPI endpoints use, preserving determinism and parity. No semantic drift.

## Invariants (Must Remain True)
- **Single source of truth for logic:** MCP tools call `tools/compose_packet.py`, `tools/lint_packet.py`, and `app/registry.py` directly. No reimplementation.
- **Determinism:** Identical inputs through MCP yield identical outputs, matching the HTTP endpoints byte-for-byte.
- **No outbound network calls.** MCP transport is stdio.
- **FastAPI app unchanged** in behavior.

## Constraints (Stage-05)
- MCP SDK (`mcp`) is the only new runtime dependency.
- MCP server is a separate entry point (`python -m app.mcp_server`); it does not import or embed the FastAPI app.
- Registry root is controlled by `CLARITY_REGISTRY_ROOT` env var (same as HTTP).
- No tool may fire outbound requests, call `callback_url`, or mutate anything outside `packets/registry/`.

## Stage-05 Scope (What We Add)
- `app/mcp_server.py` — stdio MCP server exposing:
  - `compose_packet` — manifest → `{packet_md, manifest, context_sha}`
  - `lint_packet` — manifest → `{ok, errors, warnings}`
  - `register_packet` — compose + persist (idempotent)
  - `get_packet` — sha → stored manifest + md, or error if unknown
  - `list_packets` — returns registered `{context_sha, mission}` entries
  - `diff_packets` — two manifests (or shas) → `{added, removed, changed}`
  - `enqueue_packet` — JCT envelope
  - `check_action` — `(context_sha, action)` → `{allowed, reason}` based on the packet's `allowed_actions`
- Thin tool handlers live in `app/mcp_server.py`; business logic stays in existing modules.

## Definition of Done (Acceptance)
- `python -m app.mcp_server` starts an MCP stdio server exposing all tools.
- Each MCP tool returns output that matches its HTTP counterpart for the golden manifest.
- `check_action` returns `allowed: true` for an action listed in the packet's `allowed_actions`, `false` otherwise, and `allowed: false, reason: "unknown_packet"` for an unregistered sha.
- All HTTP tests still pass; new unit tests exercise the tool handlers directly.
- `requirements.txt` pins `mcp`.

## Failure Modes
Stage-05 fails if any of the following occur:
- MCP tool outputs drift from HTTP outputs for the same input.
- Tool handlers duplicate logic instead of delegating.
- Server makes outbound network calls.
- Adding the MCP layer breaks the FastAPI app.

## Non-Goals
- No UI (Stage-06).
- No execution of agent actions — only permission checks.
- No persistent MCP session state beyond the registry.

## Substage Gate
Proceed only with Stage-05 until verified.

---

# Stage-05 Substages

## 05.1 — MCP Tool Exposure
**Objective:** Expose compose/lint/register/get/list/diff/enqueue as MCP tools that delegate to existing modules.
**Gate:** Each tool's output matches the HTTP endpoint for the golden manifest.

## 05.2 — Agent Permissions Enforcement
**Objective:** Add a `check_action(context_sha, action)` MCP tool that resolves the registered packet and answers whether the action is in `allowed_actions`.
**Gate:** Returns `allowed: true` for a permitted action, `false` with reason for an unpermitted one, and `allowed: false, reason: "unknown_packet"` for an unknown sha.

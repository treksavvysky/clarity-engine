# Stage-04 Mission — JCT Integration

## Mission
Make Context Packets **enqueueable as work units** by exposing a JCT-compatible enqueue shape and a transport-only callback field, without Clarity Engine itself acquiring runtime, orchestration, or outbound-network responsibilities.

## Intent
Stage-03 made packets addressable. Stage-04 makes them **executable hand-offs**: a single HTTP call returns everything a JCT-like orchestrator needs to queue a task — a stable `task_id`, the manifest, the rendered packet, declared permissions, and evidence expectations. Clarity Engine still does not execute or poll anything.

## Invariants (Must Remain True)
- **Determinism:** enqueue output depends only on the manifest. No timestamps, no random ids.
- **No outbound network calls** from Clarity Engine itself. `callback_url` is transport data for a downstream system.
- **Compose/lint/register/diff/ancestors** remain untouched in behavior.
- **task_id = context_sha.** No separate id space.

## Constraints (Stage-04)
- Enqueue endpoint is **compose-equivalent + registry-write**, not a new execution path.
- `callback_url` is an **optional, stored-only** field. Clarity Engine never hits it.
- No polling, webhooks, or status-update endpoints in Stage-04.
- No new runtime dependencies.

## Stage-04 Scope (What We Add)
- `POST /packets/enqueue` — composes, registers (idempotent), and returns a JCT-ready envelope.
- Optional `callback_url` field in `pcp_lite.schema.json` (URL pattern, validated by linter).

## JCT Envelope Shape
```json
{
  "task_id": "<context_sha>",
  "context_sha": "<context_sha>",
  "mission": "<from manifest>",
  "manifest": { ... },
  "packet_md": "...",
  "allowed_actions": [...],
  "evidence_requirements": [...],
  "risk_flags": [...],
  "callback_url": "https://..." | null,
  "registered": true | false
}
```

## Definition of Done (Acceptance)
- `POST /packets/enqueue` with the example manifest returns `task_id === context_sha` and a complete envelope.
- Calling enqueue twice with the same manifest returns `registered: false` on the second call; `task_id` is identical.
- `callback_url` in the manifest round-trips through compose, register, and enqueue.
- A non-URL `callback_url` is rejected by the linter.
- All prior tests still pass; new tests cover enqueue shape, idempotency, and callback validation.

## Failure Modes
Stage-04 fails if any of the following occur:
- Enqueue output varies between calls for the same manifest (non-determinism).
- Clarity Engine issues any outbound request on enqueue.
- `task_id` diverges from `context_sha`.

## Non-Goals
- No MCP server (Stage-05).
- No UI (Stage-06).
- No status callbacks fired by Clarity Engine.
- No task lifecycle state machine.

## Substage Gate
Proceed only with Stage-04 until verified.

---

# Stage-04 Substages

## 04.1 — Enqueue Shape
**Objective:** `POST /packets/enqueue` returns a deterministic JCT envelope with `task_id = context_sha`, and persists to the registry (idempotent).
**Gate:** Envelope matches schema; task_id equals context_sha; second call is a no-op.

## 04.2 — Callback URL Field
**Objective:** Add optional `callback_url` to the schema. Linter validates URL shape. Enqueue envelope includes it (or `null`).
**Gate:** Non-URL values fail lint; valid URLs round-trip; packets without callback serialize with `callback_url: null`.

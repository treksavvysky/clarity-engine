# Stage-02 Mission — Enhanced Linting & Schema Expansion

> Backfilled retrospectively. Stage-02 was shipped across commits `d5fa405` (02.1), `5dbf702` (02.2/02.3/02.4), and `18ab9f5`/`3b63b7b`/`c59785e` (02.5). This document records the intent and gates those commits satisfied.

## Mission
Make Context Packets **smarter and safer** before they leave the compiler by detecting ambiguity in content, expanding the schema with risk/permission/evidence metadata, and exposing the API for import into custom GPTs.

## Intent
Stage-01 made compose and lint reachable over HTTP. Stage-02 raises the quality bar of what flows through those endpoints. The schema gains additive optional fields that downstream systems (JCT, MCP agents) will need in later stages, and the linter gains heuristic warnings that flag vague or untestable language without blocking valid work.

## Invariants (Must Remain True)
- **Determinism:** composition output is still deterministic.
- **Additive schema changes only:** every new field is optional; existing manifests still validate.
- **Warnings are non-blocking:** the linter's `ok` flag only flips on errors, not warnings.
- **CLI parity:** `tools/*` behavior remains consistent with HTTP endpoint behavior.

## Constraints (Stage-02)
- No new runtime dependencies.
- No persistence, auth, or outbound network calls.
- Schema changes must preserve the existing required list.
- `/docs` and `/openapi.json` are the only new endpoints; no new packet endpoints in 02.x.

## Stage-02 Scope (What Was Added)
- Ambiguity detection in the linter (`tools/lint_packet.py`).
- Three additive schema fields: `risk_flags`, `allowed_actions`, `evidence_requirements`.
- OpenAPI surface optimized for GPT Action discovery, with a `?server=<url>` injection on `/openapi.json`.

## Definition of Done (Acceptance)
- Linter flags vague language (`maybe`, `should`, `try to`, …) and untestable acceptance entries as `[warning]` issues that do not fail validation.
- Schema accepts valid values in `risk_flags`, `allowed_actions`, `evidence_requirements` and rejects out-of-enum values.
- `compose_packet.py` renders all new sections in the generated packet markdown.
- `/docs` (Swagger UI) and `/openapi.json` are live; `/openapi.json?server=<url>` injects a `servers` entry.
- Example manifest continues to round-trip through compose/lint with `ok: true`.
- All prior tests still pass; new tests cover ambiguity, schema enums, and the OpenAPI server injection.

## Failure Modes (Would Have Failed 02)
- A warning flipping the linter to `ok: false`.
- A required field added to the schema.
- A non-deterministic rendering of the new sections.
- Network-dependent test coverage.

## Non-Goals
- No registry or packet persistence (Stage-03).
- No MCP server (Stage-05).
- No UI (Stage-06).

---

# Stage-02 Substages — Status

## 02.1 — Ambiguity Detection ✓
Linter flags vague language in `mission`, `acceptance`, `constraints`, `required_artifacts`; warns when acceptance entries lack action verbs. Warnings are prefixed `[warning]` and do not cause failure.

## 02.2 — Risk Flags Field ✓
Optional `risk_flags` array added to `pcp_lite.schema.json` with enum: `high_blast_radius`, `needs_human_signoff`, `missing_info`, `network_required`, `destructive_action`, `secrets_involved`, `external_dependency`.

## 02.3 — Allowed Actions Field ✓
Optional `allowed_actions` array added with enum: `git_read`, `git_write`, `filesystem_read`, `filesystem_write`, `http_read`, `http_write`, `docker`, `shell_exec`, `secrets_read`, `database_read`, `database_write`.

## 02.4 — Evidence Requirements Field ✓
Optional `evidence_requirements` array added with enum: `pr_link`, `commit_sha`, `test_output`, `diff`, `logs`, `screenshot`, `artifact_path`, `api_response`.

## 02.5 — OpenAPI / Custom GPT Actions ✓
`/docs` (Swagger UI) and `/openapi.json` enabled. Custom `/openapi.json?server=<url>` injects the `servers` field so custom GPTs can import the spec pointed at any hosted instance. App version bumped to 0.2.0.

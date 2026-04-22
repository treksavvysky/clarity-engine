# Current Reality (Facts Only) — Stage-04 Complete

## Repository / Contract Baseline
- Core artifacts have evolved through Stage-02:
  - `CONTEXT_PACKET_TEMPLATE.md` — Updated with risk_flags, allowed_actions, evidence_requirements sections
  - `pcp_lite.schema.json` — Extended with Stage-02 optional fields
  - `tools/compose_packet.py` — Renders all schema fields including Stage-02 additions
  - `tools/lint_packet.py` — Includes ambiguity detection (vague language, untestable acceptance)

## API Implementation State
- A FastAPI application at `app/main.py` (v0.2.0) exposes:
  - `GET /healthz` returning `{ "status": "ok" }`.
  - `GET /openapi.json` with optional `?server=<url>` for GPT Action imports.
  - `POST /packets/compose` returning `{ packet_md, manifest, context_sha }`.
  - `POST /packets/lint` returning `{ ok, errors, warnings }` — warnings don't fail validation.
- OpenAPI docs available at `/docs` (Swagger UI).
- 15 tests cover endpoints, CLI tools, ambiguity detection, and Stage-02 fields.

## Dependency / Runtime Reality
- A `requirements.txt` exists for the HTTP service dependencies and includes FastAPI, Uvicorn, and Pytest.
- Installing dependencies from `requirements.txt` succeeds in the development environment.

## Verified Execution (Observed)
- The service starts successfully via `uvicorn app.main:app --reload`.
- A request to `/healthz` returns `{ "status": "ok" }` (HTTP 200).
- `POST /packets/compose` returns deterministic `packet_md`, normalized `manifest`, and `context_sha` using Stage-0 compose functions for the example manifest.
- `POST /packets/lint` returns `{ "ok": true, "issues": [] }` for the example manifest and reports missing required fields when omitted.
- `pytest -q` runs the minimal endpoint tests in-process with FastAPI's `TestClient`.

## CI / Tests
- CI continues to run Python 3.12 and the Stage-0 packet checks.
- CI includes an import smoke check to ensure `app.main` loads without side effects.
- CI runs `pytest -q` for the minimal FastAPI endpoint coverage alongside Stage-0 packet tooling checks.

## Service Properties
- The service remains stateless: no persistence, authentication, outbound network calls, or UI components are present.

## Stage-01.5 Documentation State
- `CLAUDE.md` added at repository root with project guidance for Claude Code (commands, architecture, constraints).
- `docs/DESCRIPTION.md` added explaining the "intent → execution packet" vision and architectural positioning.
- `docs/vision/architecture.md` updated with Future Stages Roadmap (Stages 02–06).
- README.md already reflects Stage-01.3 usage and endpoints.

## Stage-01 Completion
All Stage-01 substages (01.1–01.5) are complete.

## Stage-02.5 OpenAPI / Custom GPT Actions
- OpenAPI documentation enabled at `/docs` (Swagger UI) and `/openapi.json`.
- App description optimized for GPT action discovery: "Intent-to-packet compiler for AI agents."
- Endpoints tagged (`packets`, `health`) with rich summaries and descriptions.
- Version bumped to 0.2.0.
- Custom `/openapi.json` endpoint accepts `?server=<url>` query param to inject the `servers` field for GPT Action imports (e.g., `/openapi.json?server=https://your-host.com`).

## Stage-02.1 Ambiguity Detection
- Linter extended with vague language detection (flags: "maybe", "should", "try to", "if possible", etc.).
- Linter detects untestable acceptance criteria (entries lacking action verbs like "returns", "creates", "passes").
- Warnings are prefixed with `[warning]` and do not cause lint failure.
- API response structure updated: `{ ok, errors, warnings }` — `ok` is true if no errors (warnings allowed).
- CLI prints warnings but exits 0 if no errors.

## Stage-02.2 Risk Flags Field
- Schema extended with optional `risk_flags` array.
- Valid values: `high_blast_radius`, `needs_human_signoff`, `missing_info`, `network_required`, `destructive_action`, `secrets_involved`, `external_dependency`.
- Template and compose tool updated to render Risk Flags section.

## Stage-02.3 Allowed Actions Field
- Schema extended with optional `allowed_actions` array.
- Valid values: `git_read`, `git_write`, `filesystem_read`, `filesystem_write`, `http_read`, `http_write`, `docker`, `shell_exec`, `secrets_read`, `database_read`, `database_write`.
- Enables downstream agents to validate permissions before acting.

## Stage-02.4 Evidence Requirements Field
- Schema extended with optional `evidence_requirements` array.
- Valid values: `pr_link`, `commit_sha`, `test_output`, `diff`, `logs`, `screenshot`, `artifact_path`, `api_response`.
- Defines proof-of-work agents must return to verify completion.

## Stage-02 Completion
All Stage-02 substages (02.1–02.5) are complete.

## Stage-03.1 Packet Registry
- `app/registry.py` provides a filesystem-backed content-addressed store under `packets/registry/<sha>/` (overridable via `CLARITY_REGISTRY_ROOT`).
- `POST /packets/register` composes and persists; idempotent (second call returns `registered: false`).
- `GET /packets` lists `{context_sha, mission}` entries; `GET /packets/{sha}` returns stored manifest + markdown or 404.
- Compose/lint endpoints remain side-effect-free.

## Stage-03.2 Packet Diffing
- `POST /packets/diff` accepts `left` and `right`, each either a `context_sha` string or an inline manifest object.
- Returns `{added, removed, changed}` — only fields that differ; unchanged fields are omitted.
- Unknown sha returns 404; missing sides return 400.

## Stage-03.3 Packet Versioning
- Optional `parent_sha` field added to schema (pattern `^[a-f0-9]{64}$`).
- Linter honors string `pattern` constraints.
- Compose renders a `Parent SHA:` line in the markdown header when present.
- `GET /packets/{sha}/ancestors` walks the lineage chain and returns ancestors ordered nearest → oldest.

## Stage-03 Completion
All Stage-03 substages (03.1–03.3) are complete.

## Stage-04.1 Enqueue Shape
- `POST /packets/enqueue` composes + registers + returns a JCT-ready envelope.
- `task_id === context_sha` (no separate id space).
- Idempotent: second call returns `registered: false`; envelope is deterministic.

## Stage-04.2 Callback URL Field
- Optional `callback_url` added to schema (`^https?://[^\s]+$`).
- Linter rejects non-URL values.
- Clarity Engine never calls the URL; it is transport-only data for downstream orchestrators.

## Stage-04 Completion
All Stage-04 substages (04.1–04.2) are complete. Test count: 37. Ready to proceed to Stage-05 (MCP Server).

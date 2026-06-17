# Current Reality (Facts Only) — Stage-06 Complete (All Stages Shipped)

## Repository / Contract Baseline
- Core artifacts have evolved through Stage-06:
  - `CONTEXT_PACKET_TEMPLATE.md` — Updated with risk_flags, allowed_actions, evidence_requirements sections
  - `pcp_lite.schema.json` — Extended with optional fields for risk flags, allowed actions, evidence requirements, packet lineage, and callback transport
  - `tools/compose_packet.py` — Renders all schema fields including the shipped optional fields
  - `tools/lint_packet.py` — Includes ambiguity detection (vague language, untestable acceptance)

## API Implementation State
- A FastAPI application at `app/main.py` (v0.2.0) exposes:
  - `GET /healthz` returning `{ "status": "ok" }`.
  - `GET /openapi.json` with optional `?server=<url>` for GPT Action imports.
  - `POST /packets/compose` returning `{ packet_md, manifest, context_sha }`.
  - `POST /packets/lint` returning `{ ok, errors, warnings }` — warnings don't fail validation.
  - `POST /packets/register`, `GET /packets`, `GET /packets/{sha}`, and `GET /packets/{sha}/ancestors` for registry and lineage operations.
  - `POST /packets/diff` for manifest or registered-packet comparison.
  - `POST /packets/enqueue` for deterministic JCT-ready task envelopes.
  - `GET /` and `/ui/*` for the static browser UI.
- OpenAPI docs available at `/docs` (Swagger UI).
- Tests cover endpoints, CLI tools, ambiguity detection, optional schema fields, registry operations, diffing, lineage, enqueue, MCP parity, and UI serving. Current Stage-06 completion test count: 50.

## Dependency / Runtime Reality
- A `requirements.txt` exists for the HTTP service dependencies and includes FastAPI, Uvicorn, and Pytest.
- Installing dependencies from `requirements.txt` succeeds in the development environment.

## Verified Execution (Observed)
- The service starts successfully via `uvicorn app.main:app --reload`.
- A request to `/healthz` returns `{ "status": "ok" }` (HTTP 200).
- `POST /packets/compose` returns deterministic `packet_md`, normalized `manifest`, and `context_sha` for the example manifest.
- `POST /packets/lint` returns `{ "ok": true, "errors": [], "warnings": [] }` for the example manifest and reports missing required fields when omitted.
- `pytest -q` runs the endpoint, CLI, MCP, registry, diff, lineage, enqueue, and UI tests in-process.

## CI / Tests
- CI runs Python 3.12 and the packet checks.
- CI includes an import smoke check to ensure `app.main` loads without side effects.
- CI runs `pytest -q`, lints the example manifest, and composes the example manifest.

## Service Properties
- Persistence is filesystem-only under `packets/registry/<sha>/`, with no database.
- Compose and lint endpoints are side-effect-free; register and enqueue write to the registry.
- No authentication, secrets handling, or outbound network calls are present.
- The browser UI is a static `ui/index.html` file mounted by FastAPI.

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
All Stage-04 substages (04.1–04.2) are complete.

## Stage-05.1 MCP Tool Exposure
- `app/mcp_server.py` exposes eight MCP tools over stdio: `compose_packet_tool`, `lint_packet_tool`, `register_packet_tool`, `get_packet_tool`, `list_packets_tool`, `diff_packets_tool`, `enqueue_packet_tool`, `check_action_tool`.
- All tool handlers delegate to existing modules (`tools/compose_packet.py`, `tools/lint_packet.py`, `app/registry.py`) — no logic duplication.
- Tool outputs match HTTP endpoint outputs for the golden manifest (parity verified in tests).
- Entry point: `python -m app.mcp_server`.

## Stage-05.2 Agent Permissions Enforcement
- `check_action_tool` resolves a registered packet and returns `{allowed, reason}` for a proposed action.
- Reasons: `permitted`, `not_in_allowed_actions`, `unknown_packet`.

## Stage-05 Dependencies
- `mcp==1.27.0` added to `requirements.txt`.
- FastAPI upgraded to 0.136.0, Uvicorn to 0.45.0 for starlette 1.0 compatibility.

## Stage-05 Completion
All Stage-05 substages (05.1–05.2) are complete.

## Stage-06.1 Packet Browser UI
- `GET /` serves `ui/index.html`; `/ui/*` mounted as static assets.
- Browser tab lists packets from `GET /packets` and shows manifest + markdown detail.
- No Node/npm toolchain; single static HTML file.

## Stage-06.2 Diff Viewer UI
- Diff tab accepts two sides, each either a 64-char sha or an inline JSON manifest.
- Calls `POST /packets/diff`; renders added/removed/changed in color-coded sections.

## Stage-06.3 Manifest Editor UI
- Editor tab has a JSON textarea with Lint / Compose / Register / Enqueue buttons.
- Includes a "Load example" helper; refreshes the Browser list after Register/Enqueue.

## Stage-06 Completion
All Stage-06 substages (06.1–06.3) are complete. Test count: 50. A Next.js/React frontend remains the architectural aspiration; `ui/index.html` is the concrete Stage-06 deliverable and can be replaced without backend changes.

## Project State
All documented stages (01–06) are shipped. The service exposes HTTP, MCP, and browser access to the same deterministic packet operations. Further work is additive (new fields, new tools) or a platform swap (Next.js UI, database registry) that would warrant a new stage plan.

## Raw Intent Intake Boundary
Clarity Engine currently accepts structured Project Context Protocol lite (PCP-lite) manifests. Raw human intent is clarified into a manifest by a human or agent before lint, compose, register, or enqueue. A future additive stage may introduce an explicit raw-intent intake contract such as `{ raw_intent, context, constraints, route }` that returns a draft mission packet.

# AGENTS.md — Operating Guide for Codex

This file defines how Codex should work on the **clarity-engine** repo.

The goal is to keep changes **small, testable, and reversible**, while maintaining the core context-engineering artifacts that humans and other agents rely on.

---

## 1. Mission

Clarity Engine provides tools to compose, lint, and emit **Context Packets** for human–AI workflows.

Codex’s mission in this repo:

> Implement and maintain small, incremental changes that improve the ability to generate clear, consistent, and testable Context Packets—without breaking existing behavior or contracts.

See `docs/vision/mission.md` for the extended mission statement.
See `docs/vision/architecture.md` for the shipped architecture and historical roadmap.
---

## 2. Scope and Boundaries

### Current State
All documented stages (01-06) are shipped. The repo now includes the packet CLI tools, FastAPI service, content-addressed registry, packet diff/lineage, JCT-ready enqueue envelope, MCP server, and static browser UI. `docs/vision/current_reality.md` is the facts-only source of truth.

### Evolution Policy
- **Additive changes allowed:** Tools (`lint_packet.py`, `compose_packet.py`) may be extended with new functionality.
- **No breaking changes:** Existing validation semantics and deterministic outputs must be preserved.
- **Schema evolution:** `pcp_lite.schema.json` may add new optional fields; required fields need migration plan.
- **Template sync:** `CONTEXT_PACKET_TEMPLATE.md` must stay aligned with schema changes.
- **Shared behavior:** HTTP endpoints, MCP tools, and CLI commands should continue to delegate to the same core modules so behavior does not drift.

### Current Allowances
- Add new lint warnings, optional schema fields, render sections, HTTP endpoints, MCP tools, or UI affordances when explicitly scoped.
- Improve registry, diff, enqueue, and permission-check behavior without changing deterministic hashes for unchanged manifests.
- Replace the static UI with a richer frontend only under a new explicit stage plan; the current shipped UI is `ui/index.html`.

### Still out of scope
- Authentication, secrets handling, databases, outbound network behavior, or destructive workflows unless explicitly scoped in a new packet or stage plan.
- Runtime dependencies that require network access in CI or make offline tests impossible.

---

## 3. Required Artifacts (Must Exist and Stay Current)

Codex is responsible for **creating and keeping the following artifacts up to date** as the project evolves.

Always consult `docs/vision/current_reality.md` for the current facts about the project stage and runtime; update that file whenever tasks move the system forward.

### 3.1 Documentation & Contracts

1. `README.md`
   - Must reflect:
     - Current project mission and scope
     - Tech stack actually in use
     - How to run backend, tests, and (if present) UI
   - Update whenever:
     - The setup process changes
     - Key components or workflow change

2. `AGENTS.md` (this file)
   - Must describe:
     - Codex’s role and boundaries
     - Required artifacts
     - Expected workflow and constraints
   - Update when:
     - New stages add responsibilities
     - Constraints or conventions change

3. `CONTEXT_PACKET_TEMPLATE.md`
   - A paste-ready template for Context Packets, with sections such as:
     - Mission
     - Current reality (facts only)
     - Constraints
     - Acceptance (Definition of Done)
     - Required artifacts
     - Failure modes
     - Sources of truth
   - Keep aligned with the actual structure used by the tools and schema.

---

### 3.2 PCP-lite Schema & Manifests

4. `pcp_lite.schema.json`
   - Defines the machine-readable structure of a Context Packet manifest (e.g.):
     - `project`, `stage`, `substage`
     - `mission`
     - `facts[]`
     - `constraints[]`
     - `acceptance[]`
     - `required_artifacts[]`
     - `failure_modes[]`
     - `sources_of_truth[]`
     - `version`
   - Must be updated if:
     - New required fields are introduced
     - Old fields are removed or meaning changes

5. Manifest examples (optional but recommended)
   - Example JSON manifest(s) under:
     - `examples/` or `packets/examples/`
   - Keep examples valid against `pcp_lite.schema.json`.

---

### 3.3 Tools

6. `tools/compose_packet.py`
   - Deterministic tool that:
     - Takes a manifest (e.g. JSON file or stdin)
     - Emits:
       - `packet.md` (Context Packet)
       - `manifest.json` (normalized)
       - `context_sha` (content hash)
   - Must:
     - Use the PCP-lite schema as contract
     - Produce stable output for the same input

7. `tools/lint_packet.py`
   - Validates Context Packet manifests for:
     - Required sections/fields
     - Obvious ambiguity (e.g. empty acceptance criteria)
   - Must:
     - Return a non-zero exit code on lint failure
     - Print useful diagnostics

8. `packets/` directory
   - Contains committed examples under `packets/examples/`.
   - Runtime registry output lives under `packets/registry/<context_sha>/` and is ignored by git.
   - Codex must not commit runtime registry artifacts unless explicitly requested.

---

### 3.4 CI / Automation

 9. `.github/workflows/ci.yml`
   - Must run, at minimum:
     - Tests
     - Packet linter on any committed manifests or templates
     - FastAPI import checks without starting network services
     - Example packet compose checks
   - Update as new tools or tests are added.

---

### 3.5 Docker Dev Container

10. `Dockerfile`, `docker-compose.yml`, `.dockerignore`
   - Run the FastAPI service in a container for local dev: `python:3.12-slim` base, installs `requirements.txt`, runs `uvicorn app.main:app --reload` on port 8000, published to host port 8010.
   - `docker-compose.yml` bind-mounts the repo into `/app` so `--reload` picks up host edits, and so `packets/registry/` persists on the host regardless of whether the service runs bare-metal or containerized.
   - Must be updated if:
     - `requirements.txt` changes (rebuild picks it up automatically, but bump the base image or add system deps here if a new dependency needs them)
     - The app's entrypoint, port, or module path changes
     - A public vhost is added (join `codejourney-proxy` network and add a proxy entry; do this only under an explicit request)
   - The MCP server (`app/mcp_server.py`) stays host-only (stdio, launched via `.mcp.json`) — do not add it to the container.

---

## 4. Change Rules for Codex

When Codex makes changes:

1. **Small surface area**
   - Prefer small, focused changes that touch:
     - One artifact or
     - One logical behavior at a time.

2. **No silent contract changes**
   - If schema, template, or required artifacts change:
     - Update `pcp_lite.schema.json`, `CONTEXT_PACKET_TEMPLATE.md`, and any relevant docs.
     - Ensure CI is updated if needed.

3. **Keep artifacts consistent**
   - If a change affects the Context Packet structure:
     - Update:
       - Template
       - Schema
       - Tools (compose/lint)
       - README and/or AGENTS if behavior or expectations change.

## Stage Reference

- `docs/vision/current_reality.md` — facts-only inventory of the shipped system.
- `docs/vision/architecture.md` — shipped architecture and historical roadmap.
- `docs/vision/STAGE-0{1,2,3,4,5,6}-MISSION.md` — per-stage plans and acceptance gates.

When working on stage-scoped changes, reference the relevant mission file and update `current_reality.md` when the system moves forward.

4. **Respect constraints**
   - No new dependencies without clear purpose and a stage-mission note.
   - No network or secrets in CI or tests.
   - Do not remove existing working functionality without replacement.

---

## 5. Expected Workflow for Codex

For any non-trivial change, Codex should:

1. **Confirm intent**
   - Identify which stage/substage the change belongs to (if applicable).
   - Identify which artifacts are affected.

2. **Update schema / template first (if needed)**
   - Align `pcp_lite.schema.json` and `CONTEXT_PACKET_TEMPLATE.md` with the desired structure.

3. **Update tools**
   - Adjust `compose_packet.py` and/or `lint_packet.py` to match the new contract.

4. **Update docs**
   - Reflect changes in `README.md` and `AGENTS.md` if behavior or expectations changed.

5. **Run checks**
   - Ensure tests and lint pass.
   - Ensure packet linter works on any example manifests/templates.

6. **Commit completed work**
   - After completing a task and running the relevant checks, create a git commit without waiting for a separate prompt.
   - Include only intentional source, docs, tests, and contract changes.
   - Leave generated runtime data under `packets/registry/` uncommitted unless explicitly requested.

---

## 6. Non-Goals for Codex

Codex should **not**:

- Add authentication, databases, background workers, or outbound callbacks unless explicitly requested.
- Replace the static UI or introduce a build toolchain without a new scoped plan.
- Commit generated registry data from `packets/registry/` unless explicitly requested.

By following this guide, Codex helps keep **clarity-engine** simple, reliable, and auditable as new packet capabilities are added.

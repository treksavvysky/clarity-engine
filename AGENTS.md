# AGENTS.md — Operating Guide for Codex

This file defines how Codex should work on the **clarity-engine** repo.

The goal is to keep changes **small, testable, and reversible**, while maintaining the core context-engineering artifacts that humans and other agents rely on.

---

## 1. Mission

The **Clarity Engine** exists to **reduce the cognitive load between raw human intent and aligned strategic action.**

It does not exist to create packets; mission packets are one possible downstream artifact of clarity, not the definition of clarity itself.

Codex’s mission in this repo:

> Implement and maintain small, incremental changes that improve human-first intent capture, route diagnosis, and ephemeral "Smallest Next Move" generation—without breaking existing behavior or contracts.

See [mission.md](file:///home/architect/cognition/clarity-engine/docs/vision/mission.md) for the extended mission statement.
See [CLARITY-ENGINE-2.0-DESIGN-DIRECTION.md](file:///home/architect/cognition/clarity-engine/docs/vision/CLARITY-ENGINE-2.0-DESIGN-DIRECTION.md) for the active 2.0 architecture direction.

---

## 2. Scope and Boundaries

### Current State
Operating as **Clarity Engine Lite**. The repository includes packet CLI tools, a FastAPI service, a content-addressed filesystem registry, packet diff/lineage, MCP server, and a human-friendly static browser UI. `docs/vision/current_reality.md` is the facts-only source of truth.

### Evolution Policy (Clarity Engine Lite & 2.0 Core Rules)
1. **Conversational 5-Question Intake:** UI capturing is structured around:
   - *What is on your mind?* (raw intent)
   - *What makes this hard?* (extracts constraints/boundaries)
   - *What context matters?* (captures immediate facts)
   - *Where should this route?* (predefined dropdown paths)
   - *What do you want back?* (diagnosis/mission/packet/review)
2. **Human-Readable Before Machine-Readable:** The default UI view is a plain-language card (Diagnosis, Mission, Next Action). The machine-readable JSON manifest is a background metadata artifact.
3. **One-Intent / One-Mission Rule:** A single raw intent maps to exactly one primary strategic objective and one next action. Merger of multiple intents is allowed only if they share: same object, same failure condition, same desired state, same execution path, and same review criteria.
4. **The Ephemeral "Smallest Next Move":** Formally defined as *the minimum action needed to move a clarified mission into the correct downstream loop without pretending the mission is complete*. It must not contain checklists, and the engine retains zero memory of its execution state.
5. **No Silent Context Generation:** Gaps in intent must be marked as missing (`missing_info`), not silently invented.

### Still Out of Scope
* **Operational Loops & Task Tracking:** We explicitly avoid task tracking, backlog scheduling, and loop management (decoupled from this repo; handled externally by JCT/DevOps).
* **Continuous Improvement Systems:** PDCA, QRCI, and Hoshin Kanri loops are out-of-scope and belong in separate systems (e.g. [DEVOPS-CONTINUOUS-IMPROVEMENT-LOOP.md](file:///home/architect/cognition/clarity-engine/docs/vision/DEVOPS-CONTINUOUS-IMPROVEMENT-LOOP.md)).
* **Database & Auth:** Persistence remains local filesystem-only under `packets/registry/<sha>/`.
* **Outbound network callbacks / secrets handling.**

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
   - Run the FastAPI service in a container. `plannedintent` is the production deployment host; `codejourney` is the local development and testing workspace.
   - `docker-compose.yml` defines the base service publishing host port 8010 and mounting `packets/registry/` for data persistence.
   - `docker-compose.override.yml` (gitignored) provides host-specific development settings on `codejourney` (bind-mounting `/app` for `--reload` and joining `codejourney-proxy` for sibling containers).
   - Must be updated if:
     - `requirements.txt` changes (rebuild picks it up automatically, but bump the base image or add system deps here if a new dependency needs them)
     - The app's entrypoint, port, or module path changes
     - A public vhost is added (join proxy network and add a proxy entry; do this only under an explicit request)
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

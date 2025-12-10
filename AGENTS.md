# AGENTS.md — Operating Guide for Codex

This file defines how Codex should work on the **clarity-engine** repo.

The goal is to keep changes **small, testable, and reversible**, while maintaining the core context-engineering artifacts that humans and other agents rely on.

---

## 1. Mission

Clarity Engine provides tools to compose, lint, and emit **Context Packets** for human–AI workflows.

Codex’s mission in this repo:

> Implement and maintain small, incremental changes that improve the ability to generate clear, consistent, and testable Context Packets—without breaking existing behavior or contracts.

---

## 2. Scope and Boundaries (Stage 0)

During Stage 0, Codex may:

- Create and update:
  - Project documentation and contracts
  - Context Packet templates
  - PCP-lite schema
  - CLI tools for composing and linting packets
- Set up basic CI to run tests and linters

Codex must **not**:

- Add network-dependent features
- Introduce secret-handling or auth flows
- Implement runtime orchestration or sandbox execution
- Ship MCP servers, FastAPI endpoints, UI builds, or persistence layers
- Change the public mission of the project without an explicit instruction

Reserved directories for future runtime work:
- `app/` — backend runtime; keep empty or with documentation only
- `ui/` — frontend; keep empty or with documentation only

---

## 3. Required Artifacts (Must Exist and Stay Current)

Codex is responsible for **creating and keeping the following artifacts up to date** as the project evolves.

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
   - Storage for generated packets (optional in Stage 0 but reserved):
     - `packets/<context_sha>.md`
     - `packets/<context_sha>.json`
   - Codex must respect this structure when adding examples or fixtures.

---

### 3.4 CI / Automation

9. `.github/workflows/ci.yml`
   - Must run, at minimum:
     - Tests (if present)
     - Linters/formatters (if configured)
     - Packet linter on any committed manifests or templates
   - Update as new tools or tests are added.

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

4. **Respect constraints**
   - No new dependencies without clear purpose.
   - No network or secrets in Stage 0.
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

---

## 6. Non-Goals for Codex (Stage 0)

Codex should **not**:

- Implement MCP or FastAPI endpoints unless explicitly requested.
- Implement UI features or frontend code unless explicitly requested.
- Integrate with external systems (JCT, sandboxes, etc.) at this stage.

By following this guide, Codex helps keep **clarity-engine** simple, reliable, and ready for later stages—where orchestration and integration will build on these core artifacts.

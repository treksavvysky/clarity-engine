# Current Reality (Facts Only) — Clarity Engine Lite

## 1. Clarity Engine Lite Doctrine & Baseline
The Clarity Engine has been refactored into **Clarity Engine Lite**, aligning with its core doctrine as an intent-to-mission compiler. It does not store memory, execute work, or manage tasks directly.

The system is defined by these eight core capabilities:
1. **Capture raw intent** — messiest human impulse/impulse seeds.
2. **Capture human constraints** — boundaries for time, scope, or action.
3. **Capture additional context** — background facts and connections.
4. **Select route** — strategic pathing (e.g. SMI, Clarity Engine, Strategic Plan).
5. **Produce readable diagnosis** — flags DevOps/CI continuous improvement tasks and recommends routing them to external issue trackers.
6. **Produce one clarified mission** — clean strategic objective framing the intent without vague language.
7. **Produce one smallest next action** — concrete, safe first step to begin design definition.
8. **Optionally reveal structured packet** — toggleable advanced view for the compiled PCP-lite JSON manifest.

---

## 2. API Endpoints (`app/main.py`)
- `GET /healthz` — returns health status.
- `POST /intents/draft` — intake boundary that processes raw intent, runs DevOps diagnosis, cleans vague terms, and drafts the manifest without registry writes.
- `POST /packets/register` — registers a compiled manifest in the filesystem registry only after review.
- `POST /packets/diff` — computes changes between two manifests or registered SHAs.
- `POST /packets/compose` — compositions endpoint (renders markdown).
- `POST /packets/lint` — validates manifests against schema.
- `/packets/enqueue` — (DEFERRED/HIDDEN) JCT-compatible task queue envelope generation.

---

## 3. UI Implementation (`ui/index.html`)
- **Beginner mode (Default):**
  - Land directly on the **Intent Capture** tab.
  - Text inputs for Messy Intent, Context Bullets, and Constraint Bullets.
  - Returns a beautifully formatted HTML preview card showing Strategic Objective, Constraints, Acceptance Criteria, and the highlighted Smallest Next Action.
  - Prominent alert banners for DevOps routing diagnosis and linter warnings.
  - Gated registry workflow: *"Approve & Save to Registry"* button is enabled only after a successful draft is compiled.
- **Advanced mode (Toggleable):**
  - Clicking *"Enable Advanced Mode"* reveals the "Registered Missions", "Diff", and "Editor" tabs, route selection inputs, and raw JSON previews.
  - Hides JCT enqueue controls.

---

## 4. Dependencies & Runtime
- Base requirements: FastAPI, Uvicorn, pytest, mcp.
- Local filesystem registry at `packets/registry/` (gitignored).
- Standard unit tests cover CLI compose/lint, registry diffing, lineage, intents draft, DevOps diagnosis, and UI mounts. All 55 tests pass in-process.

---

## 5. Explicitly Deferred / Out of Scope
The following areas are deferred from the engine and handled externally:
- **Automatic registry writes** (registry is review-gated).
- **Task queuing & JCT orchestration** (hidden/deferred).
- **Cross-project rollouts** (out of scope).
- **Full SMI/PCP/Anamnesis integration** (SMI/Anamnesis are separate systems).
- **Multi-agent execution** (execution is handled by worker agents like Jules/Codex/Claude).
- **The Intent Router** (complex automated routing is deferred; manual/diagnosed route select remains).

### 5.1 Intelligence Engine Interface (Deferred Specification)
Future MCP servers, custom GPTs, or connected apps serving as the Clarity Engine interpreter should align with the following request/response schema contract:

**Draft Request (Input):**
```json
{
  "raw_intent": "...",
  "human_constraints": "...",
  "additional_context": ["..."],
  "route": ["..."],
  "known_project_context": "...",
  "desired_output_mode": "diagnosis | mission | packet | review"
}
```

**Draft Response (Output):**
```json
{
  "diagnosis": "...",
  "clarified_intent": "...",
  "mission": "...",
  "path": "engineering | lifeops | mixed",
  "smallest_next_action": "...",
  "packet_draft": {},
  "review_required": true
}
```
*Note: The first user-facing layer serving these outputs must be presented in plain, readable language.*


# Current Reality (Facts Only) — Clarity Engine 2.0

## 1. Clarity Engine 2.0 Doctrine & Baseline
The Clarity Engine has been upgraded to **Clarity Engine 2.0**, fully implementing the Prime Directive of reducing cognitive load between messy human intent and aligned strategic action.

The system features:
1. **Conversational 5-Question Intake:** UI capturing is structured around what is on your mind, what makes this hard (friction/constraints), what context matters, where it should route (dropdown), and what you want back.
2. **4-Step Plain-Language Output Hierarchy:** Output cards present Plain-Language Diagnosis (warnings and DevOps redirection checks), Clarified Mission, Smallest Next Action (dynamic momentum seed addressing user friction), and an Optional Packet manifest (hidden behind Advanced toggle).
3. **One-Intent / One-Mission Rule:** A single raw intent maps 1-to-1 with a strategic mission.
4. **Loop Separation:** Backlog queues, task tracking, and outbound execution are out of scope. Obsolete queuing endpoints are deprecated.

---

## 2. API Endpoints (`app/main.py`)
- `GET /healthz` — returns health status.
- `POST /intents/draft` — intake boundary that processes raw intent with 2.0 conversational fields, performs DevOps regex word-boundary checks, compiles strategic missions, and returns the 4-step output payload.
- `POST /packets/register` — registers a compiled manifest in the filesystem registry only after review.
- `POST /packets/diff` — computes changes between two manifests or registered SHAs.
- `POST /packets/compose` — compositions endpoint (renders markdown).
- `POST /packets/lint` — validates manifests against schema.
- `/packets/enqueue` — (DEPRECATED) JCT-compatible task queue envelope generation.

---

## 3. UI Implementation (`ui/index.html`)
- **Conversational Wizard View (Default):**
  - Textareas for Question 1 (mind), Question 2 (hard/friction), and Question 3 (context).
  - Strict Dropdown Select for Question 4 (Route selection).
  - Dropdown Select for Question 5 (Desired output density).
  - Displays a clean 4-step output card layout.
  - Registry workflow is review-gated: *"Approve & Save to Registry"* is enabled only after drafting.
- **Advanced Mode (Toggleable):**
  - Revealing tabs for "Registered Missions", "Diff", and "Editor".
  - Shows known project context input overrides and raw JSON manifests.

---

## 4. MCP Server (`app/mcp_server.py`)
- Exposed as stdio MCP server `clarity-engine`.
- Exposes tools: `compose_packet_tool`, `lint_packet_tool`, `register_packet_tool`, `get_packet_tool`, `list_packets_tool`, `diff_packets_tool`, `check_action_tool`.
- Added **`draft_intent_tool`**: Enables client agents to programmatically draft 2.0 strategic missions conversational wizard style.

---

## 5. Dependencies & Runtime
- FastAPI, Uvicorn, pytest, mcp.
- Local filesystem registry at `packets/registry/` (gitignored).
- Standard unit tests cover CLI tools, endpoints, schema lint, DevOps diagnosis, MCP tool parity, and UI static assets. All 59 tests are fully green.


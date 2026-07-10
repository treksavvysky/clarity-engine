# Clarity Engine 2.0 Implementation Roadmap

This roadmap tracks the step-by-step transition from Clarity Engine Lite to Clarity Engine 2.0. Progress must be documented by marking items with `[x]` along with the commit hash and a one-line summary as evidence of completion.

---

## Phase 1: Intake & Core Translation Backend
Focuses on updating the backend schemas, endpoints, and helpers to support the 5-question conversational workflow.

* [ ] **Task 1.1: Implement 2.0 Intake Schema Contracts**
  * Update API payload validation to accept the 5 conversational input fields mapping to standard keys.
  * *Evidence:*
* [ ] **Task 1.2: Refactor Constraint & Context Extraction**
  * Update the compilation compiler to translate Question 2 ("What makes this hard?") into schema constraints, and Question 3 ("What context matters?") into background current reality facts.
  * *Evidence:*
* [ ] **Task 1.3: Update Backend Test Coverage**
  * Add unit tests to verify the conversational schema validation, extraction logic, and input-to-manifest mapping.
  * *Evidence:*

---

## Phase 2: Plain-Language Output & Intercept Routing
Refactors the API responses to return the 4-step output hierarchy and locks down route-governed behaviors.

* [ ] **Task 2.1: Refactor Draft Output Payloads**
  * Modify the `/intents/draft` endpoint response to return exactly the 4-step output hierarchy (diagnosis, mission, smallest_next_action, and optional packet_draft).
  * *Evidence:*
* [ ] **Task 2.2: Implement Dropdown Route Logic**
  * Refactor route processing to accept the dropdown route selections and determine grounding rules and downstream handoff types.
  * *Evidence:*
* [ ] **Task 2.3: Lock Down the Ephemeral Next Action**
  * Implement the strict next-action formatter that extracts a singular momentum seed from the friction question without checklists or task queues.
  * *Evidence:*
* [ ] **Task 2.4: Validate Phase 2 Endpoints**
  * Write unit tests for route boundaries, next-action formulation, and plain-language diagnosis blocks.
  * *Evidence:*

---

## Phase 3: Conversational User Interface
Redesigns the static web viewport to serve a conversational intake layout and scannable cards.

* [ ] **Task 3.1: Build the Conversational Input UI**
  * Redesign `ui/index.html` to present the 5 conversational capture questions, with Question 4 rendered as a strict dropdown list.
  * *Evidence:*
* [ ] **Task 3.2: Render the 4-Step Output Hierarchy Card**
  * Refactor the frontend display panels to map draft responses to the scannable 4-step output card layout, hiding the JSON block behind the Advanced Mode toggle.
  * *Evidence:*
* [ ] **Task 3.3: Write Frontend Integration Tests**
  * Add UI integration tests to assert that root serving mounts the new conversational UI and processes inputs correctly.
  * *Evidence:*

---

## Phase 4: Integration & Cleanup
Aligns CLI tools and the MCP server with the new 2.0 compilation engine, and deactivates obsolete modules.

* [ ] **Task 4.1: Update MCP Server Tools**
  * Align the stdio MCP tools (`compose`, `lint`, `register`) with the updated 2.0 schema translation boundaries.
  * *Evidence:*
* [ ] **Task 4.2: Deactivate Obsolete Task/JCT Assets**
  * Remove or isolate JCT queuing logic and JCT endpoints to maintain loop separation boundaries.
  * *Evidence:*
* [ ] **Task 4.3: Final Regression Testing**
  * Run the full unit and integration test suite to ensure 100% green coverage across all endpoints and CLI scripts.
  * *Evidence:*

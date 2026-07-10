# Clarity Engine 2.0: Strategic Design Direction

## 1. Executive Summary & Doctrine Refinement
Clarity Engine 2.0 shifts focus from **artifact generation** to **cognitive resolution**. Its core directive is to:

> **Reduce the distance between human intent and aligned action.**

We recognize that structured Context Packets are merely one possible artifact of clarity, not the definition of clarity itself. The system must exist to clear human mental drag and align strategic momentum, separating itself entirely from task tracking and DevOps continuous improvement loops.

---

## 2. Core Architectural Pillars

```
+---------------------------------------------------------------+
|                      Human Raw Capture                        |
|              (Single Input, Messy Thought Seed)               |
+------------------------------+--------------------------------+
                               |
                               v
+------------------------------+--------------------------------+
|                 Intelligence Parsing Layer                    |
|       - Extract constraints & contexts dynamically           |
|       - Diagnose & Route DevOps/Task/Strategic items          |
+------------------------------+--------------------------------+
                               |
                               +------------------------+
                               | (Strategic Mission)    | (DevOps Issue)
                               v                        v
+------------------------------+-------+  +-------------+-------+
|        Clarity Engine 2.0 Core       |  |  External Tooling   |
|   - One Strategic Objective           |  |  - Issue Tracker    |
|   - One Smallest Next Action          |  |  - Task Board (JCT) |
|   - Schema manifest (Background only) |  |  - Memory (SMI)     |
+--------------------------------------+  +---------------------+
```

### Pillar 1: Conversational Zero-Friction Capture (The 5-Question Workflow)
* **Lite Baseline:** The human manually inputs separate textareas labeled Intent, Context Bullets, and Constraint Bullets.
* **2.0 Direction:** The capture interface is replaced with a brutally simple, conversational 5-step form (or single-page equivalent) based on these questions:
  1. **What is on your mind?** (Maps to `raw_intent` messy thought dump)
  2. **What makes this hard?** (Maps to `human_constraints` - extracts friction/boundaries naturally)
  3. **What context matters?** (Maps to `additional_context` - captures immediate connections)
  4. **Where should this route?** (Selected via a simple dropdown in the UI containing predefined paths like SMI, Mnemos, DevOps, or Strategic Plan, mapping to `route`)
  5. **What do you want back?** (Maps to `desired_output_mode` - options: diagnosis, mission, packet, or review)

### Pillar 2: DevOps Separation & Route Diagnosis
* **Lite Baseline:** Checks for DevOps keywords and logs warning alerts on the UI.
* **2.0 Direction:** Strict intercept routing. DevOps tasks (bug fixes, refactoring, deployments) are automatically flagged, and the compiler prevents strategic mission generation for them, guiding the human to route them to issue trackers or continuous improvement channels.
* **Route Governance:** When the automated routing layer is implemented, the selected **Routes** must dictate:
  1. **Grounding behavior:** How raw intent is anchored against SMI variables, project state (PCP), or Mnemos workspace memory.
  2. **Output type:** The structure of the generated artifact (e.g. strategic mission, observation note, architecture rule).
  3. **Downstream handoff:** The target execution context or agent (e.g. JCT state queues, Jules worker, Mnemos workspace).

### Pillar 3: The Plain-Language Output Hierarchy
* **Lite Baseline:** Displays the entire structured manifest details (Acceptance, Failure Modes, etc.) on the UI card.
* **2.0 Direction:** The output is structured strictly into a clean, human-scannable layout:
  1. **Plain-Language Diagnosis:** Clear routing guidance and context analysis (e.g. DevOps detection or warnings).
  2. **Clarified Mission:** Sanitized strategic objective framing the intent without vague words.
  3. **Smallest Next Action:** One immediate, low-friction next step to kickstart momentum.
  4. **Optional Packet:** The detailed PCP-lite manifest JSON, hidden by default and revealed only on demand.
* **Deferred Packet Formalization:** The formalization of the mission packet (JSON serialization, schema verification, and filesystem registry writes) is **deferred** until we are ready to build the downstream intelligence layer (the agents that actually consume these packets). Until then, the system operates as a pure cognitive unblocker, avoiding the administrative overhead of premature structured files.

---

## 3. Interface Schema Contract (Deferred Implementation)

To decouple the UI from the intelligence processing layer, Clarity Engine 2.0 defines this standard payload contract for interpreter integrations (such as custom GPTs, MCP tools, and external services):

### Input Payload
```json
{
  "raw_intent": "string (Question 1: What is on your mind?)",
  "human_constraints": "string (Question 2: What makes this hard?)",
  "additional_context": ["string (Question 3: What context matters?)"],
  "route": ["string (Question 4: Where should this route? Dropdown selection)"],
  "known_project_context": "string (extracted from SMI/PCP)",
  "desired_output_mode": "diagnosis | mission | packet | review (Question 5: What do you want back?)"
}
```

### Output Payload
```json
{
  "diagnosis": "string (Output 1: Plain-language diagnosis - DevOps check, warnings, lint status)",
  "mission": "string (Output 2: Clarified mission - sanitized strategic objective)",
  "smallest_next_action": "string (Output 3: Smallest next action - first concrete step)",
  "packet_draft": {
    "project": "string",
    "stage": "string",
    "substage": "string",
    "version": "string",
    "mission": "string",
    "current_reality": ["string"],
    "constraints": ["string"],
    "acceptance": ["string"],
    "required_artifacts": ["string"],
    "failure_modes": ["string"]
  },
  "review_required": "boolean"
}
```

---

## 4. UI/UX Evolution Path
* **Standard Strategic Interface:** An ultra-clean, card-based interface focused on single-box capture, diagnosis banners, and single next-action highlights.
* **Advanced/Power User Mode:** Remains toggleable to reveal JSON schema editors, diff tools, version lineage graphs, and direct registry reads/writes.

---

## 5. Core Lessons Learned (Clarity Engine Lite)
The development of Clarity Engine 2.0 is guided by these five critical design lessons:

1. **One Intent, One Clarification:** One raw intent produces exactly one primary strategic objective and one next action, preventing premature decomposition and task bloat unless the user explicitly requests it.
2. **Human Comprehension is the Metric of Success:** A packet is only successful if the human operator can understand the strategic mission in 5 seconds or less. Technical complexity must not block comprehension.
3. **Human-Readable Before Machine-Readable:** The default interface must speak in plain, scannable language. Structuring machine-readable schemas (like JSON manifests) is a secondary compilation output that resides in the background.
4. **No Silent Context Hallucination:** Missing constraints or context must be explicitly marked as missing (using flags like `missing_info` and linter warnings), forcing the human to clarify rather than letting the system silently invent facts.
5. **Separation of Strategy and Tasking:** Clarity Engine produces strategic mission clarity. Downstream task trackers (like JCT) and execution agents manage individual checklists, schedules, and task queues.

---

## 6. Discarded & Redesigned Legacy Paradigms
To prevent design regression, Clarity Engine 2.0 explicitly discards or radically refactors these legacy architectural concepts:

* **Packet-First Output (Discarded):** Replaced by a human-first strategic card layout (Diagnosis, Mission, Smallest Next Action). The structured packet is a background artifact.
* **Markdown-Dense Presentation (Redesigned):** Replaced with clean, scannable visual typography. The verbose text blocks are hidden by default.
* **Multi-Packet Generation (Discarded):** Gated under a strict 1-to-1 ratio (One Intent -> One Mission) to reduce decision fatigue.
* **Premature Registry Workflow (Discarded/Deferred):** Automatic or low-gate file writes are deactivated. Registry saving is strictly manual, review-gated, and deferred.
* **Overloaded Task/Project Hierarchy (Discarded):** Removed task tracking and nested project arrays. Clarity Engine tracks strategic meaning, not execution status.
* **Ambiguous Route Semantics (Redesigned):** Replaced manual text routes with strict route selection (via UI dropdown) that governs grounding rules, output layouts, and downstream handoff properties.

---

## 7. Defining the "Smallest Next Move" (Anti-Task-Manager Bounds)
To prevent design regression into task tracking, the **Smallest Next Move** is formally defined as:

> **The minimum action needed to move a clarified mission into the correct downstream loop without pretending the mission is complete.**

* **It is not the complete plan:** It represents a single trigger seed to start the improvement or execution loop, not a breakdown of the mission.
* **It is not the only thing required:** It initiates progress without implying the mission is solved.
* **It is not a task list:** It contains a single momentum action rather than scheduling checklists or tracking states.

Under the hood, this is governed by three strict architectural constraints:
1. **Ephemerality (No State Tracking):** Clarity Engine maintains **zero execution memory**. It does not track whether a move is "done," "in progress," or "blocked." It presents the trigger seed once and exits.
2. **Singular Momentum (No Checklists):** The output produces exactly **one** immediate first action. Generating task lists, backlogs, or checklists is strictly prohibited.
3. **Friction-Centric Extraction:** The move is extracted by diagnosing *"What makes this hard?"* (Question 2 of the capture workflow) and identifying the absolute smallest entry point to unblock that specific friction and route the mission to the correct downstream loop (e.g. QRCI, PDCA, or Hoshin).

By enforcing these boundaries, the engine remains focused on **cognitive resolution** (reducing cognitive load to zero) while leaving all project management state to external trackers.

---

## 8. Multi-Intent Consolidation (The Merger Rule)
While the default mapping is strictly 1-to-1 (One Intent -> One Mission), either the human or the Intelligence Layer may identify related raw intents over time that should be consolidated. Multiple raw intents may be formulated into a single strategic mission if and only if they share:

1. **Same Object:** They concern the exact same system, situation, or ecosystem boundary.
2. **Same Failure Condition:** They trace back to the same root problem or vulnerability.
3. **Same Desired State:** Resolving the intents leads to a single, coherent strategic outcome.
4. **Same Execution Path:** The unblocking effort can be addressed in a single, bounded sweep.
5. **Same Review Criteria:** Success for all intents can be evaluated collectively under one standard.

When merged, the original raw intents must be preserved individually in the background compilation metadata (e.g. within `current_reality` history) to maintain complete auditability, while rendering a single plain-language mission card for the operator.

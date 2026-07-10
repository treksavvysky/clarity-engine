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

### Pillar 1: Zero-Friction Capturing (Single-Box Intake)
* **Lite Baseline:** The human manually inputs separate arrays for Intent, Context Bullets, and Constraint Bullets.
* **2.0 Direction:** The capture interface is reduced to a single input field. The human dumps a messy paragraph. Under the hood, the backend parses, extracts, and populates the schema fields (contexts, constraints, routes) dynamically.

### Pillar 2: DevOps Separation & Route Diagnosis
* **Lite Baseline:** Checks for DevOps keywords and logs warning alerts on the UI.
* **2.0 Direction:** Strict intercept routing. DevOps tasks (bug fixes, refactoring, deployments) are automatically flagged, and the compiler prevents strategic mission generation for them, guiding the human to route them to issue trackers or continuous improvement channels.

### Pillar 3: The "One-Action" Resolution Principle
* **Lite Baseline:** Displays the entire structured manifest details (Acceptance, Failure Modes, etc.) on the UI card.
* **2.0 Direction:** The primary output is reduced to the absolute minimum needed for momentum:
  1. **One Clarified Strategic Objective.**
  2. **One Smallest Next Action.**
* **Deferred Packet Formalization:** The formalization of the mission packet (JSON serialization, schema verification, and filesystem registry writes) is **deferred** until we are ready to build the downstream intelligence layer (the agents that actually consume these packets). Until then, the system operates as a pure cognitive unblocker, avoiding the administrative overhead of premature structured files.

---

## 3. Interface Schema Contract (Deferred Implementation)

To decouple the UI from the intelligence processing layer, Clarity Engine 2.0 defines this standard payload contract for interpreter integrations (such as custom GPTs, MCP tools, and external services):

### Input Payload
```json
{
  "raw_intent": "string (messy human input)",
  "human_constraints": "string (optional manual constraints)",
  "additional_context": ["string (optional context bullets)"],
  "route": ["string (suggested path)"],
  "known_project_context": "string (extracted from SMI/PCP)",
  "desired_output_mode": "diagnosis | mission | packet | review"
}
```

### Output Payload
```json
{
  "diagnosis": "string (DevOps warning, task route recommendation, or lint checks)",
  "clarified_intent": "string (sanitized, prefix-free statement)",
  "mission": "string (Establish strategic framework and boundaries for...)",
  "path": "engineering | lifeops | mixed",
  "smallest_next_action": "string (the immediate concrete first step)",
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

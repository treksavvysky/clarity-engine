# Clarity Engine: Overview & Detailed Description

## 1. High-Level Arc and Main Objective
The ultimate objective of our project is to **build an autonomous cognitive ecosystem that supports human intent, AI cognition, software execution, memory, and life operations.**

The **Clarity Engine** is a small, specialized part of this ecosystem.

---

## 2. Clarity Engine Doctrine
The Clarity Engine serves strictly as the **cognitive intent compiler** of the ACE/Cortex ecosystem.

* **It does not store memory.** (Memory is handled by `Mnemos` and `SMI`).
* **It does not execute work.** (Execution is handled by worker agents like Jules/Codex/Claude).
* **It does not manage tasks directly.** (Orchestration is handled by task/job trackers like JCT).

Its sole job is to **clarify intent**.

It takes raw human input, retrieved memory, present project truth (PCP), doctrine, constraints, and strategic state, and refines them into a structured mission packet suitable for downstream planning and execution.

* **SMI** tells the system where meaning lives.
* **Anamnesis** tells the system what past context still applies.
* **PCP** tells the system what is currently true about a project.
* **Mnemos** gives the human a human-facing cognitive workspace.
* **The Clarity Engine** decides what the intent means *now* and preserves the bridge between thought and action.

---

## 3. DevOps vs. Strategic Intent Separation (Routing & Diagnosis)
A key failure mode is conflating strategic intent/mission definition with continuous DevOps tasks (bug fixing, refactoring, code formatting, CI/CD setup, ticket management). 

Clarity Engine is designed to capture high-level strategic intentions. It is **not** a DevOps issue tracker or ticket queue. DevOps continuous improvement tasks belong in their respective dedicated systems (issue trackers, product docs, CI pipelines). Clarity Engine diagnoses and flags incoming DevOps-specific tasks to route them correctly, keeping the engine focused on strategic clarification.

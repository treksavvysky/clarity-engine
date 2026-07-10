# Intent Capture Guide — How to Feed the Clarity Engine

_Practical tips for the human side of the pipeline: what good raw input looks like, and what to avoid._

## The first principle

**Do not try to give the Clarity Engine clean intent. Give it honest intent.**

The human role is not to perfectly organize a thought before capture — that defeats the point. The Clarity Engine exists because raw human intention is often emotional, incomplete, layered, and tangled with memory, fear, urgency, strategy, and half-formed possibility.

The best practice is to capture **enough signal** for the system to clarify. The human should not become the compiler. The human should remain the source of intent.

---

## 1. Capture the raw impulse first

Start with the messy sentence:

> "I need to do something about the Ford Focus."

> "I feel like this project is drifting."

> "I want Mnemos to matter, but I'm not sure what it actually does yet."

> "I'm worried I'm creating too many systems again."

This is valuable. Do not prematurely convert it into a task — raw impulse is often where the real intent lives.

**Bad capture:**

> "Create task: fix car."

**Better capture:**

> "The Ford Focus is becoming an unresolved liability. It connects to California readiness, money, mobility, and my sense that I'm letting open loops accumulate."

That gives the Clarity Engine something to work with.

## 2. Separate signal from noise

When capturing intent, try to name three things:

- **What happened?** — the observable fact.
- **What does it mean to me?** — the interpretation or concern.
- **What might need to change?** — the desired movement.

Example:

> "The Ford Focus still needs attention. That matters because it is part of my larger California-readiness mission. I do not need to solve everything now, but I need it represented correctly in the system so it stops living as mental background noise."

That is excellent intent capture.

## 3. Use "I think / I feel / I need / I want" without shame

These are not weak phrases. They are intent markers, and each one carries different signal:

| Phrase                 | What it reveals              |
| ---------------------- | ---------------------------- |
| "I think…"             | current reasoning            |
| "I feel…"              | emotional weight             |
| "I need…"              | perceived necessity          |
| "I want…"              | desired future               |
| "I'm avoiding…"        | friction or resistance       |
| "I keep returning to…" | unresolved importance        |
| "This connects to…"    | dependency or larger mission |

The Clarity Engine treats these as raw cognitive telemetry.

## 4. Always name the larger mission when known

Human intent is rarely isolated. A task becomes clearer when attached to the mission it serves.

Instead of:

> "Clean car."

Say:

> "Clean the Ford Focus as part of California readiness and reducing life-ops drag."

Instead of:

> "Work on Mnemos."

Say:

> "Clarify Mnemos as the human-facing second brain so it does not get confused with Cortex OS, SMI, or ACE memory."

This prevents the system from flattening meaning into chores.

## 5. Capture constraints early

Constraints are not obstacles. They are design boundaries.

| Constraint type | Example                                        |
| --------------- | ---------------------------------------------- |
| Time            | "I only have 30 minutes."                      |
| Energy          | "I'm mentally tired today."                    |
| Money           | "This cannot require spending right now."      |
| Scope           | "Do not turn this into a new project."         |
| Tooling         | "This belongs in ACE, not a todo app."         |
| Urgency         | "This matters before the Mammoth Lakes trip."  |
| Boundary        | "No coding yet; doctrine first."               |

A vague intent with clear constraints is often better than a detailed task with no boundaries.

## 6. Define the desired state, not just the action

Actions are brittle. Desired states are strategic.

**Weak:**

> "Make a task list for the car."

**Strong:**

> "I want the Ford Focus represented as a bounded life-ops mission with clear next actions, dependencies, and its relationship to California readiness."

The Clarity Engine's question is always: **what state is the system supposed to reach?** Examples of desired states:

- "This is no longer floating in my head."
- "This project has a clear current objective."
- "This idea has been classified correctly."
- "This open loop has a next action."
- "This memory has been grounded against present reality."
- "This ambition has been reduced to one executable mission."

## 7. Use the "messy capture" format

When your thoughts are tangled, use this template:

```text
Raw thought:
I am thinking about...

Why it matters:
This matters because...

Current friction:
The thing that feels unclear or blocked is...

Larger mission:
This connects to...

Constraint:
Right now, I do not want to...

Desired outcome:
What I want after clarification is...
```

Example:

```text
Raw thought:
I am thinking about Mnemos again and how it relates to Obsidian.

Why it matters:
This matters because I need a human-facing second brain, not another vague AI project.

Current friction:
The unclear part is whether Mnemos stores memory, indexes memory, or acts as a workspace over memory.

Larger mission:
This connects to Cortex OS, SMI, Scriptoria, and my personal cognitive infrastructure.

Constraint:
I do not want to start coding yet.

Desired outcome:
I want a clean definition of Mnemos' role and boundaries.
```

That is near-perfect input for the Clarity Engine.

## 8. Do not overclassify too soon

A common trap is trying to decide immediately: Is this ACE? Mnemos? SMI? Fionn? Cortex OS? Life ops? A project? A task?

Sometimes the correct first move is simply:

> "This is an unresolved intent requiring classification."

Let the Clarity Engine classify after context is gathered. **Premature classification creates architectural debt.**

## 9. Mark uncertainty explicitly

Uncertainty is useful data. Say things like:

> "I'm not sure if this belongs in ACE or Mnemos."

> "I may be mixing up memory, indexing, and orchestration."

> "This might be a project, or it might only be doctrine."

> "I don't know if this is urgent or just emotionally loud."

That gives the system permission to resolve ambiguity rather than assume certainty.

## 10. Use levels of intent

Not every thought is a mission. The Clarity Engine distinguishes levels:

| Level       | Meaning                     | Example                                           |
| ----------- | --------------------------- | ------------------------------------------------- |
| Observation | Something noticed           | "The car needs attention."                        |
| Concern     | Something creating pressure | "This may affect California readiness."           |
| Desire      | Something wanted            | "I want this open loop handled."                  |
| Decision    | Commitment made             | "The Ford Focus is part of California readiness." |
| Mission     | Structured objective        | "Create a vehicle-readiness plan."                |
| Task        | Concrete action             | "Check tire condition today."                     |

A good capture can be as simple as:

> "This is an observation, not yet a task."

That prevents task bloat.

## 11. Keep doctrine separate from execution

Some thoughts are not tasks. They are doctrine.

Example:

> "Mnemos is not memory itself; it is the human-facing command surface over memory."

That should **not** become:

> "Build Mnemos UI."

It should become a doctrine entry, definition, or architectural constraint. The Clarity Engine preserves the difference between:

- **Idea**
- **Doctrine**
- **Decision**
- **Mission**
- **Task**
- **System requirement**
- **Memory update**
- **Present reality correction**

That distinction is crucial.

## 12. Best single prompt to use

When in doubt, give the Clarity Engine this:

```text
Clarify this intent.

Raw thought:
[write messy thought here]

Context:
[what this connects to]

Why it matters:
[why I care]

Constraints:
[what not to do / limits / timing / energy]

Desired output:
Turn this into the right structure: observation, doctrine, decision, mission, task, or project update.
```

The prompt is simple, but it does the right thing: it does not assume the output category before clarification.

---

## Practical rule: the cognitive seed

The ideal human input is not a perfect requirement. It is a **cognitive seed** with five nutrients:

1. **Raw thought**
2. **Why it matters**
3. **What it connects to**
4. **What constraints exist**
5. **What kind of clarity you want**

The Clarity Engine's job is to transform that seed into structure.

> The human should not become the compiler. The human should remain the source of intent.

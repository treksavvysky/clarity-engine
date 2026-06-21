# Agent Refinement Proposal Contract

Agent Refinement Proposals hold evidence-backed agent analysis before a human
accepts any material into immutable Raw Intent lineage.

They are separate from both Raw Intent Packets and PCP-lite Mission Packets. A
proposal cannot change Raw Intent status, request readiness, assert approval,
promote a Mission Packet, enqueue work, or execute actions.

## Required Fields

- `version` — currently `1.0.0`.
- `source_intent_sha` — the exact registered Raw Intent revision analyzed.
- `proposer` — agent and transport attribution, with an optional model label.
- `summary` — the bounded purpose and conclusion of the analysis.
- `grounding_entries` — sourced observations, verified facts, or rejected
  assumptions.
- `clarification_questions` — stable-ID questions for the human.
- `unresolved_gaps` — evidence or decisions still missing.
- `created_at` — an RFC 3339 timestamp with timezone.

Every grounding entry requires at least one source. Source strings remain
transport-neutral pointers such as `repo:path`, `fluxion:ISSUE`, or
`intent:<sha>`. A source pointer does not mechanically prove a claim; it makes
the evidence inspectable during review.

## Deterministic Identity

`tools/agent_refinement_proposal.py` validates, canonicalizes, renders, and
hashes the complete proposal. Canonical JSON uses sorted keys, two-space
indentation, preserved Unicode, and one trailing newline. The resulting
`proposal_sha` changes when any proposal field changes.

```bash
python tools/agent_refinement_proposal.py lint \
  packets/examples/agent_refinement_proposal_example.json

python tools/agent_refinement_proposal.py compose \
  packets/examples/agent_refinement_proposal_example.json \
  --output-dir /tmp/agent-refinement-proposal
```

Compose emits `manifest.json`, `proposal.md`, and `proposal_sha`.

The canonical Eidolon example identity is:

```text
15e7418c61243da509799ee51298b41a672e366953ef3b0696707ed6713b76c6
```

## Current Boundary

The contract and CLI are side-effect-free. There is no proposal registry, HTTP
endpoint, MCP proposal tool, or browser proposal review yet. Existing Raw Intent
MCP tools remain read-only. Human-controlled grounding, clarification,
readiness, approval, and promotion continue through the shipped browser and
HTTP workflow.

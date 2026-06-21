# Raw Intent Packet Contract

Raw Intent Packets preserve early human thought before it has been grounded into
an executable PCP-lite Mission Packet.

The contract is intentionally separate from `pcp_lite.schema.json`. Raw intent
may be vague, speculative, or incomplete, so it must not be placed in a Mission
Packet's factual `current_reality` merely because it was captured.

## Contract

`raw_intent_packet.schema.json` defines the v1 manifest. Required fields are:

- `version` — currently `1.0.0`.
- `raw_intent` — the original accepted JSON string, preserved verbatim.
- `status` — one of `captured`, `grounding`, `clarification_needed`,
  `ready_for_mission`, `promoted`, or `abandoned`.
- `provenance.source` — one of `ui`, `api`, `cli`, `mcp`, or `import`.

Optional fields separate human-supplied context, constraints, desired direction,
assumptions, related projects, clarification needs, and context sources from
derived grounding material.

Structured grounding uses:

```json
{
  "grounding_entries": [{
    "kind": "verified_fact",
    "statement": "The repository contains app/main.py.",
    "sources": ["repo:app/main.py"]
  }]
}
```

`kind` is `observation`, `verified_fact`, or `rejected_assumption`. Every entry
requires at least one source reference.

Structured clarification records use stable IDs:

```json
{
  "clarifications": [{
    "id": "deployment-owner",
    "question": "Who owns deployment?",
    "status": "answered",
    "answer": "The platform maintainer."
  }]
}
```

Open records omit `answer`; answered records require it. IDs are unique within
the packet.

Raw Intent Packets do not contain a mission, factual Current Reality, acceptance
criteria, execution permissions, or enqueue instructions.

## Deterministic Identity

`tools/raw_intent_packet.py` validates, normalizes, renders, and hashes a
manifest. Canonical JSON uses sorted keys, two-space indentation, preserved
Unicode, and one trailing newline, matching the existing Mission Packet
serialization convention.

The complete manifest participates in `intent_sha`. Changing status,
provenance, content, or `parent_intent_sha` changes the identity.

The tool does not trim or rewrite an accepted `raw_intent` value. A
whitespace-only value is rejected, but leading, trailing, internal, multiline,
and Unicode content is otherwise preserved exactly.

## Commands

```bash
python tools/raw_intent_packet.py lint \
  packets/examples/raw_intent_packet_example.json

python tools/raw_intent_packet.py compose \
  packets/examples/raw_intent_packet_example.json \
  --output-dir /tmp/raw-intent-packet
```

Compose emits:

- `manifest.json` — canonical normalized manifest.
- `intent.md` — deterministic human-readable rendering.
- `intent_sha` — SHA-256 identity.

The canonical example hash is:

```text
0d0c7657719231ad5f8d778dbe64b58f4bb26a664afaeb4ded590fb6620aa478
```

## Registry and HTTP Access

Registered revisions are stored independently from Mission Packets:

```text
packets/intents/<intent_sha>/manifest.json
packets/intents/<intent_sha>/intent.md
```

Set `CLARITY_INTENT_REGISTRY_ROOT` to override the runtime root. Registration is
append-only, atomic, and idempotent. Reads verify schema, directory identity,
and deterministic Markdown before returning a record.

Roots begin in `captured`. Child revisions require a registered parent, preserve
`raw_intent` exactly, and follow the documented lifecycle. Ancestry is returned
nearest parent first.

HTTP operations:

- `POST /intents/lint`
- `POST /intents/compose`
- `POST /intents/register`
- `GET /intents`
- `GET /intents/{intent_sha}`
- `GET /intents/{intent_sha}/ancestors`
- `POST /intents/diff`
- `POST /intents/{intent_sha}/grounding`
- `POST /intents/{intent_sha}/clarifications`
- `POST /intents/{intent_sha}/promote`
- `GET /intents/{intent_sha}/missions`

Lint and compose remain side-effect-free.

Grounding and clarification operations create child revisions. They accept
strict request shapes and cannot change original intent, provenance, human
context, constraints, or lineage directly.

The browser's **Raw Intents** workspace exposes these operations in a selected
revision's Workflow Actions panel. It can append one sourced grounding entry,
replace unresolved gaps, ask or answer one stable-ID clarification, and request
readiness. Each successful action follows the returned immutable child
revision. Terminal `promoted` and `abandoned` revisions do not expose active
mutation controls.

## Readiness

A revision may enter `ready_for_mission` only when:

- at least one structured grounding entry is a sourced `verified_fact`;
- every structured clarification is answered;
- `unresolved_gaps` is absent or empty.

The same readiness check applies to direct `/intents/register` calls. Readiness
does not imply human approval or create a Mission Packet. The browser displays
these rules as an advisory checklist; backend validation remains authoritative.

## Promotion and Mission Links

Promotion is the only Raw Intent operation that creates a Mission Packet. It
requires:

- a registered `ready_for_mission` source revision;
- no open structured clarifications or unresolved gaps;
- a PCP-lite candidate with no lint errors;
- `approval.approved: true` and non-empty caller-supplied `approved_by`;
- complete grounding references for every candidate `current_reality` and
  `constraints` entry.

Each grounding reference names a target `packet_field` and `packet_index`, plus
an `intent_field` and `intent_index`. Current Reality entries must point to
sourced `verified_fact` grounding entries. Constraint entries may point to
grounding entries, human context, captured constraints, context sources, or
answered clarification records.

Successful promotion creates or reuses three immutable records:

```text
packets/registry/<context_sha>/
packets/links/intent-missions/<intent_sha>/<context_sha>.json
packets/intents/<promoted_intent_sha>/
```

The link record is authoritative; the Mission Packet is not rewritten.
Promotion is idempotent, rejects conflicting links, verifies all records before
reporting success, and never enqueues or executes work. Set
`CLARITY_INTENT_LINK_ROOT` to override the link root.

## Current Boundary

Read-only stdio MCP access is available through:

- `list_intents_tool`
- `get_intent_tool`
- `get_intent_lineage_tool`
- `get_intent_missions_tool`
- `diff_intents_tool`

These tools delegate to the same registry and domain functions as HTTP. They do
not expose Raw Intent mutation or promotion. Authentication, external-context
proxying, browser promotion controls, and MCP mutation remain deferred. The
existing `/intents/draft` endpoint remains unchanged and continues to produce a
side-effect-free PCP-lite Mission Packet candidate.

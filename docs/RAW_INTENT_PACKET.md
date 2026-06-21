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

Lint and compose remain side-effect-free.

## Current Boundary

Read-only stdio MCP access is available through:

- `list_intents_tool`
- `get_intent_tool`
- `get_intent_lineage_tool`
- `diff_intents_tool`

These tools delegate to the same registry and domain functions as HTTP. They do
not add Raw Intent mutation, promotion into Mission Packets, intent-to-mission
link records, external-context proxying, or UI changes. The existing
`/intents/draft` endpoint remains unchanged and continues to produce a
side-effect-free PCP-lite Mission Packet candidate.

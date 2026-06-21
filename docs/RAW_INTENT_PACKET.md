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

## Current Boundary

This release provides the contract layer only. It does not add:

- Raw Intent persistence or registry APIs.
- HTTP endpoints.
- MCP tools.
- promotion into Mission Packets.
- UI changes.

The existing `/intents/draft` endpoint remains unchanged and continues to
produce a side-effect-free PCP-lite Mission Packet candidate.

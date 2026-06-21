# Tools

Deterministic contract tooling:

- `compose_packet.py` emits PCP-lite packet Markdown, normalized manifests, and
  `context_sha`.
- `lint_packet.py` validates PCP-lite manifests and reports ambiguity warnings.
- `raw_intent_packet.py` validates and composes Raw Intent Packets into
  normalized manifests, `intent.md`, and `intent_sha`.

Raw Intent Packet commands:

```bash
python tools/raw_intent_packet.py lint \
  packets/examples/raw_intent_packet_example.json
python tools/raw_intent_packet.py compose \
  packets/examples/raw_intent_packet_example.json \
  --output-dir /tmp/raw-intent-packet
```

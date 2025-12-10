# compose_packet.py in Plain English

The `tools/compose_packet.py` script is a tiny deterministic compiler that turns a JSON manifest into three predictable files you can hand to later tooling.

## What it expects
- You give it a JSON object either as a file path argument or through standard input.
- It only checks that the JSON is valid and represents an object; deeper schema validation is intentionally deferred to other stages.

## What it produces
Running `python tools/compose_packet.py <manifest>` always writes three artifacts to the current directory:
1. `manifest.json` — the same manifest, but normalized with sorted keys and pretty indentation.
2. `packet.md` — a Markdown packet that fills in the sections from `CONTEXT_PACKET_TEMPLATE.md` without changing the wording you supply.
3. `context_sha` — a SHA-256 hash of the normalized manifest so the packet can be uniquely identified.

## How it works (step by step)
1. Load the manifest (from file or stdin) and stop with an error if it is not valid JSON or not a JSON object.
2. Serialize the manifest with sorted keys to get the normalized JSON text.
3. Hash that normalized text with SHA-256 to get `context_sha`.
4. Render the Markdown sections in a fixed order, plugging in values directly from the manifest.
5. Write `manifest.json`, `packet.md`, and `context_sha` alongside your working directory.

## Example usage
```bash
python tools/compose_packet.py examples/minimal_manifest.json
```
This leaves `packet.md`, `manifest.json`, and `context_sha` next to wherever you ran the command.

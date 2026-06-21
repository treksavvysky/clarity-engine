# Packets Directory

- `packets/examples/` contains committed PCP-lite and Raw Intent examples.
- `packets/registry/<context_sha>/` contains runtime Mission Packet records and
  is ignored by git.
- `packets/intents/<intent_sha>/` contains runtime Raw Intent Packet revisions
  and is ignored by git except for `.gitkeep`.

Do not commit runtime data dumps; only include intentional fixtures or examples
aligned with the corresponding contract.

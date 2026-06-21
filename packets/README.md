# Packets Directory

- `packets/examples/` contains committed PCP-lite and Raw Intent examples.
- `packets/registry/<context_sha>/` contains runtime Mission Packet records and
  is ignored by git.
- Future Raw Intent persistence will use a separate runtime namespace; the
  current release ships only schema and deterministic composition tooling.

Do not commit runtime data dumps; only include intentional fixtures or examples aligned with `pcp_lite.schema.json`.

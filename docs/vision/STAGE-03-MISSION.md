# Stage-03 Mission — Registry & Packet Operations

## Mission
Make Context Packets **addressable, retrievable, and comparable** by introducing a filesystem-backed, content-addressed registry and packet operations (diff, lineage), while preserving determinism and the stateless runtime guarantees for compose/lint.

## Intent
Stage-02 made packets smarter and safer. Stage-03 makes them **persistent artifacts** — queryable by `context_sha`, diffable across revisions, and (optionally) linked to parent packets for lineage. This is the minimum storage surface needed before Stage-04 (JCT enqueue) can reference packets by id.

## Invariants (Must Remain True)
- **Determinism:** the same manifest still produces identical `packet_md`, normalized `manifest`, and `context_sha`.
- **Compose/lint purity:** `POST /packets/compose` and `POST /packets/lint` remain side-effect-free.
- **Contract-first:** no drift in `pcp_lite.schema.json` beyond additive optional fields (lineage).
- **CLI stability:** existing CLI tools continue to work exactly as before.

## Constraints (Stage-03)
- **Persistence is filesystem-only**, content-addressed under `packets/registry/<sha>/`.
- **No database, no auth, no outbound network calls, no secret handling.**
- Registry writes must be **idempotent** — re-registering a packet with the same `context_sha` is a no-op.
- Registry must be **append-only** at the API surface (no delete/overwrite endpoints in 03.x).
- **FastAPI** remains the only runtime framework; no new runtime deps.
- Filesystem artifacts under `packets/registry/` are **runtime state**, gitignored.

## Stage-03 Scope (What We Add)
- `app/registry.py` — thin filesystem helper: `write(sha, manifest_json, packet_md)`, `read(sha)`, `list_shas()`.
- New endpoints:
  - `POST /packets/register` — compose + persist; returns `{ context_sha, registered }`.
  - `GET /packets/{sha}` — returns `{ context_sha, manifest, packet_md }` or 404.
  - `GET /packets` — returns `{ packets: [{ context_sha, objective }] }`.
  - `POST /packets/diff` — returns a structured diff of two manifests (by sha or inline).
- Optional `parent_sha` field in schema for lineage (03.3).

## Definition of Done (Acceptance)
- `POST /packets/register` with the example manifest writes `packets/registry/<sha>/manifest.json` and `packet.md`; a second call is a no-op and returns `registered: false`.
- `GET /packets/{sha}` returns the stored manifest and rendered markdown; unknown sha returns 404.
- `GET /packets` lists all registered shas with their objective.
- `POST /packets/diff` reports added/removed/changed fields between two manifests.
- Compose and lint endpoints still produce identical results to Stage-02 (no side effects).
- All existing tests pass; new tests cover register idempotency, get-by-sha, list, and diff.
- CI remains green and offline.

## Failure Modes
Stage-03 fails if any of the following occur:
- Registry writes introduce non-determinism (timestamps in stored artifacts, ordering drift).
- `POST /packets/compose` gains a side effect on disk.
- Schema changes break existing manifests.
- CI depends on network, secrets, or mutable shared state.

## Non-Goals
- No MCP server (Stage-05).
- No JCT enqueue integration (Stage-04).
- No UI (Stage-06).
- No authentication or multi-tenant isolation.
- No packet deletion/mutation endpoints.

## Substage Gate
Proceed only with **Stage-03** (Registry & Packet Operations). No orchestration, MCP, or UI work until Stage-03 is complete and verified.

---

# Stage-03 Substages — Table of Contents

## 03.1 — Packet Registry
**Objective:** Filesystem content-addressed store under `packets/registry/<sha>/`. Add `POST /packets/register`, `GET /packets/{sha}`, `GET /packets`.
**Gate:** Example manifest registers successfully; duplicate register is a no-op; get-by-sha and list work; compose remains side-effect-free.

## 03.2 — Packet Diffing
**Objective:** `POST /packets/diff` accepts two manifests (by sha or inline) and returns a structured field-level diff.
**Gate:** Diff reports added/removed/changed keys for known manifest shapes; unchanged fields are omitted; unknown sha returns 404.

## 03.3 — Packet Versioning
**Objective:** Add optional `parent_sha` to `pcp_lite.schema.json`. Registry exposes lineage via `GET /packets/{sha}/ancestors`.
**Gate:** Manifests without `parent_sha` still validate; a registered chain A → B → C returns `[B, A]` for C's ancestors.

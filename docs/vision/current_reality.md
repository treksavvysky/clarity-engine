# Current Reality (Facts Only) — Stage-01.4

## Repository / Contract Baseline
- Stage 0 artifacts and CLI tools remain unchanged and authoritative:
  - `CONTEXT_PACKET_TEMPLATE.md`
  - `pcp_lite.schema.json`
  - `tools/compose_packet.py`
  - `tools/lint_packet.py`

## Stage-01.4 Implementation State
- A FastAPI application at `app/main.py` exposes:
  - `GET /healthz` returning `{ "status": "ok" }`.
  - `POST /packets/compose` delegating to Stage-0 compose logic.
  - `POST /packets/lint` delegating to Stage-0 lint logic and returning only `ok` and `issues`.
  - Minimal deterministic tests exercise `/healthz`, `/packets/compose`, and `/packets/lint` using the example manifest.

## Dependency / Runtime Reality
- A `requirements.txt` exists for the HTTP service dependencies and includes FastAPI, Uvicorn, and Pytest.
- Installing dependencies from `requirements.txt` succeeds in the development environment.

## Verified Execution (Observed)
- The service starts successfully via `uvicorn app.main:app --reload`.
- A request to `/healthz` returns `{ "status": "ok" }` (HTTP 200).
- `POST /packets/compose` returns deterministic `packet_md`, normalized `manifest`, and `context_sha` using Stage-0 compose functions for the example manifest.
- `POST /packets/lint` returns `{ "ok": true, "issues": [] }` for the example manifest and reports missing required fields when omitted.
- `pytest -q` runs the minimal endpoint tests in-process with FastAPI's `TestClient`.

## CI / Tests
- CI continues to run Python 3.12 and the Stage-0 packet checks.
- CI includes an import smoke check to ensure `app.main` loads without side effects.
- CI runs `pytest -q` for the minimal FastAPI endpoint coverage alongside Stage-0 packet tooling checks.

## Service Properties
- The service remains stateless: no persistence, authentication, outbound network calls, or UI components are present.

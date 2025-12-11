# Current Reality (Facts Only) — Stage-01.2

- Stage 0 artifacts and CLI tools (`CONTEXT_PACKET_TEMPLATE.md`, `pcp_lite.schema.json`, `tools/compose_packet.py`, `tools/lint_packet.py`) remain unchanged and authoritative.
- Stage-01.2 extends the FastAPI application at `app/main.py` with a `/packets/compose` endpoint that reuses the Stage-0 compose logic to return `packet_md`, normalized `manifest`, and `context_sha`.
- The `/healthz` endpoint continues to return `{ "status": "ok" }` and acts as a lightweight health check.
- Dependency management uses `requirements.txt` (FastAPI + Uvicorn) to support running the app locally; these dependencies install cleanly in the dev environment.
- The FastAPI app starts under Uvicorn and responds with deterministic payloads for both `/healthz` and `/packets/compose`.
- CI still runs Python 3.12 and Stage-0 packet checks, with an added import check to ensure the FastAPI app loads without side effects.
- The service is stateless: no persistence, authentication, outbound network calls, or UI components are present.
- The pytest suite (covering `/healthz`, packet tools, and the compose endpoint) currently passes.

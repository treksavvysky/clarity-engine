# Current Reality (Facts Only) — Stage-01.1

- Stage 0 artifacts and CLI tools (`CONTEXT_PACKET_TEMPLATE.md`, `pcp_lite.schema.json`, `tools/compose_packet.py`, `tools/lint_packet.py`) remain unchanged and authoritative.
- Stage-01.1 introduces a minimal FastAPI application at `app/main.py` with a single `/healthz` endpoint returning `{ "status": "ok" }`.
- Dependency management now uses `requirements.txt` (FastAPI + Uvicorn) to support running the app locally.
- CI still runs Python 3.12 and Stage-0 packet checks, with an added import check to ensure the FastAPI app loads without side effects.
- The service is stateless: no persistence, authentication, outbound network calls, or UI components are present.

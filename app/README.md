# App Directory (Stage-01.3)

The backend runtime hosts a FastAPI application that exposes deterministic
transport adapters over the Stage-0 packet tools:
- `GET /healthz`
- `POST /packets/compose`
- `POST /packets/lint`

## Run locally
1. Install dependencies from the repository root:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server with auto-reload:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Verify health:
   ```bash
   curl -s http://127.0.0.1:8000/healthz
   # {"status": "ok"}
   ```

Keep imports side-effect free; no persistence, auth, or outbound calls are
permitted in this stage.

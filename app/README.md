# App Directory (Stage-01.1)

The backend runtime now hosts a minimal FastAPI application that exposes a
single health endpoint. This establishes the HTTP boundary without changing
any Stage-0 contract artifacts.

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

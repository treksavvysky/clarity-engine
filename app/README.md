# App Directory

The backend runtime hosts FastAPI transport adapters over shared deterministic
Mission Packet and Raw Intent Packet modules.

Core operations include:
- `GET /healthz`
- `POST /packets/compose`
- `POST /packets/lint`
- `POST /packets/register`, list/get/ancestors/diff/enqueue
- `POST /intents/draft` for the legacy direct Mission Packet draft flow
- `POST /intents/lint`, `/intents/compose`, and `/intents/register`
- `GET /intents`, `/intents/{intent_sha}`, and ancestry
- `POST /intents/diff`

`app/registry.py` stores Mission Packets. `app/intent_registry.py` independently
stores immutable Raw Intent Packet revisions and enforces lifecycle lineage.

`app/mcp_server.py` exposes 12 stdio tools: eight existing Mission Packet tools
and four read-only Raw Intent tools (`list_intents_tool`, `get_intent_tool`,
`get_intent_lineage_tool`, `diff_intents_tool`). Raw Intent mutation and
promotion are not exposed through MCP.

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

Keep imports side-effect free. Persistence is local filesystem-only. No
authentication, database, background worker, or outbound network behavior is
present.

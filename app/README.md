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
- `POST /intents/{intent_sha}/grounding`
- `POST /intents/{intent_sha}/clarifications`
- `POST /intents/{intent_sha}/promote`
- `GET /intents/{intent_sha}/missions`
- `POST /proposals/lint`, `/proposals/compose`, and `/proposals/register`
- `GET /proposals` and `/proposals/{proposal_sha}`

`app/registry.py` stores Mission Packets. `app/intent_registry.py` independently
stores immutable Raw Intent Packet revisions and enforces lifecycle lineage.
`app/intent_workflow.py` builds immutable grounding and clarification revisions
and centralizes `ready_for_mission` checks.
`app/intent_promotion.py` validates approved Mission Packet candidates and
coordinates retry-safe registration. `app/intent_links.py` stores and verifies
authoritative append-only associations.
`app/proposal_registry.py` independently stores immutable Agent Refinement
Proposals bound to verified Raw Intent revisions.

`app/mcp_server.py` exposes 18 stdio tools: eight existing Mission Packet tools
and five read-only Raw Intent tools (`list_intents_tool`, `get_intent_tool`,
`get_intent_lineage_tool`, `get_intent_missions_tool`, `diff_intents_tool`), plus
five proposal tools for lint, compose, register, list, and get. Proposal
registration does not mutate Raw Intents.

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

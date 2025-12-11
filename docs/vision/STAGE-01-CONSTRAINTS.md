Universal Stage-01 constraints (apply to every Stage-01.x):
	•	Must not modify: CONTEXT_PACKET_TEMPLATE.md, pcp_lite.schema.json
	•	Must not break/change behavior of: tools/compose_packet.py, tools/lint_packet.py
	•	Must not introduce: auth, persistence/DB, UI, MCP server, secrets handling, outbound network calls
	•	Service must remain stateless
	•	FastAPI is the only new runtime framework allowed
	•	Preserve determinism and contract semantics (no semantic drift)

# Clarity Engine

Clarity Engine is intent and context infrastructure: it standardizes how we generate clear, testable Context Packets for human–AI and agentic workflows so work stays aligned and auditable.

## Project Identity (Stage-01.1)
- **Mission:** Provide repeatable Context Packets that remove ambiguity for coding agents while preserving the broader intent/context infrastructure vision.
- **Current Stage:** Stage-01.1 — Stage 0 artifacts remain frozen, and a minimal FastAPI boundary now exposes a `/healthz` endpoint.
- **Out of Scope (now):** No additional HTTP endpoints, authentication, persistence, orchestration, UI implementation, or network-dependent behaviors.
- **Active stack:** Python 3.12 + FastAPI (+ Uvicorn for local serving) alongside the Stage-0 packet tools.

## Authoritative Artifacts
These files define how the project operates and must stay in sync.
- `AGENTS.md`: Operating guide and constraints for agents contributing to the repo (includes Stage-01 reference instructions).
- `CONTEXT_PACKET_TEMPLATE.md`: Paste-ready Context Packet template aligned with the schema.
- `pcp_lite.schema.json`: Machine-readable contract for packet manifests.
- `packets/examples/context_packet_example.json`: Minimal manifest example that conforms to the PCP-lite schema.
- `.github/workflows/ci.yml`: CI pipeline covering tests, packet checks, and FastAPI import verification.

## Repository Structure
```
clarity-engine/
├── AGENTS.md                       # Rules for code agents
├── CONTEXT_PACKET_TEMPLATE.md      # Paste-ready prompt skeleton
├── pcp_lite.schema.json            # PCP-lite manifest contract
├── requirements.txt                # Runtime deps (FastAPI + Uvicorn)
├── README.md                       # Project overview and current stage scope
├── docs/                           # Documentation set, including vision and stage summaries
├── tools/                          # Packet compose/lint tools (Stage-0 contract)
│   └── compose_packet.py           # Deterministically emits packet.md, manifest.json, and context_sha
├── packets/                        # Reserved: generated packet artifacts and examples
├── app/                            # FastAPI entrypoint with /healthz
├── ui/                             # Reserved: future UI (no implementation yet)
└── .github/workflows/ci.yml        # CI pipeline for packet tools and runtime import checks
```

Stage-0 contract files (`CONTEXT_PACKET_TEMPLATE.md`, `pcp_lite.schema.json`, `tools/compose_packet.py`, `tools/lint_packet.py`) remain unchanged and authoritative during Stage-01.1.

## How to Run the FastAPI App
1. Install dependencies from the repository root:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Check health locally:
   ```bash
   curl -s http://127.0.0.1:8000/healthz
   # {"status": "ok"}
   ```

## How to Work With Context Packets (Stage 0 artifacts)
1. Start from `CONTEXT_PACKET_TEMPLATE.md` when drafting packets for tasks.
2. Use `pcp_lite.schema.json` as the contract for any machine-readable manifests.
3. Keep template, schema, and any packet artifacts consistent; schema changes require template updates (and vice versa).

CLI tools for composition and linting live under `tools/`. Use `python tools/compose_packet.py <manifest.json>` to emit a packet markdown, normalized manifest, and context hash. Run `python tools/lint_packet.py <manifest.json>` to validate manifests against the PCP-lite schema and required content sections before composing.

## Continuous Integration
- CI runs on every push and pull request via [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- Checks ensure Python 3.12 setup, run the unit test suite, lint the example manifest at `packets/examples/context_packet_example.json`, compose a packet from the same manifest, and verify `app.main:app` imports cleanly.

## Further context
Deeper mission, architecture, and planned runtime surfaces are captured in `docs/vision/`:
- `docs/vision/mission.md`
- `docs/vision/architecture.md`
- `docs/vision/STAGE-01-MISSION.md`
- `docs/vision/STAGE-01-SUMMARY.md`
- `docs/vision/current_reality.md`

## Current Constraints
- No authentication or multi-user persistence.
- No orchestration, sandbox execution, additional MCP endpoints, or network-dependent behaviors beyond the health check.
- UI runtime remains dormant.

## Planned Technical Posture (for later stages)
- **Backend (future):** Python 3.12, FastAPI, MCP Server SDK, Pydantic.
- **Frontend (future):** Vite, React, TypeScript, Tailwind, Radix, Zod.

These stacks beyond the health check are not yet enabled; they anchor expectations for future development.

## License
Apache License 2.0 (see `LICENSE`).

## Contact
Maintained by **@treksavvy**; contributions should respect Stage-01.1 boundaries.

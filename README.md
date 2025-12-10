# Clarity Engine

Clarity Engine is intent and context infrastructure: it standardizes how we generate clear, testable Context Packets for human–AI and agentic workflows so work stays aligned and auditable.

## Project Identity (Stage 0)
- **Mission:** Provide repeatable Context Packets that remove ambiguity for coding agents while preserving the broader intent/context infrastructure vision.
- **Current Stage:** Stage 0 — repository initialization, contracts, and directory skeleton; the core artifact is the Context Packet produced from the shared template and schema.
- **Out of Scope (now):** No runtime services, no MCP server, no FastAPI endpoints, no UI implementation, and no network- or secret-dependent behaviors.
- **Future stack (not implemented):** FastAPI + MCP backend, packet registry, and a small Next.js-style UI are planned but explicitly dormant in this stage.

## Authoritative Artifacts
These files define how the project operates and must stay in sync.
- `AGENTS.md`: Operating guide and constraints for agents contributing to the repo.
- `CONTEXT_PACKET_TEMPLATE.md`: Paste-ready Context Packet template aligned with the schema.
- `pcp_lite.schema.json`: Machine-readable contract for packet manifests.
- `packets/examples/context_packet_example.json`: Minimal manifest example that conforms to the PCP-lite schema.
- `.github/workflows/ci.yml`: Baseline CI placeholder for Stage 0.

## Repository Structure
```
clarity-engine/
├── AGENTS.md                       # Rules for code agents
├── CONTEXT_PACKET_TEMPLATE.md      # Paste-ready prompt skeleton
├── pcp_lite.schema.json            # PCP-lite manifest contract
├── README.md                       # Project overview and Stage 0 scope
├── tools/                          # Packet compose/lint tools
│   └── compose_packet.py           # Deterministically emits packet.md, manifest.json, and context_sha
├── packets/                        # Reserved: generated packet artifacts
├── app/                            # Reserved: future backend runtime (no services in Stage 0)
├── ui/                             # Reserved: future UI (no implementation in Stage 0)
└── .github/workflows/ci.yml        # CI placeholder aligned to Stage 0
```

Stage 0 keeps these directories present but intentionally minimal; do not add runtime code yet.

## How to Work With Context Packets (Stage 0)
1. Start from `CONTEXT_PACKET_TEMPLATE.md` when drafting packets for tasks.
2. Use `pcp_lite.schema.json` as the contract for any machine-readable manifests.
3. Keep template, schema, and any packet artifacts consistent; schema changes require template updates (and vice versa).

CLI tools for composition and linting live under `tools/`. Use `python tools/compose_packet.py <manifest.json>` to emit a packet markdown, normalized manifest, and context hash.

## Further context (not required for Stage 0)
Deeper mission, architecture, and planned runtime surfaces are captured in `docs/vision/`:
- `docs/vision/mission.md`
- `docs/vision/architecture.md`

## Stage 0 Non-Goals
- No authentication or multi-user persistence.
- No orchestration, sandbox execution, MCP endpoints, or FastAPI services.
- No UI runtime or build pipeline.

## Planned Technical Posture (for later stages)
- **Backend (future):** Python 3.12, FastAPI, MCP Server SDK, Pydantic.
- **Frontend (future):** Vite, React, TypeScript, Tailwind, Radix, Zod.

These stacks are not enabled in Stage 0; they are listed to anchor expectations for future development.

## License
Apache License 2.0 (see `LICENSE`).

## Contact
Maintained by **@treksavvy**; contributions should respect Stage 0 boundaries.

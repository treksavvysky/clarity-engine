# clarity-engine
context-engineering service

# Clarity Engine

**Clarity Engine** is a lightweight context-engineering service for producing clear, testable, and repeatable intent packets for human–AI and agentic workflows.

It generates structured **Context Packets** that define:
- mission,
- current reality (facts only),
- constraints,
- acceptance criteria,
- required artifacts,
- and failure modes  
so coding agents (Claude, Codex, etc.) can plan and execute with minimal ambiguity.

This project is designed as **intent infrastructure**: simple tools first, orchestration later.

---

## Core Workflow

1. **Compose** a structured context manifest (JSON or form input)
2. **Lint** the manifest for completeness and ambiguity
3. **Emit**:
   - a paste-ready Markdown Context Packet
   - a machine-readable manifest
   - a `context_sha` digest for traceability
4. **Paste** into Claude / Codex for execution

Later stages will allow these packets to be stamped into execution traces.

---

## Stage 0 Scope (Current)

Stage 0 is focused on **project bootstrapping and contracts**, not full orchestration.

Included:
- Repo structure + documentation
- Agent operating rules (`AGENTS.md`)
- Context packet template
- PCP-lite schema for manifests
- Deterministic CLI tools for:
  - packet composition
  - packet linting

Explicitly NOT included yet:
- Authentication
- Multi-user persistence
- Network or secret-using tools
- Sandbox execution
- JCT or runtime orchestration

---

## Tech Stack (Initial)

**Backend**
- Python 3.12
- FastAPI
- MCP Server (Python SDK)
- Pydantic

**Frontend (Optional in Stage 0)**
- Vite
- React
- TypeScript
- Tailwind + Radix
- Zod

All semantics live in the backend. The UI is a thin client.

---

## Repo Map (Planned)
clarity-engine/
├── AGENTS.md                      # Rules for code agents
├── CONTEXT_PACKET_TEMPLATE.md    # Paste-ready prompt skeleton
├── pcp_lite.schema.json          # Machine contract for context manifests
├── tools/
│   ├── compose_packet.py         # Deterministic packet compiler
│   └── lint_packet.py            # Packet validator
├── packets/                      # Generated packet artifacts
├── app/                          # FastAPI + MCP server
├── ui/                           # Optional Vite/React frontend
└── .github/workflows/ci.yml      # CI baseline

---

## Design Principles

- **Artifacts over vibes** — every action leaves a durable record.
- **Testable progress** — each stage produces verifiable outputs.
- **Simple tools first** — orchestration is layered later.
- **Stateless agents, stateful systems** — agents reset, packets persist.
- **Constraints before cleverness** — guardrails define the search space.

---

## License

TBD (MIT or Apache-2.0 recommended for tooling reuse)

---

## Author

GitHub: **@treksavvy**

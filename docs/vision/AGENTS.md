# AGENTS.md — docs/vision (Vision + Reality Artifacts Contract)

## Purpose
This folder contains **human-readable governance artifacts** for Clarity Engine stages (missions, substages, current reality, acceptance, and constraints). These documents exist to keep development aligned and to prevent scope drift.

## How to Use `current_reality.md`
`current_reality.md` is a **facts-only snapshot** of what is true *right now* for the active stage/substage.

### Hard Rules (Do Not Violate)
- Write **only verifiable facts**. No goals, no plans, no predictions.
- Every statement must be **provable** by one of:
  - repository contents (files, paths, code),
  - deterministic commands (documented below),
  - CI configuration and results.
- If a claim cannot be verified immediately, **omit it** or move it into another doc (e.g., Work Plan).

### Required Structure
`current_reality.md` must be organized under these headings:
- Repository / Contract Baseline
- Implementation State
- Dependency / Runtime Reality
- Verified Execution (Observed)
- CI / Tests
- Service Properties

### Verification Commands (Preferred Evidence)
When stating runtime/test claims, ensure they are true under these commands:
- `pip install -r requirements.txt`
- `python -c "from app.main import app"`
- `uvicorn app.main:app --reload`
- `curl -s http://127.0.0.1:8000/healthz`
- `pytest -q`

If the claim is based on CI, it must align with `.github/workflows/ci.yml`.

## Scope / Intent
- This folder may be updated freely to reflect current stage status and decisions.
- **Do not** change Stage-0 contract artifacts (`CONTEXT_PACKET_TEMPLATE.md`, `pcp_lite.schema.json`) based on anything in `docs/vision/`.
- `docs/vision/` documents describe and constrain the system; they do not redefine the packet contract.

## Style
- Be concise, specific, and literal.
- Prefer file paths and exact endpoint names.
- Avoid adjectives like “cleanly” unless the meaning is made concrete by a command/result.

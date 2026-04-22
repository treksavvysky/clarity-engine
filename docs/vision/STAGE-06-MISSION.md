# Stage-06 Mission — UI

## Mission
Provide a **minimal browser UI** for humans to browse, compare, and edit Context Packets — served directly by FastAPI with no build step, no npm, no Node toolchain.

## Intent
The architecture doc calls for an eventual Next.js front. That remains the long-term aspiration. Stage-06 delivers the same three capabilities (browser, diff, editor) as a **single static HTML file** so the project stays lean and CI stays offline. The future Next.js app can replace `ui/index.html` without any backend changes.

## Invariants (Must Remain True)
- **No Node/npm toolchain.** UI is static HTML + vanilla JS + a small CSS block.
- **No new runtime deps.** FastAPI already supports `StaticFiles`.
- **API-first:** the UI uses existing HTTP endpoints — no UI-specific routes that duplicate logic.
- **Offline:** no CDN imports, no external fonts.

## Constraints (Stage-06)
- One `ui/index.html` file, served at `/` and `/ui/`.
- Single-page, tabbed interface. No routing library.
- All state lives in the DOM; no persistence outside the registry.

## Stage-06 Scope (What We Add)
- `GET /` — serves `ui/index.html`.
- `GET /ui/*` — serves static assets from `ui/`.
- `ui/index.html` with three tabs: **Browser**, **Diff**, **Editor**.

## Definition of Done (Acceptance)
- Navigating to the service root in a browser loads the UI.
- Browser tab lists registered packets and shows detail on click.
- Diff tab accepts two shas (or inline manifests) and renders added/removed/changed fields.
- Editor tab accepts a JSON manifest and offers Lint / Compose / Register / Enqueue actions, rendering the response.
- No build step. No Node. No new Python deps.

## Failure Modes
Stage-06 fails if any of the following occur:
- The UI requires a build step or Node runtime.
- External network resources (fonts, CDNs) are required to render.
- UI-specific API endpoints are added that duplicate existing logic.

## Non-Goals
- No authentication or user accounts.
- No Next.js / React framework (deferred; architectural aspiration).
- No live-reload dev server beyond what uvicorn provides.

## Substage Gate
Proceed only with Stage-06 until verified.

---

# Stage-06 Substages

## 06.1 — Packet Browser
**Objective:** Serve `ui/index.html` at `/` with a Browser tab listing registered packets and showing their manifest + rendered markdown.
**Gate:** Hitting `/` in a browser lists packets; clicking one shows detail.

## 06.2 — Diff Viewer
**Objective:** Add a Diff tab that calls `POST /packets/diff` with two sha or inline-manifest inputs and renders the result.
**Gate:** Diff tab produces the same `{added, removed, changed}` output as the API.

## 06.3 — Manifest Editor
**Objective:** Add an Editor tab with a JSON textarea and buttons for Lint, Compose, Register, Enqueue; renders the JSON response.
**Gate:** All four actions round-trip for the golden example manifest.

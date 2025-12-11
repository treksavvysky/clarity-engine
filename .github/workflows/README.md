# GitHub Workflows

Workflow definitions live here. The Stage-01.1 CI pipeline installs Python 3.12, runs unit tests (including the FastAPI health check), verifies `app.main:app` imports, lints the example manifest, and composes a packet from it.

Add or adjust workflows when new tooling or stages introduce additional checks; keep jobs network-free and deterministic.

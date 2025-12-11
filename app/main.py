"""Minimal FastAPI application for Clarity Engine Stage-01.1.

The service is intentionally minimal: a single health endpoint to
establish the HTTP boundary without altering Stage-0 semantics.
"""

from fastapi import FastAPI

app = FastAPI(title="Clarity Engine", version="0.1.0", docs_url=None, redoc_url=None)


@app.get("/healthz")
def read_health() -> dict[str, str]:
    """Return a simple status payload for health checks."""

    return {"status": "ok"}

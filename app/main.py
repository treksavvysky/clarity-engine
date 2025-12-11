"""FastAPI application for Clarity Engine Stage-01.2."""

import json
from typing import Any

from fastapi import FastAPI, HTTPException

from tools import compose_packet

app = FastAPI(title="Clarity Engine", version="0.1.0", docs_url=None, redoc_url=None)


@app.get("/healthz")
def read_health() -> dict[str, str]:
    """Return a simple status payload for health checks."""

    return {"status": "ok"}


@app.post("/packets/compose")
def compose_packet_endpoint(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compose a Context Packet using the Stage-0 compose logic.

    The endpoint reuses the deterministic Stage-0 compose functions to avoid
    semantic drift. It returns the rendered packet markdown, normalized
    manifest object, and context SHA.
    """

    if not isinstance(manifest, dict):
        raise HTTPException(status_code=400, detail="Manifest must be a JSON object.")

    normalized_manifest = compose_packet.normalize_manifest(manifest)
    packet_md = compose_packet.render_packet_md(manifest) + "\n"
    context_sha = compose_packet.compute_context_sha(normalized_manifest)

    return {
        "packet_md": packet_md,
        "manifest": json.loads(normalized_manifest),
        "context_sha": context_sha,
    }

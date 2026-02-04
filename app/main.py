"""FastAPI application for Clarity Engine."""

import json
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from tools import compose_packet, lint_packet

app = FastAPI(
    title="Clarity Engine",
    version="0.2.0",
    description=(
        "Intent-to-packet compiler for AI agents. "
        "Transforms human intent into standardized, testable Context Packets "
        "that agents can execute without ambiguity. "
        "Use /packets/compose to generate packets and /packets/lint to validate manifests."
    ),
    openapi_tags=[
        {
            "name": "packets",
            "description": "Compose and validate Context Packet manifests.",
        },
        {
            "name": "health",
            "description": "Service health checks.",
        },
    ],
    openapi_url=None,  # Disable default, we provide custom endpoint
)

LINT_SCHEMA = lint_packet.load_schema()


@app.get(
    "/openapi.json",
    tags=["health"],
    include_in_schema=False,
)
def get_openapi_schema(
    server: str | None = Query(
        default=None,
        description="Server URL to include in the OpenAPI schema (e.g., https://your-host.com)",
    ),
) -> JSONResponse:
    """Return OpenAPI schema with optional server URL for GPT Actions."""
    schema = app.openapi()
    if server:
        schema["servers"] = [{"url": server}]
    return JSONResponse(content=schema)


@app.get(
    "/healthz",
    tags=["health"],
    summary="Check service health",
    description="Returns a simple status payload. Use this to verify the service is running.",
)
def read_health() -> dict[str, str]:
    """Return a simple status payload for health checks."""
    return {"status": "ok"}


@app.post(
    "/packets/compose",
    tags=["packets"],
    summary="Compose a Context Packet from a manifest",
    description=(
        "Takes a JSON manifest with mission, constraints, acceptance criteria, and other fields. "
        "Returns the rendered packet as markdown, the normalized manifest, and a deterministic "
        "content hash (context_sha) that uniquely identifies this packet. "
        "The same input always produces the same output."
    ),
)
def compose_packet_endpoint(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compose a Context Packet using deterministic logic.

    Returns packet_md (markdown), manifest (normalized JSON), and context_sha (hash).
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


@app.post(
    "/packets/lint",
    tags=["packets"],
    summary="Validate a Context Packet manifest",
    description=(
        "Checks a manifest against the PCP-lite schema and content rules. "
        "Returns ok=true if valid (no errors), or ok=false with errors. "
        "Warnings about vague language or untestable criteria are included "
        "but do not cause ok=false. Use this before composing to catch problems early."
    ),
)
def lint_packet_endpoint(manifest: Any = Body(...)) -> dict[str, Any]:
    """Lint a Context Packet manifest. Returns ok (bool), errors, and warnings."""
    issues = lint_packet.lint_manifest(manifest, LINT_SCHEMA)
    errors = [i for i in issues if not i.startswith("[warning]")]
    warnings = [i for i in issues if i.startswith("[warning]")]
    return {"ok": not errors, "errors": errors, "warnings": warnings}

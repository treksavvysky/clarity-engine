"""FastAPI application for Clarity Engine."""

import json
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app import registry
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


@app.post(
    "/packets/register",
    tags=["packets"],
    summary="Compose and persist a Context Packet",
    description=(
        "Composes the manifest and writes the resulting packet to the content-addressed "
        "registry under packets/registry/<context_sha>/. Idempotent: a second call with "
        "the same manifest returns registered=false and does not rewrite files."
    ),
)
def register_packet_endpoint(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compose and persist a packet. Returns context_sha and registered (bool)."""
    if not isinstance(manifest, dict):
        raise HTTPException(status_code=400, detail="Manifest must be a JSON object.")

    normalized_manifest = compose_packet.normalize_manifest(manifest)
    packet_md = compose_packet.render_packet_md(manifest) + "\n"
    context_sha = compose_packet.compute_context_sha(normalized_manifest)

    registered = registry.write(context_sha, normalized_manifest, packet_md)
    return {"context_sha": context_sha, "registered": registered}


@app.get(
    "/packets",
    tags=["packets"],
    summary="List registered Context Packets",
    description="Returns all packets currently in the registry with their context_sha and mission.",
)
def list_packets_endpoint() -> dict[str, Any]:
    """Return all registered packets as {context_sha, mission} entries."""
    entries = []
    for sha in registry.list_shas():
        record = registry.read(sha)
        if record is None:
            continue
        mission = record["manifest"].get("mission", "")
        entries.append({"context_sha": sha, "mission": mission})
    return {"packets": entries}


@app.get(
    "/packets/{sha}",
    tags=["packets"],
    summary="Retrieve a registered Context Packet",
    description="Returns the stored manifest and rendered markdown for the given context_sha.",
)
def get_packet_endpoint(sha: str) -> dict[str, Any]:
    """Return a registered packet or 404 if sha is unknown."""
    record = registry.read(sha)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Packet {sha} not found.")
    return {
        "context_sha": sha,
        "manifest": record["manifest"],
        "packet_md": record["packet_md"],
    }

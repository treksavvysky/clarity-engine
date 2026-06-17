"""FastAPI application for Clarity Engine."""

import json
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import registry
from tools import compose_packet, lint_packet

UI_DIR = Path(__file__).resolve().parent.parent / "ui"

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
            "name": "intents",
            "description": "Draft Context Packet manifests from raw human intent.",
        },
        {
            "name": "health",
            "description": "Service health checks.",
        },
    ],
    openapi_url=None,  # Disable default, we provide custom endpoint
)

LINT_SCHEMA = lint_packet.load_schema()


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail=f"'{field}' must be a non-empty string.")
    return value.strip()


def _optional_string_list(body: dict[str, Any], field: str) -> list[str]:
    value = body.get(field, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise HTTPException(status_code=400, detail=f"'{field}' must be a list of strings.")

    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise HTTPException(
                status_code=400,
                detail=f"'{field}' entry at index {index} must be a non-empty string.",
            )
        items.append(item.strip())
    return items


def _draft_smallest_next_action(raw_intent: str) -> str:
    normalized = raw_intent.strip().rstrip(".")
    lowered = normalized.lower()
    prefix = "i should work on "
    if lowered.startswith(prefix):
        target = normalized[len(prefix):].strip()
        if target:
            return (
                f"Create a short inventory note for {target} that records current state, "
                "access path, known constraint, and first improvement target."
            )
    return (
        "Create a short intent inventory note that records current state, known constraint, "
        "and first improvement target."
    )


def _draft_manifest_from_intent(body: dict[str, Any]) -> dict[str, Any]:
    raw_intent = _require_non_empty_string(body.get("raw_intent"), "raw_intent")
    context = _optional_string_list(body, "context")
    constraints = _optional_string_list(body, "constraints")
    route = _optional_string_list(body, "route")

    next_action = _draft_smallest_next_action(raw_intent)
    route_text = " -> ".join(route) if route else "Clarity Engine"
    current_reality = [
        f"Raw intent received: {raw_intent}",
        "The intent needs clarification before agent execution.",
    ]
    current_reality.extend(f"Caller supplied context: {item}" for item in context)

    manifest_constraints = [
        "Do not execute the work yet.",
        "Do not register the packet until the draft is reviewed.",
        "Convert only one raw intent into one mission packet draft.",
    ]
    manifest_constraints.extend(constraints)
    manifest_constraints.append(f"Route through: {route_text}.")

    return {
        "project": "Clarity Engine",
        "stage": "Stage-07",
        "substage": "raw-intent-draft",
        "version": "1.0.0",
        "mission": "Clarify one raw human intent into the smallest executable mission packet draft.",
        "current_reality": current_reality,
        "constraints": manifest_constraints,
        "acceptance": [
            "Create one draft mission packet from the provided raw intent.",
            "Include the smallest concrete next action for the clarified mission.",
            "Return a PCP-lite manifest that passes lint without errors.",
            "Exclude registry writes until a human or agent approves the draft.",
        ],
        "required_artifacts": [
            "Returned draft PCP-lite manifest for review.",
            f"Smallest next action: {next_action}",
        ],
        "failure_modes": [
            "The draft stays abstract and does not name a smallest next action.",
            "The draft expands into execution, platform building, or workflow automation.",
            "The draft bypasses review and writes directly to the packet registry.",
        ],
        "substage_gate": [
            "In-scope: draft one mission packet from one raw intent.",
            "Out-of-scope: registering packets, executing tasks, adding UI, or automating workflows.",
        ],
        "notes": [
            f"Raw intent: {raw_intent}",
            f"Suggested route: {route_text}.",
            f"Smallest next action: {next_action}",
        ],
        "risk_flags": ["missing_info"],
        "allowed_actions": ["filesystem_read"],
        "evidence_requirements": ["api_response"],
    }


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


@app.get("/", include_in_schema=False)
def serve_ui_root() -> FileResponse:
    """Serve the UI entry point."""
    return FileResponse(UI_DIR / "index.html")


app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


@app.post(
    "/intents/draft",
    tags=["intents"],
    summary="Draft a Context Packet manifest from raw intent",
    description=(
        "Accepts one raw human intent plus optional context, constraints, and route. "
        "Returns a deterministic PCP-lite manifest draft with lint results and a rendered preview. "
        "This endpoint is side-effect-free: it does not register or enqueue the draft."
    ),
)
def draft_intent_endpoint(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Draft a PCP-lite manifest from one raw intent without registry side effects."""
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")

    manifest = _draft_manifest_from_intent(body)
    issues = lint_packet.lint_manifest(manifest, LINT_SCHEMA)
    errors = [i for i in issues if not i.startswith("[warning]")]
    warnings = [i for i in issues if i.startswith("[warning]")]
    normalized_manifest = compose_packet.normalize_manifest(manifest)
    packet_md = compose_packet.render_packet_md(manifest) + "\n"
    context_sha = compose_packet.compute_context_sha(normalized_manifest)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "manifest": json.loads(normalized_manifest),
        "packet_md": packet_md,
        "context_sha": context_sha,
        "registered": False,
    }


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


@app.get(
    "/packets/{sha}/ancestors",
    tags=["packets"],
    summary="Retrieve packet lineage via parent_sha",
    description=(
        "Walks the parent_sha chain starting from the given packet and returns the ancestor shas "
        "in order from nearest parent to oldest ancestor. Stops at the first packet with no "
        "parent_sha or whose parent is not in the registry."
    ),
)
def get_ancestors_endpoint(sha: str) -> dict[str, Any]:
    """Return the ancestor chain for a registered packet."""
    record = registry.read(sha)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Packet {sha} not found.")
    ancestors: list[str] = []
    seen = {sha}
    current = record["manifest"].get("parent_sha")
    while current and current not in seen:
        seen.add(current)
        ancestors.append(current)
        parent_record = registry.read(current)
        if parent_record is None:
            break
        current = parent_record["manifest"].get("parent_sha")
    return {"context_sha": sha, "ancestors": ancestors}


def _resolve_side(value: Any, side: str) -> dict:
    """Accept a sha string or inline manifest dict; return the manifest."""
    if isinstance(value, str):
        record = registry.read(value)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Packet {value} not found ({side}).")
        return record["manifest"]
    if isinstance(value, dict):
        return value
    raise HTTPException(
        status_code=400,
        detail=f"'{side}' must be a context_sha string or an inline manifest object.",
    )


def _diff_manifests(left: dict, right: dict) -> dict[str, Any]:
    """Field-level diff of two manifests. Returns added/removed/changed."""
    left_keys = set(left)
    right_keys = set(right)
    added = {k: right[k] for k in sorted(right_keys - left_keys)}
    removed = {k: left[k] for k in sorted(left_keys - right_keys)}
    changed = {
        k: {"before": left[k], "after": right[k]}
        for k in sorted(left_keys & right_keys)
        if left[k] != right[k]
    }
    return {"added": added, "removed": removed, "changed": changed}


@app.post(
    "/packets/enqueue",
    tags=["packets"],
    summary="Compose, register, and return a JCT-ready envelope",
    description=(
        "Composes the manifest, persists it to the registry, and returns an envelope "
        "suitable for hand-off to a JCT-like orchestrator. task_id equals context_sha. "
        "Idempotent: a second call returns registered=false but the same envelope. "
        "Clarity Engine never calls callback_url — it is transport-only data."
    ),
)
def enqueue_packet_endpoint(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compose + register + return JCT envelope. Deterministic for the same manifest."""
    if not isinstance(manifest, dict):
        raise HTTPException(status_code=400, detail="Manifest must be a JSON object.")

    normalized_manifest = compose_packet.normalize_manifest(manifest)
    packet_md = compose_packet.render_packet_md(manifest) + "\n"
    context_sha = compose_packet.compute_context_sha(normalized_manifest)
    registered = registry.write(context_sha, normalized_manifest, packet_md)
    normalized = json.loads(normalized_manifest)

    return {
        "task_id": context_sha,
        "context_sha": context_sha,
        "mission": normalized.get("mission", ""),
        "manifest": normalized,
        "packet_md": packet_md,
        "allowed_actions": normalized.get("allowed_actions", []),
        "evidence_requirements": normalized.get("evidence_requirements", []),
        "risk_flags": normalized.get("risk_flags", []),
        "callback_url": normalized.get("callback_url"),
        "registered": registered,
    }


@app.post(
    "/packets/diff",
    tags=["packets"],
    summary="Diff two Context Packets",
    description=(
        "Compares two manifests and returns field-level differences. "
        "Each side ('left', 'right') is either a context_sha string (looked up in the registry) "
        "or an inline manifest object. Response has added/removed/changed keys with only differing fields."
    ),
)
def diff_packets_endpoint(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Return {added, removed, changed} for two manifests."""
    if not isinstance(body, dict) or "left" not in body or "right" not in body:
        raise HTTPException(
            status_code=400,
            detail="Request body must include 'left' and 'right'.",
        )
    left = _resolve_side(body["left"], "left")
    right = _resolve_side(body["right"], "right")
    return _diff_manifests(left, right)

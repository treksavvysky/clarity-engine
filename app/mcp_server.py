"""Clarity Engine MCP server.

Exposes compose/lint/registry/diff/enqueue/permission operations as MCP tools
over stdio. All tool handlers delegate to the same modules the FastAPI
endpoints use — no business logic is reimplemented here.

Run with:
    python -m app.mcp_server
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from app import registry
from tools import compose_packet, lint_packet

mcp = FastMCP(
    "clarity-engine",
    instructions=(
        "Clarity Engine MCP tools: compose, lint, register, retrieve, diff, "
        "enqueue, and permission-check Context Packets. All operations are "
        "deterministic; register/enqueue persist to packets/registry/."
    ),
)

_SCHEMA = lint_packet.load_schema()


def _compose(manifest: dict) -> dict:
    normalized = compose_packet.normalize_manifest(manifest)
    packet_md = compose_packet.render_packet_md(manifest) + "\n"
    context_sha = compose_packet.compute_context_sha(normalized)
    return {
        "packet_md": packet_md,
        "manifest": json.loads(normalized),
        "context_sha": context_sha,
        "normalized_json": normalized,
    }


def _resolve_manifest(value: Any, side: str) -> dict:
    if isinstance(value, str):
        record = registry.read(value)
        if record is None:
            raise ValueError(f"Packet {value} not found ({side}).")
        return record["manifest"]
    if isinstance(value, dict):
        return value
    raise ValueError(f"'{side}' must be a context_sha string or manifest object.")


@mcp.tool(description="Compose a Context Packet from a manifest.")
def compose_packet_tool(manifest: dict) -> dict:
    result = _compose(manifest)
    return {
        "packet_md": result["packet_md"],
        "manifest": result["manifest"],
        "context_sha": result["context_sha"],
    }


@mcp.tool(description="Lint a Context Packet manifest against the PCP-lite schema.")
def lint_packet_tool(manifest: dict) -> dict:
    issues = lint_packet.lint_manifest(manifest, _SCHEMA)
    errors = [i for i in issues if not i.startswith("[warning]")]
    warnings = [i for i in issues if i.startswith("[warning]")]
    return {"ok": not errors, "errors": errors, "warnings": warnings}


@mcp.tool(description="Compose a packet and persist it to the content-addressed registry.")
def register_packet_tool(manifest: dict) -> dict:
    result = _compose(manifest)
    registered = registry.write(
        result["context_sha"], result["normalized_json"], result["packet_md"]
    )
    return {"context_sha": result["context_sha"], "registered": registered}


@mcp.tool(description="Retrieve a registered packet by context_sha.")
def get_packet_tool(context_sha: str) -> dict:
    record = registry.read(context_sha)
    if record is None:
        raise ValueError(f"Packet {context_sha} not found.")
    return {
        "context_sha": context_sha,
        "manifest": record["manifest"],
        "packet_md": record["packet_md"],
    }


@mcp.tool(description="List all registered packets.")
def list_packets_tool() -> dict:
    entries = []
    for sha in registry.list_shas():
        record = registry.read(sha)
        if record is None:
            continue
        entries.append(
            {"context_sha": sha, "mission": record["manifest"].get("mission", "")}
        )
    return {"packets": entries}


@mcp.tool(description="Diff two manifests (by sha or inline). Returns added/removed/changed.")
def diff_packets_tool(left: Any, right: Any) -> dict:
    left_m = _resolve_manifest(left, "left")
    right_m = _resolve_manifest(right, "right")
    left_keys = set(left_m)
    right_keys = set(right_m)
    return {
        "added": {k: right_m[k] for k in sorted(right_keys - left_keys)},
        "removed": {k: left_m[k] for k in sorted(left_keys - right_keys)},
        "changed": {
            k: {"before": left_m[k], "after": right_m[k]}
            for k in sorted(left_keys & right_keys)
            if left_m[k] != right_m[k]
        },
    }


@mcp.tool(description="Compose, register, and return a JCT-ready envelope.")
def enqueue_packet_tool(manifest: dict) -> dict:
    result = _compose(manifest)
    registered = registry.write(
        result["context_sha"], result["normalized_json"], result["packet_md"]
    )
    m = result["manifest"]
    return {
        "task_id": result["context_sha"],
        "context_sha": result["context_sha"],
        "mission": m.get("mission", ""),
        "manifest": m,
        "packet_md": result["packet_md"],
        "allowed_actions": m.get("allowed_actions", []),
        "evidence_requirements": m.get("evidence_requirements", []),
        "risk_flags": m.get("risk_flags", []),
        "callback_url": m.get("callback_url"),
        "registered": registered,
    }


@mcp.tool(
    description=(
        "Check whether an action is permitted by a registered packet's allowed_actions. "
        "Returns {allowed, reason}. reason='unknown_packet' if sha is not registered, "
        "'not_in_allowed_actions' if the action is not permitted, "
        "or 'permitted' when allowed."
    )
)
def check_action_tool(context_sha: str, action: str) -> dict:
    record = registry.read(context_sha)
    if record is None:
        return {"allowed": False, "reason": "unknown_packet"}
    allowed_actions = record["manifest"].get("allowed_actions") or []
    if action in allowed_actions:
        return {"allowed": True, "reason": "permitted"}
    return {"allowed": False, "reason": "not_in_allowed_actions"}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

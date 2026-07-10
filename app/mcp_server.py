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


@mcp.tool(
    description=(
        "Draft a PCP-lite manifest from one raw intent conversational wizard style. "
        "Returns {diagnosis, mission, smallest_next_action, packet_draft}."
    )
)
def draft_intent_tool(
    raw_intent: str,
    human_constraints: str | None = None,
    additional_context: str | None = None,
    route: str | None = None,
    known_project_context: str | None = None,
    desired_output_mode: str | None = None,
) -> dict:
    body = {
        "raw_intent": raw_intent,
    }
    if human_constraints:
        body["human_constraints"] = human_constraints
    if additional_context:
        body["additional_context"] = additional_context
    if route:
        body["route"] = route
    if known_project_context:
        body["known_project_context"] = known_project_context
    if desired_output_mode:
        body["desired_output_mode"] = desired_output_mode

    # Call FastAPI draft builder helper
    from app.main import _draft_manifest_from_intent, _diagnose_intent, _optional_string_or_list
    import json

    manifest = _draft_manifest_from_intent(body)
    issues = lint_packet.lint_manifest(manifest, _SCHEMA)
    errors = [i for i in issues if not i.startswith("[warning]")]
    warnings = [i for i in issues if i.startswith("[warning]")]
    
    diagnosis = _diagnose_intent(raw_intent)
    warnings.extend(diagnosis["warnings"])

    route_list = _optional_string_or_list(body, "route")
    if not route_list:
        route_list = diagnosis["suggested_route"]
    route_text = " -> ".join(route_list)

    diag_parts = []
    if diagnosis["is_devops"] or any("DevOps" in r for r in route_list):
        diag_parts.append("DevOps Task Detected: Strategic intent is clear, but continuous improvement tasks should be redirected to external DevOps loops (QRCI).")
    else:
        diag_parts.append(f"Strategic Route Grounded: {route_text}. Handed off to strategic deployment loop.")

    if warnings:
        clean_warns = [w.replace("[warning]", "").strip() for w in warnings]
        diag_parts.append(f"Lint Warnings: {', '.join(clean_warns)}")
    
    diagnosis_text = " | ".join(diag_parts)

    normalized_manifest = compose_packet.normalize_manifest(manifest)
    
    smallest_next_action = ""
    for artifact in manifest["required_artifacts"]:
        if artifact.startswith("Smallest next action:"):
            smallest_next_action = artifact.replace("Smallest next action:", "").strip()
            break
    if not smallest_next_action:
        for note in manifest["notes"]:
            if note.startswith("Smallest next action:"):
                smallest_next_action = note.replace("Smallest next action:", "").strip()
                break

    return {
        "diagnosis": diagnosis_text,
        "mission": manifest["mission"],
        "smallest_next_action": smallest_next_action,
        "packet_draft": json.loads(normalized_manifest),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

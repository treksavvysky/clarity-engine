"""Clarity Engine MCP server.

Exposes Mission Packet operations and read-only Raw Intent Packet access as MCP
tools over stdio. All tool handlers delegate to the same modules the FastAPI
endpoints use — no business logic is reimplemented here.

Run with:
    python -m app.mcp_server
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from app import intent_links, intent_registry, proposal_registry, registry
from tools import agent_refinement_proposal, compose_packet, lint_packet

mcp = FastMCP(
    "clarity-engine",
    instructions=(
        "Clarity Engine MCP tools provide deterministic Mission Packet operations "
        "and read-only Raw Intent Packet list, get, lineage, linked-mission, and diff access. "
        "Agent Refinement Proposal tools can validate and store review records but "
        "cannot mutate Raw Intent lineage or grant readiness, approval, or execution authority. "
        "Mission Packet register/enqueue operations persist to packets/registry/. "
        "Raw Intent MCP operations do not mutate, promote, or retrieve external context."
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


def _raise_intent_error(exc: intent_registry.IntentRegistryError) -> None:
    raise ValueError(f"{exc.code}: {exc.message}") from exc


def _raise_intent_link_error(exc: intent_links.IntentLinkError) -> None:
    raise ValueError(f"{exc.code}: {exc.message}") from exc


def _raise_proposal_error(exc: proposal_registry.ProposalRegistryError) -> None:
    raise ValueError(f"{exc.code}: {exc.message}") from exc


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


@mcp.tool(description="List registered Raw Intent Packet revisions.")
def list_intents_tool() -> dict:
    return {"intents": intent_registry.list_summaries()}


@mcp.tool(description="Retrieve one registered Raw Intent Packet by intent_sha.")
def get_intent_tool(intent_sha: str) -> dict:
    try:
        return intent_registry.read(intent_sha)
    except intent_registry.IntentRegistryError as exc:
        _raise_intent_error(exc)


@mcp.tool(description="Retrieve Raw Intent Packet ancestry nearest parent first.")
def get_intent_lineage_tool(intent_sha: str) -> dict:
    try:
        intent_registry.read(intent_sha)
        lineage = intent_registry.ancestors(intent_sha)
    except intent_registry.IntentRegistryError as exc:
        _raise_intent_error(exc)
    return {"intent_sha": intent_sha, "ancestors": lineage}


@mcp.tool(description="List Mission Packets promoted from a Raw Intent.")
def get_intent_missions_tool(intent_sha: str) -> dict:
    try:
        return intent_links.list_missions(intent_sha)
    except intent_registry.IntentRegistryError as exc:
        _raise_intent_error(exc)
    except intent_links.IntentLinkError as exc:
        _raise_intent_link_error(exc)


@mcp.tool(description="Diff two Raw Intent Packets by intent_sha or inline manifest.")
def diff_intents_tool(left: Any, right: Any) -> dict:
    try:
        left_manifest = intent_registry.resolve_manifest(left, "left")
        right_manifest = intent_registry.resolve_manifest(right, "right")
    except intent_registry.IntentRegistryError as exc:
        _raise_intent_error(exc)
    return intent_registry.diff_manifests(left_manifest, right_manifest)


@mcp.tool(
    description=(
        "Validate an Agent Refinement Proposal without persistence or Raw Intent mutation."
    )
)
def lint_refinement_proposal_tool(manifest: dict) -> dict:
    errors = agent_refinement_proposal.validate_manifest(manifest)
    return {"ok": not errors, "errors": errors, "warnings": []}


@mcp.tool(
    description=(
        "Compose deterministic Agent Refinement Proposal artifacts without persistence."
    )
)
def compose_refinement_proposal_tool(manifest: dict) -> dict:
    try:
        result = agent_refinement_proposal.compose_manifest(manifest)
    except ValueError as exc:
        _raise_proposal_error(proposal_registry.InvalidProposalError(str(exc)))
    return {
        "manifest": result["manifest"],
        "proposal_md": result["proposal_md"],
        "proposal_sha": result["proposal_sha"],
    }


@mcp.tool(
    description=(
        "Register an immutable proposal for human review. This does not mutate the "
        "source Raw Intent or grant readiness, approval, promotion, enqueue, or execution."
    )
)
def register_refinement_proposal_tool(manifest: dict) -> dict:
    try:
        return proposal_registry.register(manifest)
    except proposal_registry.ProposalRegistryError as exc:
        _raise_proposal_error(exc)


@mcp.tool(description="List registered Agent Refinement Proposals, optionally by source intent.")
def list_refinement_proposals_tool(source_intent_sha: str | None = None) -> dict:
    try:
        return {"proposals": proposal_registry.list_summaries(source_intent_sha)}
    except proposal_registry.ProposalRegistryError as exc:
        _raise_proposal_error(exc)


@mcp.tool(description="Retrieve one verified Agent Refinement Proposal by proposal_sha.")
def get_refinement_proposal_tool(proposal_sha: str) -> dict:
    try:
        return proposal_registry.read(proposal_sha)
    except proposal_registry.ProposalRegistryError as exc:
        _raise_proposal_error(exc)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

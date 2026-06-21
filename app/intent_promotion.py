"""Validation and orchestration for approved Raw Intent promotion."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from app import intent_links, intent_registry, intent_workflow, registry
from tools import compose_packet, lint_packet, raw_intent_packet

LINT_SCHEMA = lint_packet.load_schema()


class PromotionError(Exception):
    """Stable promotion request failure."""

    code = "invalid_promotion"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _approval(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PromotionError("'approval' must be a JSON object.")
    unexpected = sorted(set(value) - {"approved", "approved_by", "reference"})
    if unexpected:
        raise PromotionError(
            "'approval' contains unsupported fields: " + ", ".join(unexpected) + "."
        )
    if value.get("approved") is not True:
        raise PromotionError("'approval.approved' must be true.")
    approved_by = value.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise PromotionError(
            "'approval.approved_by' must be a non-empty string."
        )
    result = {"approved": True, "approved_by": approved_by.strip()}
    reference = value.get("reference")
    if reference is not None:
        if not isinstance(reference, str) or not reference.strip():
            raise PromotionError(
                "'approval.reference' must be a non-empty string when provided."
            )
        result["reference"] = reference.strip()
    return result


def prepare(intent_sha: str, body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise PromotionError("Promotion request body must be a JSON object.")
    expected = {"mission_packet", "approval", "grounding_references"}
    unexpected = sorted(set(body) - expected)
    missing = sorted(expected - set(body))
    if unexpected or missing:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unsupported: " + ", ".join(unexpected))
        raise PromotionError("Invalid promotion fields (" + "; ".join(details) + ").")

    source = intent_registry.read(intent_sha)
    source_manifest = source["manifest"]
    if source_manifest["status"] != "ready_for_mission":
        raise PromotionError(
            "Raw Intent Packet must have status 'ready_for_mission' before promotion."
        )
    readiness = intent_workflow.readiness_errors(source_manifest)
    if readiness:
        raise PromotionError(" ".join(readiness))

    mission_manifest = body["mission_packet"]
    if not isinstance(mission_manifest, dict):
        raise PromotionError("'mission_packet' must be a JSON object.")
    issues = lint_packet.lint_manifest(mission_manifest, LINT_SCHEMA)
    errors = [issue for issue in issues if not issue.startswith("[warning]")]
    warnings = [issue for issue in issues if issue.startswith("[warning]")]
    if errors:
        raise PromotionError(
            "Mission Packet failed lint validation: " + "; ".join(errors)
        )
    normalized = compose_packet.normalize_manifest(mission_manifest)
    normalized_manifest = json.loads(normalized)
    context_sha = compose_packet.compute_context_sha(normalized)
    packet_md = compose_packet.render_packet_md(normalized_manifest) + "\n"
    approval = _approval(body["approval"])
    try:
        references = intent_links.validate_grounding_references(
            body["grounding_references"], source_manifest, normalized_manifest
        )
    except intent_links.InvalidIntentLinkError as exc:
        raise PromotionError(exc.message) from exc

    promoted_manifest = deepcopy(source_manifest)
    promoted_manifest["parent_intent_sha"] = intent_sha
    promoted_manifest["status"] = "promoted"
    errors = raw_intent_packet.validate_manifest(promoted_manifest)
    if errors:
        raise PromotionError(
            "Promoted Raw Intent revision is invalid: " + " ".join(errors)
        )
    promoted_result = raw_intent_packet.compose_manifest(promoted_manifest)
    link = {
        "version": intent_links.LINK_VERSION,
        "intent_sha": intent_sha,
        "context_sha": context_sha,
        "promoted_intent_sha": promoted_result["intent_sha"],
        "approval": approval,
        "grounding_references": references,
    }
    intent_links.validate_link(link)
    return {
        "source_intent_sha": intent_sha,
        "context_sha": context_sha,
        "mission_manifest": normalized_manifest,
        "normalized_json": normalized,
        "packet_md": packet_md,
        "warnings": warnings,
        "promoted_manifest": promoted_result["manifest"],
        "promoted_intent_sha": promoted_result["intent_sha"],
        "link": link,
    }


def promote(intent_sha: str, body: Any) -> dict[str, Any]:
    prepared = prepare(intent_sha, body)
    intent_links.ensure_compatible(prepared["link"])
    mission_registered = registry.write(
        prepared["context_sha"],
        prepared["normalized_json"],
        prepared["packet_md"],
    )
    link_registered = intent_links.write(prepared["link"])
    intent_result = intent_registry.register(prepared["promoted_manifest"])
    verified = intent_links.read(intent_sha, prepared["context_sha"])
    return {
        "source_intent_sha": intent_sha,
        "promoted_intent_sha": intent_result["intent_sha"],
        "context_sha": prepared["context_sha"],
        "mission_registered": mission_registered,
        "link_registered": link_registered,
        "intent_registered": intent_result["registered"],
        "link": verified["link"],
        "manifest": prepared["mission_manifest"],
        "packet_md": prepared["packet_md"],
        "warnings": prepared["warnings"],
    }

"""Authoritative append-only links from Raw Intents to Mission Packets."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from app import intent_registry, registry
from tools import compose_packet

DEFAULT_ROOT = (
    Path(__file__).resolve().parent.parent
    / "packets"
    / "links"
    / "intent-missions"
)
SHA_PATTERN = re.compile(r"^[a-f0-9]{64}$")
LINK_VERSION = "1.0.0"
PACKET_FIELDS = {"current_reality", "constraints"}
INTENT_FIELDS = {
    "grounding_entries",
    "human_context",
    "constraints",
    "clarifications",
    "context_sources",
}


class IntentLinkError(Exception):
    """Base class for stable intent-to-mission link failures."""

    code = "intent_link_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidIntentLinkError(IntentLinkError):
    code = "invalid_intent_link"


class ConflictingIntentLinkError(IntentLinkError):
    code = "conflicting_intent_link"


class CorruptIntentLinkError(IntentLinkError):
    code = "corrupt_intent_link"


def root_path() -> Path:
    override = os.environ.get("CLARITY_INTENT_LINK_ROOT")
    return Path(override) if override else DEFAULT_ROOT


def _link_path(intent_sha: str, context_sha: str) -> Path:
    return root_path() / intent_sha / f"{context_sha}.json"


def _validate_sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or SHA_PATTERN.fullmatch(value) is None:
        raise InvalidIntentLinkError(
            f"'{field}' must be a lowercase 64-character SHA-256 value."
        )
    return value


def normalize_link(link: dict[str, Any]) -> str:
    return json.dumps(link, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _resolve_source(
    manifest: dict[str, Any], intent_field: str, intent_index: int
) -> Any:
    values = manifest.get(intent_field)
    if not isinstance(values, list) or intent_index >= len(values):
        raise InvalidIntentLinkError(
            f"Grounding reference points outside '{intent_field}'."
        )
    return values[intent_index]


def validate_grounding_references(
    value: Any,
    source_manifest: dict[str, Any],
    mission_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    for field in PACKET_FIELDS:
        if not isinstance(mission_manifest.get(field), list) or not mission_manifest[field]:
            raise InvalidIntentLinkError(
                f"Mission Packet '{field}' must be a non-empty list."
            )
    if not isinstance(value, list) or not value:
        raise InvalidIntentLinkError(
            "'grounding_references' must be a non-empty list."
        )
    normalized: list[dict[str, Any]] = []
    covered: set[tuple[str, int]] = set()
    for index, entry in enumerate(value):
        if not isinstance(entry, dict) or set(entry) != {
            "packet_field",
            "packet_index",
            "intent_field",
            "intent_index",
        }:
            raise InvalidIntentLinkError(
                f"'grounding_references' entry at index {index} must contain "
                "packet_field, packet_index, intent_field, and intent_index."
            )
        packet_field = entry["packet_field"]
        intent_field = entry["intent_field"]
        packet_index = entry["packet_index"]
        intent_index = entry["intent_index"]
        if packet_field not in PACKET_FIELDS:
            raise InvalidIntentLinkError(
                f"Grounding reference {index} has unsupported packet_field."
            )
        if intent_field not in INTENT_FIELDS:
            raise InvalidIntentLinkError(
                f"Grounding reference {index} has unsupported intent_field."
            )
        if (
            not isinstance(packet_index, int)
            or isinstance(packet_index, bool)
            or packet_index < 0
        ):
            raise InvalidIntentLinkError(
                f"Grounding reference {index} has invalid packet_index."
            )
        if (
            not isinstance(intent_index, int)
            or isinstance(intent_index, bool)
            or intent_index < 0
        ):
            raise InvalidIntentLinkError(
                f"Grounding reference {index} has invalid intent_index."
            )
        packet_values = mission_manifest.get(packet_field)
        if not isinstance(packet_values, list) or packet_index >= len(packet_values):
            raise InvalidIntentLinkError(
                f"Grounding reference points outside Mission Packet '{packet_field}'."
            )
        target = (packet_field, packet_index)
        if target in covered:
            raise InvalidIntentLinkError(
                f"Mission Packet {packet_field} entry {packet_index} "
                "is referenced more than once."
            )
        source = _resolve_source(source_manifest, intent_field, intent_index)
        if packet_field == "current_reality":
            if (
                intent_field != "grounding_entries"
                or not isinstance(source, dict)
                or source.get("kind") != "verified_fact"
                or not source.get("sources")
            ):
                raise InvalidIntentLinkError(
                    "Every current_reality entry must reference a sourced "
                    "verified_fact grounding entry."
                )
        if intent_field == "clarifications" and (
            not isinstance(source, dict)
            or source.get("status") != "answered"
            or not source.get("answer")
        ):
            raise InvalidIntentLinkError(
                "Clarification references must point to answered entries."
            )
        covered.add(target)
        normalized.append(
            {
                "packet_field": packet_field,
                "packet_index": packet_index,
                "intent_field": intent_field,
                "intent_index": intent_index,
            }
        )

    required = {
        (field, index)
        for field in sorted(PACKET_FIELDS)
        for index in range(len(mission_manifest[field]))
    }
    missing = sorted(required - covered)
    if missing:
        rendered = ", ".join(f"{field}[{index}]" for field, index in missing)
        raise InvalidIntentLinkError(
            f"Grounding references do not cover Mission Packet entries: {rendered}."
        )
    return normalized


def validate_link(link: Any) -> dict[str, Any]:
    if not isinstance(link, dict):
        raise InvalidIntentLinkError("Intent-to-mission link must be a JSON object.")
    expected = {
        "version",
        "intent_sha",
        "context_sha",
        "promoted_intent_sha",
        "approval",
        "grounding_references",
    }
    if set(link) != expected:
        raise InvalidIntentLinkError(
            "Intent-to-mission link fields must be exactly: "
            + ", ".join(sorted(expected))
            + "."
        )
    if link["version"] != LINK_VERSION:
        raise InvalidIntentLinkError(
            f"'version' must be '{LINK_VERSION}'."
        )
    _validate_sha(link["intent_sha"], "intent_sha")
    _validate_sha(link["context_sha"], "context_sha")
    _validate_sha(link["promoted_intent_sha"], "promoted_intent_sha")

    approval = link["approval"]
    if not isinstance(approval, dict):
        raise InvalidIntentLinkError("'approval' must be a JSON object.")
    allowed_approval = {"approved", "approved_by", "reference"}
    if set(approval) - allowed_approval:
        raise InvalidIntentLinkError("'approval' contains unsupported fields.")
    if approval.get("approved") is not True:
        raise InvalidIntentLinkError("'approval.approved' must be true.")
    approved_by = approval.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise InvalidIntentLinkError(
            "'approval.approved_by' must be a non-empty string."
        )
    reference = approval.get("reference")
    if reference is not None and (
        not isinstance(reference, str) or not reference.strip()
    ):
        raise InvalidIntentLinkError(
            "'approval.reference' must be a non-empty string when provided."
        )

    references = link["grounding_references"]
    if not isinstance(references, list) or not references:
        raise InvalidIntentLinkError(
            "'grounding_references' must be a non-empty list."
        )
    for index, reference_entry in enumerate(references):
        if not isinstance(reference_entry, dict):
            raise InvalidIntentLinkError(
                f"'grounding_references' entry at index {index} must be an object."
            )
    return link


def _read_mission(context_sha: str) -> dict[str, Any]:
    try:
        record = registry.read(context_sha)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorruptIntentLinkError(
            f"Linked Mission Packet {context_sha} cannot be read: {exc}."
        ) from exc
    if record is None:
        raise CorruptIntentLinkError(
            f"Linked Mission Packet {context_sha} was not found."
        )
    normalized = compose_packet.normalize_manifest(record["manifest"])
    actual_sha = compose_packet.compute_context_sha(normalized)
    packet_md = compose_packet.render_packet_md(record["manifest"]) + "\n"
    if actual_sha != context_sha or packet_md != record["packet_md"]:
        raise CorruptIntentLinkError(
            f"Linked Mission Packet {context_sha} failed integrity validation."
        )
    return record


def read(intent_sha: str, context_sha: str) -> dict[str, Any]:
    _validate_sha(intent_sha, "intent_sha")
    _validate_sha(context_sha, "context_sha")
    path = _link_path(intent_sha, context_sha)
    if not path.is_file():
        raise InvalidIntentLinkError(
            f"Intent-to-mission link {intent_sha}/{context_sha} was not found."
        )
    try:
        link = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorruptIntentLinkError(
            f"Intent-to-mission link {intent_sha}/{context_sha} cannot be read: {exc}."
        ) from exc
    try:
        validate_link(link)
    except InvalidIntentLinkError as exc:
        raise CorruptIntentLinkError(exc.message) from exc
    if link["intent_sha"] != intent_sha or link["context_sha"] != context_sha:
        raise CorruptIntentLinkError(
            "Intent-to-mission link path does not match its recorded identities."
        )
    try:
        source = intent_registry.read(intent_sha)
        promoted = intent_registry.read(link["promoted_intent_sha"])
    except intent_registry.IntentRegistryError as exc:
        raise CorruptIntentLinkError(
            f"Intent-to-mission link references an invalid Raw Intent record: {exc.message}"
        ) from exc
    if source["manifest"].get("status") != "ready_for_mission":
        raise CorruptIntentLinkError(
            "Linked source Raw Intent revision is not status 'ready_for_mission'."
        )
    if promoted["manifest"].get("parent_intent_sha") != intent_sha:
        raise CorruptIntentLinkError(
            "Promoted Raw Intent revision does not descend from the linked source."
        )
    if promoted["manifest"].get("status") != "promoted":
        raise CorruptIntentLinkError(
            "Linked promoted Raw Intent revision is not terminal status 'promoted'."
        )
    mission = _read_mission(context_sha)
    try:
        normalized_references = validate_grounding_references(
            link["grounding_references"],
            source["manifest"],
            mission["manifest"],
        )
    except InvalidIntentLinkError as exc:
        raise CorruptIntentLinkError(
            f"Intent-to-mission grounding references are invalid: {exc.message}"
        ) from exc
    if normalized_references != link["grounding_references"]:
        raise CorruptIntentLinkError(
            "Intent-to-mission grounding references are not normalized."
        )
    return {"link": link, "source_intent": source, "mission_packet": mission}


def write(link: dict[str, Any]) -> bool:
    validate_link(link)
    intent_sha = link["intent_sha"]
    context_sha = link["context_sha"]
    target = _link_path(intent_sha, context_sha)
    normalized = normalize_link(link)
    if not ensure_compatible(link):
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=".link-", suffix=".json", dir=target.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(normalized)
        try:
            os.link(temp_path, target)
        except FileExistsError:
            existing = target.read_text(encoding="utf-8")
            if existing != normalized:
                raise ConflictingIntentLinkError(
                    f"Intent {intent_sha} already has a conflicting link to {context_sha}."
                )
            return False
    finally:
        temp_path.unlink(missing_ok=True)
    return True


def ensure_compatible(link: dict[str, Any]) -> bool:
    """Return True when absent, False when identical, and fail on conflict."""
    validate_link(link)
    intent_sha = link["intent_sha"]
    context_sha = link["context_sha"]
    target = _link_path(intent_sha, context_sha)
    normalized = normalize_link(link)
    if target.exists():
        try:
            existing = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise CorruptIntentLinkError(
                f"Existing intent-to-mission link cannot be read: {exc}."
            ) from exc
        if existing != normalized:
            raise ConflictingIntentLinkError(
                f"Intent {intent_sha} already has a conflicting link to {context_sha}."
            )
        return False
    return True


def list_missions(intent_sha: str) -> dict[str, Any]:
    intent_registry.read(intent_sha)
    directory = root_path() / intent_sha
    missions: list[dict[str, Any]] = []
    if directory.is_dir():
        for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
            context_sha = path.stem
            try:
                record = read(intent_sha, context_sha)
            except InvalidIntentLinkError as exc:
                raise CorruptIntentLinkError(exc.message) from exc
            link = record["link"]
            mission = record["mission_packet"]["manifest"]
            missions.append(
                {
                    "context_sha": context_sha,
                    "mission": mission.get("mission", ""),
                    "promoted_intent_sha": link["promoted_intent_sha"],
                    "approval": link["approval"],
                    "grounding_references": link["grounding_references"],
                }
            )
    return {"intent_sha": intent_sha, "missions": missions}

"""Content-addressed registry for immutable Raw Intent Packet revisions."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from tools import raw_intent_packet

DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "packets" / "intents"
SHA_PATTERN = re.compile(r"^[a-f0-9]{64}$")
TEMP_PREFIX = ".intent-"

ALLOWED_TRANSITIONS = {
    "captured": {"grounding", "abandoned"},
    "grounding": {"clarification_needed", "ready_for_mission", "abandoned"},
    "clarification_needed": {"grounding", "abandoned"},
    "ready_for_mission": {"grounding", "promoted", "abandoned"},
    "promoted": set(),
    "abandoned": set(),
}


class IntentRegistryError(Exception):
    """Base class for stable Raw Intent registry failures."""

    code = "intent_registry_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidIntentError(IntentRegistryError):
    code = "invalid_intent"


class UnknownIntentError(IntentRegistryError):
    code = "unknown_intent"


class CorruptIntentError(IntentRegistryError):
    code = "corrupt_intent_record"


class BrokenLineageError(IntentRegistryError):
    code = "broken_lineage"


def root_path() -> Path:
    override = os.environ.get("CLARITY_INTENT_REGISTRY_ROOT")
    return Path(override) if override else DEFAULT_ROOT


def _record_dir(intent_sha: str) -> Path:
    return root_path() / intent_sha


def _validate_sha(intent_sha: str) -> None:
    if SHA_PATTERN.fullmatch(intent_sha) is None:
        raise InvalidIntentError("intent_sha must be a lowercase 64-character SHA-256 value.")


def _load_record_files(intent_sha: str) -> tuple[dict[str, Any], str]:
    _validate_sha(intent_sha)
    record_dir = _record_dir(intent_sha)
    if not record_dir.is_dir():
        raise UnknownIntentError(f"Raw Intent Packet {intent_sha} was not found.")

    manifest_path = record_dir / "manifest.json"
    markdown_path = record_dir / "intent.md"
    if not manifest_path.is_file() or not markdown_path.is_file():
        raise CorruptIntentError(
            f"Raw Intent Packet {intent_sha} is missing manifest.json or intent.md."
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        intent_md = markdown_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorruptIntentError(
            f"Raw Intent Packet {intent_sha} cannot be read: {exc}."
        ) from exc
    if not isinstance(manifest, dict):
        raise CorruptIntentError(
            f"Raw Intent Packet {intent_sha} manifest must be a JSON object."
        )
    return manifest, intent_md


def read(intent_sha: str) -> dict[str, Any]:
    """Read and verify one registered Raw Intent Packet."""
    manifest, intent_md = _load_record_files(intent_sha)
    errors = raw_intent_packet.validate_manifest(manifest)
    if errors:
        raise CorruptIntentError(
            f"Raw Intent Packet {intent_sha} failed schema validation: {'; '.join(errors)}"
        )

    result = raw_intent_packet.compose_manifest(manifest)
    if result["intent_sha"] != intent_sha:
        raise CorruptIntentError(
            f"Raw Intent Packet {intent_sha} does not match its directory identity."
        )
    if result["intent_md"] != intent_md:
        raise CorruptIntentError(
            f"Raw Intent Packet {intent_sha} rendered Markdown does not match its manifest."
        )
    if manifest.get("status") == "ready_for_mission":
        from app.intent_workflow import validate_readiness

        validate_readiness(manifest)
    return {
        "intent_sha": intent_sha,
        "manifest": result["manifest"],
        "intent_md": intent_md,
    }


def _validate_revision(manifest: dict[str, Any], intent_sha: str) -> None:
    parent_sha = manifest.get("parent_intent_sha")
    status = manifest["status"]
    if parent_sha is None:
        if status != "captured":
            raise BrokenLineageError(
                "A root Raw Intent Packet must begin with status 'captured'."
            )
        return
    if parent_sha == intent_sha:
        raise BrokenLineageError("A Raw Intent Packet cannot reference itself as parent.")

    try:
        parent = read(parent_sha)
    except UnknownIntentError as exc:
        raise BrokenLineageError(
            f"Parent Raw Intent Packet {parent_sha} was not found."
        ) from exc
    except CorruptIntentError as exc:
        raise BrokenLineageError(
            f"Parent Raw Intent Packet {parent_sha} is corrupt."
        ) from exc

    parent_manifest = parent["manifest"]
    if manifest["raw_intent"] != parent_manifest["raw_intent"]:
        raise BrokenLineageError(
            "A Raw Intent Packet revision must preserve raw_intent exactly."
        )

    parent_status = parent_manifest["status"]
    allowed = ALLOWED_TRANSITIONS[parent_status]
    if status not in allowed:
        if not allowed:
            raise BrokenLineageError(
                f"Status '{parent_status}' is terminal and cannot have a child revision."
            )
        allowed_text = ", ".join(sorted(allowed))
        raise BrokenLineageError(
            f"Illegal Raw Intent status transition: {parent_status} -> {status}; "
            f"allowed: {allowed_text}."
        )
    if status == "ready_for_mission":
        from app.intent_workflow import validate_readiness

        validate_readiness(manifest)


def register(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate and atomically register one immutable Raw Intent revision."""
    try:
        result = raw_intent_packet.compose_manifest(manifest)
    except ValueError as exc:
        raise InvalidIntentError(str(exc)) from exc

    intent_sha = result["intent_sha"]
    _validate_revision(result["manifest"], intent_sha)
    target = _record_dir(intent_sha)
    if target.exists():
        read(intent_sha)
        return {"intent_sha": intent_sha, "registered": False}

    root = root_path()
    root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=root))
    try:
        (temp_dir / "manifest.json").write_text(
            result["normalized_json"], encoding="utf-8"
        )
        (temp_dir / "intent.md").write_text(result["intent_md"], encoding="utf-8")
        try:
            temp_dir.rename(target)
        except FileExistsError:
            read(intent_sha)
            return {"intent_sha": intent_sha, "registered": False}
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    read(intent_sha)
    return {"intent_sha": intent_sha, "registered": True}


def list_shas() -> list[str]:
    """Return valid registered identities in deterministic order."""
    root = root_path()
    if not root.is_dir():
        return []

    valid: list[str] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if not path.is_dir() or SHA_PATTERN.fullmatch(path.name) is None:
            continue
        try:
            read(path.name)
            ancestors(path.name)
        except IntentRegistryError:
            continue
        valid.append(path.name)
    return valid


def summarize(record: dict[str, Any]) -> dict[str, Any]:
    manifest = record["manifest"]
    raw_intent = manifest["raw_intent"]
    preview = raw_intent if len(raw_intent) <= 120 else raw_intent[:117] + "..."
    open_clarifications = sum(
        1
        for entry in manifest.get("clarifications", [])
        if isinstance(entry, dict) and entry.get("status") == "open"
    )
    return {
        "intent_sha": record["intent_sha"],
        "status": manifest["status"],
        "raw_intent_preview": preview,
        "source": manifest["provenance"]["source"],
        "parent_intent_sha": manifest.get("parent_intent_sha"),
        "clarifications_needed_count": (
            len(manifest.get("clarifications_needed", [])) + open_clarifications
        ),
        "unresolved_gaps_count": len(manifest.get("unresolved_gaps", [])),
    }


def list_summaries() -> list[dict[str, Any]]:
    return [summarize(read(intent_sha)) for intent_sha in list_shas()]


def ancestors(intent_sha: str) -> list[dict[str, Any]]:
    """Return verified ancestors nearest parent to oldest root."""
    record = read(intent_sha)
    lineage: list[dict[str, Any]] = []
    seen = {intent_sha}
    child_manifest = record["manifest"]
    parent_sha = child_manifest.get("parent_intent_sha")

    while parent_sha:
        if parent_sha in seen:
            raise BrokenLineageError("Raw Intent Packet lineage contains a cycle.")
        seen.add(parent_sha)
        try:
            parent = read(parent_sha)
        except (UnknownIntentError, CorruptIntentError) as exc:
            raise BrokenLineageError(
                f"Raw Intent Packet lineage cannot resolve parent {parent_sha}."
            ) from exc

        parent_manifest = parent["manifest"]
        if child_manifest["raw_intent"] != parent_manifest["raw_intent"]:
            raise BrokenLineageError(
                "Raw Intent Packet lineage contains a raw_intent mismatch."
            )
        child_status = child_manifest["status"]
        parent_status = parent_manifest["status"]
        if child_status not in ALLOWED_TRANSITIONS[parent_status]:
            raise BrokenLineageError(
                f"Raw Intent Packet lineage contains illegal transition "
                f"{parent_status} -> {child_status}."
            )

        lineage.append(
            {
                "intent_sha": parent_sha,
                "status": parent_status,
                "parent_intent_sha": parent_manifest.get("parent_intent_sha"),
            }
        )
        child_manifest = parent_manifest
        parent_sha = parent_manifest.get("parent_intent_sha")
    if child_manifest["status"] != "captured":
        raise BrokenLineageError(
            "Raw Intent Packet lineage root must have status 'captured'."
        )
    return lineage


def resolve_manifest(value: Any, side: str) -> dict[str, Any]:
    if isinstance(value, str):
        return read(value)["manifest"]
    if isinstance(value, dict):
        errors = raw_intent_packet.validate_manifest(value)
        if errors:
            raise InvalidIntentError(
                f"Invalid inline Raw Intent Packet ({side}): {'; '.join(errors)}"
            )
        return value
    raise InvalidIntentError(
        f"'{side}' must be an intent_sha string or an inline Raw Intent Packet object."
    )


def diff_manifests(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_keys = set(left)
    right_keys = set(right)
    return {
        "added": {key: right[key] for key in sorted(right_keys - left_keys)},
        "removed": {key: left[key] for key in sorted(left_keys - right_keys)},
        "changed": {
            key: {"before": left[key], "after": right[key]}
            for key in sorted(left_keys & right_keys)
            if left[key] != right[key]
        },
    }

#!/usr/bin/env python3
"""Validate and deterministically compose Raw Intent Packet artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "raw_intent_packet.schema.json"
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON input: {exc}") from exc


def load_schema(path: Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    schema = load_json(path)
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a JSON object.")
    return schema


def _resolve_ref(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    reference = schema.get("$ref")
    if not reference:
        return schema
    if not isinstance(reference, str) or not reference.startswith("#/"):
        raise ValueError(f"Unsupported schema reference: {reference}")

    resolved: Any = root
    for part in reference[2:].split("/"):
        if not isinstance(resolved, dict) or part not in resolved:
            raise ValueError(f"Unknown schema reference: {reference}")
        resolved = resolved[part]
    if not isinstance(resolved, dict):
        raise ValueError(f"Schema reference must resolve to an object: {reference}")
    return resolved


def _is_rfc3339(value: str) -> bool:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validate(
    value: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    path: str,
) -> list[str]:
    schema = _resolve_ref(schema, root)
    errors: list[str] = []
    expected_type = schema.get("type")

    if expected_type == "object":
        if not isinstance(value, dict):
            return [f"{path} must be an object."]
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        for field in required:
            if field not in value:
                errors.append(f"{path}.{field} is required.")
        if schema.get("additionalProperties") is False:
            for field in value:
                if field not in properties:
                    errors.append(f"{path}.{field} is not allowed.")
        for field, item in value.items():
            field_schema = properties.get(field)
            if isinstance(field_schema, dict):
                errors.extend(_validate(item, field_schema, root, f"{path}.{field}"))
        return errors

    if expected_type == "array":
        if not isinstance(value, list):
            return [f"{path} must be an array."]
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path} must contain at least {min_items} item(s).")
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate(item, item_schema, root, f"{path}[{index}]"))
        return errors

    if expected_type == "string":
        if not isinstance(value, str):
            return [f"{path} must be a string."]
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path} must contain at least {min_length} character(s).")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{path} must be one of: {', '.join(enum)}.")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"{path} must match pattern {pattern}.")
        if schema.get("format") == "date-time" and not _is_rfc3339(value):
            errors.append(f"{path} must be an RFC 3339 date-time with a timezone.")
        return errors

    return [f"{path} uses unsupported schema type: {expected_type}."]


def validate_manifest(
    manifest: Any,
    schema: dict[str, Any] | None = None,
) -> list[str]:
    active_schema = schema or load_schema()
    errors = _validate(manifest, active_schema, active_schema, "$")
    if isinstance(manifest, dict):
        raw_intent = manifest.get("raw_intent")
        if isinstance(raw_intent, str) and not raw_intent.strip():
            errors.append("$.raw_intent must contain non-whitespace content.")
    return errors


def normalize_manifest(manifest: dict[str, Any]) -> str:
    """Return canonical JSON without rewriting any accepted string values."""
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute_intent_sha(normalized_manifest: str) -> str:
    return hashlib.sha256(normalized_manifest.encode("utf-8")).hexdigest()


def _render_list(title: str, values: Any) -> list[str]:
    if not isinstance(values, list) or not values:
        return []
    lines = [f"## {title}", ""]
    lines.extend(f"- {value}" for value in values)
    lines.append("")
    return lines


def render_intent_md(manifest: dict[str, Any]) -> str:
    provenance = manifest["provenance"]
    lines = [
        "# Raw Intent Packet",
        "",
        f"- **Version:** {manifest['version']}",
        f"- **Status:** {manifest['status']}",
        f"- **Source:** {provenance['source']}",
    ]
    if provenance.get("author"):
        lines.append(f"- **Author:** {provenance['author']}")
    if provenance.get("captured_at"):
        lines.append(f"- **Captured At:** {provenance['captured_at']}")
    if manifest.get("parent_intent_sha"):
        lines.append(f"- **Parent Intent SHA:** {manifest['parent_intent_sha']}")

    lines.extend(["", "## Raw Intent (Verbatim)", "", "```text"])
    lines.extend(manifest["raw_intent"].split("\n"))
    lines.extend(["```", ""])

    sections = [
        ("Human Context", "human_context"),
        ("Constraints", "constraints"),
        ("Desired Direction", "desired_direction"),
        ("Assumptions", "assumptions"),
        ("Related Projects", "related_projects"),
        ("Clarifications Needed", "clarifications_needed"),
        ("Context Sources", "context_sources"),
        ("Verified Facts", "verified_facts"),
        ("Grounding Observations", "grounding_observations"),
        ("Rejected Assumptions", "rejected_assumptions"),
        ("Clarification Answers", "clarification_answers"),
        ("Unresolved Gaps", "unresolved_gaps"),
    ]
    for title, field in sections:
        value = manifest.get(field)
        if field == "desired_direction" and isinstance(value, str):
            lines.extend([f"## {title}", "", value, ""])
        else:
            lines.extend(_render_list(title, value))
    return "\n".join(lines)


def compose_manifest(
    manifest: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors = validate_manifest(manifest, schema)
    if errors:
        raise ValueError("\n".join(errors))
    normalized = normalize_manifest(manifest)
    return {
        "manifest": json.loads(normalized),
        "normalized_json": normalized,
        "intent_md": render_intent_md(manifest) + "\n",
        "intent_sha": compute_intent_sha(normalized),
    }


def _write_composed(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        result["normalized_json"], encoding="utf-8"
    )
    (output_dir / "intent.md").write_text(result["intent_md"], encoding="utf-8")
    (output_dir / "intent_sha").write_text(
        result["intent_sha"] + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint or compose a Raw Intent Packet manifest."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="Validate a manifest.")
    lint_parser.add_argument("manifest_path", type=Path)

    compose_parser = subparsers.add_parser(
        "compose", help="Validate and emit deterministic artifacts."
    )
    compose_parser.add_argument("manifest_path", type=Path)
    compose_parser.add_argument(
        "--output-dir", type=Path, default=Path("."), help="Artifact directory."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        manifest = load_json(args.manifest_path)
        errors = validate_manifest(manifest)
        if errors:
            for error in errors:
                print(error)
            raise SystemExit(1)
        if args.command == "lint":
            print("Lint passed: Raw Intent Packet is structurally valid.")
            return
        result = compose_manifest(manifest)
        _write_composed(result, args.output_dir)
        print(result["intent_sha"])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

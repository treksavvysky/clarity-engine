#!/usr/bin/env python3
"""Validate and deterministically compose Agent Refinement Proposal artifacts."""

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
    Path(__file__).resolve().parent.parent
    / "agent_refinement_proposal.schema.json"
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
    if not isinstance(manifest, dict):
        return errors

    for field in ("summary",):
        value = manifest.get(field)
        if isinstance(value, str) and not value.strip():
            errors.append(f"$.{field} must contain non-whitespace content.")

    proposer = manifest.get("proposer")
    if isinstance(proposer, dict):
        for field in ("agent", "model"):
            value = proposer.get(field)
            if isinstance(value, str) and not value.strip():
                errors.append(
                    f"$.proposer.{field} must contain non-whitespace content."
                )

    entries = manifest.get("grounding_entries")
    if isinstance(entries, list):
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            statement = entry.get("statement")
            if isinstance(statement, str) and not statement.strip():
                errors.append(
                    f"$.grounding_entries[{index}].statement must contain non-whitespace content."
                )
            sources = entry.get("sources")
            if isinstance(sources, list):
                for source_index, source in enumerate(sources):
                    if isinstance(source, str) and not source.strip():
                        errors.append(
                            f"$.grounding_entries[{index}].sources[{source_index}] "
                            "must contain non-whitespace content."
                        )

    questions = manifest.get("clarification_questions")
    if isinstance(questions, list):
        seen_ids: set[str] = set()
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            question_id = question.get("id")
            if isinstance(question_id, str):
                if question_id in seen_ids:
                    errors.append(
                        f"$.clarification_questions[{index}].id must be unique."
                    )
                seen_ids.add(question_id)
            question_text = question.get("question")
            if isinstance(question_text, str) and not question_text.strip():
                errors.append(
                    f"$.clarification_questions[{index}].question "
                    "must contain non-whitespace content."
                )

    gaps = manifest.get("unresolved_gaps")
    if isinstance(gaps, list):
        for index, gap in enumerate(gaps):
            if isinstance(gap, str) and not gap.strip():
                errors.append(
                    f"$.unresolved_gaps[{index}] must contain non-whitespace content."
                )
    return errors


def normalize_manifest(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute_proposal_sha(normalized_manifest: str) -> str:
    return hashlib.sha256(normalized_manifest.encode("utf-8")).hexdigest()


def render_proposal_md(manifest: dict[str, Any]) -> str:
    proposer = manifest["proposer"]
    lines = [
        "# Agent Refinement Proposal",
        "",
        f"- **Version:** {manifest['version']}",
        f"- **Source Intent SHA:** {manifest['source_intent_sha']}",
        f"- **Proposer:** {proposer['agent']}",
        f"- **Transport:** {proposer['transport']}",
        f"- **Created At:** {manifest['created_at']}",
    ]
    if proposer.get("model"):
        lines.append(f"- **Model:** {proposer['model']}")
    lines.extend(["", "## Summary", "", manifest["summary"], ""])
    lines.extend(["## Proposed Grounding", ""])
    for entry in manifest["grounding_entries"]:
        lines.append(f"- **{entry['kind']}:** {entry['statement']}")
        lines.append(f"  - Sources: {', '.join(entry['sources'])}")
    lines.append("")
    if manifest["clarification_questions"]:
        lines.extend(["## Clarification Questions", ""])
        for question in manifest["clarification_questions"]:
            lines.append(f"- **{question['id']}:** {question['question']}")
        lines.append("")
    if manifest["unresolved_gaps"]:
        lines.extend(["## Unresolved Gaps", ""])
        lines.extend(f"- {gap}" for gap in manifest["unresolved_gaps"])
        lines.append("")
    lines.extend(
        [
            "## Authority Boundary",
            "",
            "This proposal does not mutate Raw Intent state, request readiness, "
            "approve or promote a Mission Packet, enqueue work, or execute actions.",
            "",
        ]
    )
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
        "proposal_md": render_proposal_md(manifest) + "\n",
        "proposal_sha": compute_proposal_sha(normalized),
    }


def _write_composed(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        result["normalized_json"], encoding="utf-8"
    )
    (output_dir / "proposal.md").write_text(
        result["proposal_md"], encoding="utf-8"
    )
    (output_dir / "proposal_sha").write_text(
        result["proposal_sha"] + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint or compose an Agent Refinement Proposal manifest."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    lint_parser = subparsers.add_parser("lint", help="Validate a proposal.")
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
            print("Lint passed: Agent Refinement Proposal is structurally valid.")
            return
        result = compose_manifest(manifest)
        _write_composed(result, args.output_dir)
        print(result["proposal_sha"])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

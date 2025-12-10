#!/usr/bin/env python3
"""Deterministic linter for PCP-lite Context Packet manifests."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "pcp_lite.schema.json"

CRITICAL_FIELDS = {
    "mission": "mission",
    "current_reality": "current reality (facts)",
    "constraints": "constraints",
    "acceptance": "acceptance / definition_of_done",
    "required_artifacts": "required artifacts",
    "failure_modes": "failure modes",
}


def load_json_file(path: Path) -> Any:
    """Load JSON content from a file path."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        sys.stderr.write(f"Manifest file not found: {path}\n")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Invalid JSON input: {exc}\n")
        sys.exit(1)


def load_schema(path: Path = DEFAULT_SCHEMA_PATH) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
    except FileNotFoundError:
        sys.stderr.write(f"Schema file not found: {path}\n")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Schema file is not valid JSON: {exc}\n")
        sys.exit(1)

    if not isinstance(schema, dict):
        sys.stderr.write("Schema must be a JSON object.\n")
        sys.exit(1)

    return schema


def _validate_object(manifest: Any) -> list[str]:
    if not isinstance(manifest, dict):
        return ["Manifest must be a JSON object."]
    return []


def _validate_required_fields(manifest: dict, required: list[str]) -> list[str]:
    errors: list[str] = []
    for field in required:
        if field not in manifest:
            label = CRITICAL_FIELDS.get(field, field)
            errors.append(f"Missing required field: {label} ({field}).")
    return errors


def _validate_additional_properties(manifest: dict, properties: dict, allow_additional: bool) -> list[str]:
    if allow_additional:
        return []

    errors: list[str] = []
    for key in manifest:
        if key not in properties:
            errors.append(f"Unexpected field not allowed by schema: {key}.")
    return errors


def _validate_field_types(manifest: dict, properties: dict) -> list[str]:
    errors: list[str] = []
    for key, value in manifest.items():
        prop = properties.get(key)
        if not prop:
            continue

        expected_type = prop.get("type")
        label = CRITICAL_FIELDS.get(key, key)
        if expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{label}' must be a string.")
                continue
            if key in CRITICAL_FIELDS and not value.strip():
                errors.append(f"Field '{label}' must be a non-empty string.")
        elif expected_type == "array":
            if not isinstance(value, list):
                errors.append(f"Field '{label}' must be a list.")
                continue

            min_items = prop.get("minItems")
            if min_items is not None and len(value) < min_items:
                errors.append(
                    f"Field '{label}' must contain at least {min_items} entries."
                )

            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(
                        f"Field '{label}' entry at index {index} must be a string."
                    )
                    continue
                if key in CRITICAL_FIELDS and not item.strip():
                    errors.append(
                        f"Field '{label}' entry at index {index} must not be empty."
                    )
        else:
            errors.append(f"Unsupported type for field '{label}': {expected_type}.")

    return errors


def lint_manifest(manifest: Any, schema: dict) -> list[str]:
    """Return a list of lint errors for the manifest given the schema."""
    errors = _validate_object(manifest)
    if errors:
        return errors

    properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = schema.get("required", []) if isinstance(schema, dict) else []
    additional_allowed = schema.get("additionalProperties", True)

    errors.extend(_validate_required_fields(manifest, required))
    errors.extend(_validate_additional_properties(manifest, properties, additional_allowed))
    errors.extend(_validate_field_types(manifest, properties))

    return errors


def lint_file(manifest_path: Path, schema_path: Path = DEFAULT_SCHEMA_PATH) -> list[str]:
    manifest = load_json_file(manifest_path)
    schema = load_schema(schema_path)
    return lint_manifest(manifest, schema)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a Context Packet manifest against the PCP-lite schema and content rules."
    )
    parser.add_argument(
        "manifest_path",
        help="Path to the manifest JSON file to lint.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    errors = lint_file(Path(args.manifest_path))

    if errors:
        for message in errors:
            print(message)
        sys.exit(1)

    print("Lint passed: manifest is structurally valid and complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()

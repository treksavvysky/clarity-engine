#!/usr/bin/env python3
"""Deterministic linter for PCP-lite Context Packet manifests."""

import argparse
import json
import re
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

# Vague language patterns that reduce clarity and testability
VAGUE_PATTERNS = [
    (r"\bmaybe\b", "maybe"),
    (r"\bperhaps\b", "perhaps"),
    (r"\bmight\b", "might"),
    (r"\bcould\b", "could"),
    (r"\bshould\b", "should"),
    (r"\btry to\b", "try to"),
    (r"\battempt to\b", "attempt to"),
    (r"\bif possible\b", "if possible"),
    (r"\bwhen possible\b", "when possible"),
    (r"\bas needed\b", "as needed"),
    (r"\bas appropriate\b", "as appropriate"),
    (r"\bgenerally\b", "generally"),
    (r"\busually\b", "usually"),
    (r"\bsomewhat\b", "somewhat"),
    (r"\bfairly\b", "fairly"),
    (r"\bprobably\b", "probably"),
    (r"\bapproximately\b", "approximately"),
    (r"\betc\.?\b", "etc"),
    (r"\band so on\b", "and so on"),
]

# Fields to check for vague language
VAGUE_CHECK_FIELDS = ["mission", "acceptance", "constraints", "required_artifacts"]

# Action verbs that indicate testable/observable outcomes
ACTION_VERBS = [
    "return", "returns", "respond", "responds", "output", "outputs",
    "create", "creates", "delete", "deletes", "update", "updates",
    "send", "sends", "receive", "receives", "write", "writes", "read", "reads",
    "pass", "passes", "fail", "fails", "exist", "exists",
    "contain", "contains", "include", "includes", "exclude", "excludes",
    "match", "matches", "equal", "equals", "display", "displays",
    "show", "shows", "hide", "hides", "enable", "enables", "disable", "disables",
    "start", "starts", "stop", "stops", "run", "runs", "execute", "executes",
    "log", "logs", "print", "prints", "emit", "emits", "produce", "produces",
    "validate", "validates", "verify", "verifies", "check", "checks",
    "accept", "accepts", "reject", "rejects", "allow", "allows", "deny", "denies",
    "complete", "completes", "finish", "finishes", "succeed", "succeeds",
]


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


def _detect_vague_language(manifest: dict) -> list[str]:
    """Detect vague language patterns in critical fields. Returns warnings."""
    warnings: list[str] = []

    for field in VAGUE_CHECK_FIELDS:
        value = manifest.get(field)
        if not value:
            continue

        label = CRITICAL_FIELDS.get(field, field)
        texts = [value] if isinstance(value, str) else value if isinstance(value, list) else []

        for idx, text in enumerate(texts):
            if not isinstance(text, str):
                continue
            text_lower = text.lower()
            for pattern, word in VAGUE_PATTERNS:
                if re.search(pattern, text_lower):
                    if isinstance(value, list):
                        warnings.append(
                            f"[warning] Vague language '{word}' in '{label}' entry {idx}: \"{text[:50]}...\""
                            if len(text) > 50 else
                            f"[warning] Vague language '{word}' in '{label}' entry {idx}: \"{text}\""
                        )
                    else:
                        warnings.append(
                            f"[warning] Vague language '{word}' in '{label}': \"{text[:50]}...\""
                            if len(text) > 50 else
                            f"[warning] Vague language '{word}' in '{label}': \"{text}\""
                        )
                    break  # One warning per entry

    return warnings


def _detect_untestable_acceptance(manifest: dict) -> list[str]:
    """Detect acceptance criteria that lack action verbs. Returns warnings."""
    warnings: list[str] = []
    acceptance = manifest.get("acceptance")

    if not isinstance(acceptance, list):
        return warnings

    action_pattern = re.compile(r"\b(" + "|".join(ACTION_VERBS) + r")\b", re.IGNORECASE)

    for idx, criterion in enumerate(acceptance):
        if not isinstance(criterion, str):
            continue
        if not action_pattern.search(criterion):
            warnings.append(
                f"[warning] Acceptance entry {idx} may not be testable (no action verb found): \"{criterion[:50]}...\""
                if len(criterion) > 50 else
                f"[warning] Acceptance entry {idx} may not be testable (no action verb found): \"{criterion}\""
            )

    return warnings


def lint_manifest(manifest: Any, schema: dict, warn_ambiguity: bool = True) -> list[str]:
    """Return a list of lint errors and warnings for the manifest given the schema.

    Args:
        manifest: The manifest dict to validate.
        schema: The JSON schema to validate against.
        warn_ambiguity: If True, include warnings for vague language and untestable
            acceptance criteria. Defaults to True.

    Returns:
        A list of issues. Errors are plain strings; warnings are prefixed with "[warning]".
    """
    issues = _validate_object(manifest)
    if issues:
        return issues

    properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = schema.get("required", []) if isinstance(schema, dict) else []
    additional_allowed = schema.get("additionalProperties", True)

    issues.extend(_validate_required_fields(manifest, required))
    issues.extend(_validate_additional_properties(manifest, properties, additional_allowed))
    issues.extend(_validate_field_types(manifest, properties))

    # Ambiguity detection (Stage-02.1)
    if warn_ambiguity:
        issues.extend(_detect_vague_language(manifest))
        issues.extend(_detect_untestable_acceptance(manifest))

    return issues


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
    issues = lint_file(Path(args.manifest_path))

    errors = [i for i in issues if not i.startswith("[warning]")]
    warnings = [i for i in issues if i.startswith("[warning]")]

    if errors:
        for message in errors:
            print(message)
        sys.exit(1)

    if warnings:
        for message in warnings:
            print(message)

    print("Lint passed: manifest is structurally valid and complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()

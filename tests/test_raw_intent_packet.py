import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from tools import raw_intent_packet


ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_PATH = ROOT / "packets" / "examples" / "raw_intent_packet_example.json"
GOLDEN_INTENT_SHA = (
    "0d0c7657719231ad5f8d778dbe64b58f4bb26a664afaeb4ded590fb6620aa478"
)


def load_example():
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def test_valid_example_passes_schema_validation():
    assert raw_intent_packet.validate_manifest(load_example()) == []


def test_invalid_examples_report_required_and_unknown_fields():
    missing = raw_intent_packet.load_json(
        ROOT
        / "packets"
        / "examples"
        / "raw_intent_packet_invalid_missing_provenance.json"
    )
    unknown = raw_intent_packet.load_json(
        ROOT
        / "packets"
        / "examples"
        / "raw_intent_packet_invalid_unknown_field.json"
    )

    assert "$.provenance is required." in raw_intent_packet.validate_manifest(missing)
    assert "$.mission is not allowed." in raw_intent_packet.validate_manifest(unknown)


def test_compose_is_deterministic_with_golden_identity():
    first = raw_intent_packet.compose_manifest(load_example())
    second = raw_intent_packet.compose_manifest(load_example())

    assert first == second
    assert first["intent_sha"] == GOLDEN_INTENT_SHA


def test_status_provenance_and_parent_change_identity():
    manifest = load_example()
    baseline = raw_intent_packet.compose_manifest(manifest)["intent_sha"]

    changed_status = deepcopy(manifest)
    changed_status["status"] = "grounding"
    changed_provenance = deepcopy(manifest)
    changed_provenance["provenance"]["author"] = "another-human"
    changed_parent = deepcopy(manifest)
    changed_parent["parent_intent_sha"] = "a" * 64

    assert raw_intent_packet.compose_manifest(changed_status)["intent_sha"] != baseline
    assert raw_intent_packet.compose_manifest(changed_provenance)["intent_sha"] != baseline
    assert raw_intent_packet.compose_manifest(changed_parent)["intent_sha"] != baseline


def test_raw_intent_is_preserved_exactly():
    manifest = load_example()
    raw_value = "  Fuzzy intuition\nwith  internal spacing and Unicode: café.  "
    manifest["raw_intent"] = raw_value

    result = raw_intent_packet.compose_manifest(manifest)

    assert result["manifest"]["raw_intent"] == raw_value
    assert json.loads(result["normalized_json"])["raw_intent"] == raw_value
    assert f"```text\n{raw_value}\n```" in result["intent_md"]


def test_whitespace_only_raw_intent_is_rejected_without_trimming_valid_input():
    manifest = load_example()
    manifest["raw_intent"] = " \n\t "

    assert (
        "$.raw_intent must contain non-whitespace content."
        in raw_intent_packet.validate_manifest(manifest)
    )


def test_provenance_rejects_unknown_fields_and_naive_timestamps():
    manifest = load_example()
    manifest["provenance"]["authenticated"] = True
    assert "$.provenance.authenticated is not allowed." in (
        raw_intent_packet.validate_manifest(manifest)
    )

    manifest = load_example()
    manifest["provenance"]["captured_at"] = "2026-06-20T17:00:00"
    assert "$.provenance.captured_at must be an RFC 3339 date-time with a timezone." in (
        raw_intent_packet.validate_manifest(manifest)
    )


def test_cli_lint_and_compose(tmp_path):
    script = ROOT / "tools" / "raw_intent_packet.py"
    lint_result = subprocess.run(
        [sys.executable, str(script), "lint", str(EXAMPLE_PATH)],
        capture_output=True,
        text=True,
    )
    assert lint_result.returncode == 0
    assert "Lint passed" in lint_result.stdout

    compose_result = subprocess.run(
        [
            sys.executable,
            str(script),
            "compose",
            str(EXAMPLE_PATH),
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert compose_result.returncode == 0
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "intent.md").exists()
    assert (tmp_path / "intent_sha").read_text(
        encoding="utf-8"
    ).strip() == GOLDEN_INTENT_SHA

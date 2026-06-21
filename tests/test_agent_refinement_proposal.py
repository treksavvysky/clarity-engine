import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from tools import agent_refinement_proposal


ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "packets" / "examples" / "agent_refinement_proposal_example.json"
GOLDEN_PROPOSAL_SHA = (
    "15e7418c61243da509799ee51298b41a672e366953ef3b0696707ed6713b76c6"
)


def load_example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_is_valid_and_deterministic():
    manifest = load_example()
    assert agent_refinement_proposal.validate_manifest(manifest) == []
    first = agent_refinement_proposal.compose_manifest(manifest)
    second = agent_refinement_proposal.compose_manifest(manifest)
    assert first == second
    assert first["proposal_sha"] == GOLDEN_PROPOSAL_SHA
    assert "## Authority Boundary" in first["proposal_md"]


def test_unknown_authority_field_is_rejected():
    invalid = agent_refinement_proposal.load_json(
        ROOT
        / "packets"
        / "examples"
        / "agent_refinement_proposal_invalid_authority.json"
    )
    assert "$.approved is not allowed." in (
        agent_refinement_proposal.validate_manifest(invalid)
    )


def test_source_sha_timestamp_and_proposer_are_strict():
    manifest = load_example()
    manifest["source_intent_sha"] = "not-a-sha"
    manifest["created_at"] = "2026-06-21T23:35:00"
    manifest["proposer"]["agent"] = " "
    errors = agent_refinement_proposal.validate_manifest(manifest)
    assert any("$.source_intent_sha must match pattern" in error for error in errors)
    assert "$.created_at must be an RFC 3339 date-time with a timezone." in errors
    assert "$.proposer.agent must contain non-whitespace content." in errors


def test_grounding_sources_and_duplicate_questions_are_rejected():
    manifest = load_example()
    manifest["grounding_entries"][0]["sources"] = []
    manifest["clarification_questions"].append(
        deepcopy(manifest["clarification_questions"][0])
    )
    errors = agent_refinement_proposal.validate_manifest(manifest)
    assert any(
        error.startswith("$.grounding_entries[0].sources") for error in errors
    )
    assert "$.clarification_questions[2].id must be unique." in errors


def test_unicode_and_field_changes_affect_identity():
    manifest = load_example()
    manifest["summary"] += " Café."
    first = agent_refinement_proposal.compose_manifest(manifest)
    changed = deepcopy(manifest)
    changed["unresolved_gaps"].append("Additional evidence is required.")
    second = agent_refinement_proposal.compose_manifest(changed)
    assert first["manifest"]["summary"].endswith("Café.")
    assert "Café." in first["normalized_json"]
    assert first["proposal_sha"] != second["proposal_sha"]


def test_cli_lint_compose_and_invalid_exit(tmp_path):
    script = ROOT / "tools" / "agent_refinement_proposal.py"
    lint = subprocess.run(
        [sys.executable, str(script), "lint", str(EXAMPLE)],
        capture_output=True,
        text=True,
    )
    assert lint.returncode == 0
    assert "Lint passed" in lint.stdout

    compose = subprocess.run(
        [
            sys.executable,
            str(script),
            "compose",
            str(EXAMPLE),
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert compose.returncode == 0
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "proposal.md").exists()
    assert len((tmp_path / "proposal_sha").read_text(encoding="utf-8").strip()) == 64

    invalid = subprocess.run(
        [
            sys.executable,
            str(script),
            "lint",
            str(
                ROOT
                / "packets"
                / "examples"
                / "agent_refinement_proposal_invalid_authority.json"
            ),
        ],
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == 1
    assert "$.approved is not allowed." in invalid.stdout


def test_compose_has_no_registry_side_effects(tmp_path, monkeypatch):
    packet_root = tmp_path / "registry"
    intent_root = tmp_path / "intents"
    proposal_output = tmp_path / "proposal"
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(packet_root))
    monkeypatch.setenv("CLARITY_INTENT_REGISTRY_ROOT", str(intent_root))
    result = agent_refinement_proposal.compose_manifest(load_example())
    agent_refinement_proposal._write_composed(result, proposal_output)
    assert not packet_root.exists()
    assert not intent_root.exists()

import json
from copy import deepcopy
from pathlib import Path

import pytest

from app import intent_registry, proposal_registry
from tools import agent_refinement_proposal


ROOT = Path(__file__).resolve().parent.parent
PROPOSAL_EXAMPLE = (
    ROOT / "packets" / "examples" / "agent_refinement_proposal_example.json"
)
INTENT_EXAMPLE = ROOT / "packets" / "examples" / "raw_intent_packet_example.json"


@pytest.fixture(autouse=True)
def isolated_registries(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_INTENT_REGISTRY_ROOT", str(tmp_path / "intents"))
    monkeypatch.setenv("CLARITY_PROPOSAL_REGISTRY_ROOT", str(tmp_path / "proposals"))


def registered_source():
    manifest = json.loads(INTENT_EXAMPLE.read_text(encoding="utf-8"))
    return intent_registry.register(manifest)["intent_sha"]


def proposal_manifest(source_sha):
    manifest = json.loads(PROPOSAL_EXAMPLE.read_text(encoding="utf-8"))
    manifest["source_intent_sha"] = source_sha
    return manifest


def test_register_read_list_and_idempotency():
    source_sha = registered_source()
    manifest = proposal_manifest(source_sha)
    first = proposal_registry.register(manifest)
    second = proposal_registry.register(manifest)
    record = proposal_registry.read(first["proposal_sha"])

    assert first["registered"] is True
    assert second == {"proposal_sha": first["proposal_sha"], "registered": False}
    assert record["manifest"] == manifest
    assert record["source_intent_sha"] == source_sha
    assert proposal_registry.list_summaries(source_sha)[0]["proposal_sha"] == first[
        "proposal_sha"
    ]


def test_registration_requires_valid_source_intent():
    manifest = proposal_manifest("0" * 64)
    with pytest.raises(proposal_registry.ProposalSourceError, match="unknown_intent"):
        proposal_registry.register(manifest)


def test_read_rejects_corrupt_markdown_and_missing_source():
    source_sha = registered_source()
    manifest = proposal_manifest(source_sha)
    result = proposal_registry.register(manifest)
    record_dir = (
        proposal_registry.root_path() / source_sha / result["proposal_sha"]
    )
    (record_dir / "proposal.md").write_text("corrupt", encoding="utf-8")
    with pytest.raises(proposal_registry.CorruptProposalError, match="Markdown"):
        proposal_registry.read(result["proposal_sha"])

    composed = agent_refinement_proposal.compose_manifest(
        deepcopy(proposal_manifest(source_sha))
    )
    (record_dir / "proposal.md").write_text(
        composed["proposal_md"], encoding="utf-8"
    )
    intent_dir = intent_registry.root_path() / source_sha
    for path in intent_dir.iterdir():
        path.unlink()
    intent_dir.rmdir()
    with pytest.raises(proposal_registry.ProposalSourceError, match="unknown_intent"):
        proposal_registry.read(result["proposal_sha"])


def test_list_filters_and_omits_corrupt_records():
    first_source = registered_source()
    first = proposal_manifest(first_source)
    first_result = proposal_registry.register(first)

    second_intent = json.loads(INTENT_EXAMPLE.read_text(encoding="utf-8"))
    second_intent["raw_intent"] = "A second root intent."
    second_source = intent_registry.register(second_intent)["intent_sha"]
    second = proposal_manifest(second_source)
    second["summary"] = "Second proposal."
    second_result = proposal_registry.register(second)

    assert [item["proposal_sha"] for item in proposal_registry.list_summaries(first_source)] == [
        first_result["proposal_sha"]
    ]
    assert {item["proposal_sha"] for item in proposal_registry.list_summaries()} == {
        first_result["proposal_sha"],
        second_result["proposal_sha"],
    }

    corrupt_dir = proposal_registry.root_path() / first_source / ("f" * 64)
    corrupt_dir.mkdir()
    assert len(proposal_registry.list_summaries(first_source)) == 1


def test_invalid_and_unknown_proposal_errors_are_stable():
    with pytest.raises(proposal_registry.InvalidProposalError):
        proposal_registry.read("not-a-sha")
    with pytest.raises(proposal_registry.UnknownProposalError):
        proposal_registry.read("0" * 64)

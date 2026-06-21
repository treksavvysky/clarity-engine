import json

import pytest

from app import intent_links, intent_registry, registry
from tools import compose_packet, raw_intent_packet


@pytest.fixture(autouse=True)
def isolated_registries(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    monkeypatch.setenv(
        "CLARITY_INTENT_REGISTRY_ROOT", str(tmp_path / "intent-registry")
    )
    monkeypatch.setenv(
        "CLARITY_INTENT_LINK_ROOT", str(tmp_path / "intent-links")
    )


def _registered_graph():
    root = {
        "version": "1.0.0",
        "raw_intent": "Ship a bounded feature.",
        "status": "captured",
        "provenance": {"source": "api"},
        "constraints": ["Keep the feature bounded."],
    }
    root_sha = intent_registry.register(root)["intent_sha"]
    ready = {
        **root,
        "status": "ready_for_mission",
        "parent_intent_sha": root_sha,
        "grounding_entries": [
            {
                "kind": "verified_fact",
                "statement": "The repository has tests.",
                "sources": ["repo:tests"],
            }
        ],
    }
    grounding = dict(ready)
    grounding["status"] = "grounding"
    grounding_sha = intent_registry.register(grounding)["intent_sha"]
    ready["parent_intent_sha"] = grounding_sha
    ready_sha = intent_registry.register(ready)["intent_sha"]
    promoted = dict(ready)
    promoted["status"] = "promoted"
    promoted["parent_intent_sha"] = ready_sha
    promoted_sha = intent_registry.register(promoted)["intent_sha"]

    mission = {
        "mission": "Ship the bounded feature.",
        "current_reality": ["The repository has tests."],
        "constraints": ["Keep the feature bounded."],
        "acceptance": ["Tests pass."],
        "required_artifacts": ["Implementation and tests exist."],
        "failure_modes": ["The feature expands beyond scope."],
        "substage_gate": ["Only the bounded feature is in scope."],
    }
    normalized = compose_packet.normalize_manifest(mission)
    context_sha = compose_packet.compute_context_sha(normalized)
    registry.write(
        context_sha, normalized, compose_packet.render_packet_md(mission) + "\n"
    )
    link = {
        "version": "1.0.0",
        "intent_sha": ready_sha,
        "context_sha": context_sha,
        "promoted_intent_sha": promoted_sha,
        "approval": {"approved": True, "approved_by": "Human owner"},
        "grounding_references": [
            {
                "packet_field": "current_reality",
                "packet_index": 0,
                "intent_field": "grounding_entries",
                "intent_index": 0,
            },
            {
                "packet_field": "constraints",
                "packet_index": 0,
                "intent_field": "constraints",
                "intent_index": 0,
            },
        ],
    }
    return ready_sha, context_sha, link


def test_link_write_is_atomic_idempotent_and_readable():
    intent_sha, context_sha, link = _registered_graph()

    assert intent_links.write(link) is True
    assert intent_links.write(link) is False
    assert intent_links.read(intent_sha, context_sha)["link"] == link
    assert intent_links.list_missions(intent_sha)["missions"][0]["context_sha"] == context_sha
    assert not list(intent_links.root_path().rglob(".link-*"))


def test_link_write_rejects_conflicting_content():
    _, _, link = _registered_graph()
    assert intent_links.write(link) is True
    conflicting = json.loads(json.dumps(link))
    conflicting["approval"]["approved_by"] = "Different owner"

    with pytest.raises(intent_links.ConflictingIntentLinkError):
        intent_links.write(conflicting)


def test_link_read_detects_corrupt_mission_record():
    intent_sha, context_sha, link = _registered_graph()
    intent_links.write(link)
    record = registry._packet_dir(context_sha) / "packet.md"
    record.write_text("corrupt", encoding="utf-8")

    with pytest.raises(intent_links.CorruptIntentLinkError):
        intent_links.read(intent_sha, context_sha)


def test_link_read_detects_missing_promoted_revision():
    intent_sha, context_sha, link = _registered_graph()
    link["promoted_intent_sha"] = raw_intent_packet.compose_manifest(
        {
            "version": "1.0.0",
            "raw_intent": "Missing.",
            "status": "captured",
            "provenance": {"source": "api"},
        }
    )["intent_sha"]
    intent_links.write(link)

    with pytest.raises(intent_links.CorruptIntentLinkError):
        intent_links.read(intent_sha, context_sha)

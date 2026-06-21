import json
from copy import deepcopy
from pathlib import Path

import pytest

from app import intent_registry, intent_workflow

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "packets" / "examples" / "raw_intent_packet_example.json"


@pytest.fixture(autouse=True)
def isolated_intent_registry(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLARITY_INTENT_REGISTRY_ROOT", str(tmp_path / "intent-registry")
    )


@pytest.fixture
def root_manifest():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


@pytest.fixture
def root_sha(root_manifest):
    return intent_registry.register(root_manifest)["intent_sha"]


def verified_fact(statement="The repository contains app/main.py."):
    return {
        "kind": "verified_fact",
        "statement": statement,
        "sources": ["repo:app/main.py"],
    }


def test_grounding_revision_appends_entries_and_preserves_parent(root_manifest, root_sha):
    parent_before = intent_registry.read(root_sha)
    result = intent_workflow.register_grounding_revision(
        root_sha,
        {
            "entries": [
                {
                    "kind": "observation",
                    "statement": "The API uses FastAPI.",
                    "sources": ["repo:app/main.py"],
                }
            ],
            "unresolved_gaps": ["Confirm deployment owner."],
        },
    )

    child = intent_registry.read(result["intent_sha"])["manifest"]
    assert result["status"] == "grounding"
    assert child["parent_intent_sha"] == root_sha
    assert child["grounding_entries"][0]["kind"] == "observation"
    assert child["unresolved_gaps"] == ["Confirm deployment owner."]
    assert intent_registry.read(root_sha) == parent_before


def test_grounding_revision_is_idempotent(root_sha):
    body = {"entries": [verified_fact()], "status": "grounding"}
    first = intent_workflow.register_grounding_revision(root_sha, body)
    second = intent_workflow.register_grounding_revision(root_sha, body)

    assert first["intent_sha"] == second["intent_sha"]
    assert first["registered"] is True
    assert second["registered"] is False


def test_grounding_request_rejects_unsupported_fields_and_invalid_sources(root_sha):
    with pytest.raises(intent_registry.InvalidIntentError, match="unsupported"):
        intent_workflow.build_grounding_revision(
            root_sha, {"raw_intent": "replacement"}
        )
    with pytest.raises(intent_registry.InvalidIntentError, match="sources"):
        intent_workflow.build_grounding_revision(
            root_sha,
            {
                "entries": [
                    {
                        "kind": "verified_fact",
                        "statement": "Unsourced.",
                        "sources": [],
                    }
                ]
            },
        )


def test_ready_for_mission_requires_fact_no_open_questions_and_no_gaps(root_sha):
    grounding = intent_workflow.register_grounding_revision(
        root_sha, {"entries": [verified_fact()], "status": "grounding"}
    )
    grounding_sha = grounding["intent_sha"]

    ready = intent_workflow.register_grounding_revision(
        grounding_sha, {"status": "ready_for_mission", "unresolved_gaps": []}
    )
    assert ready["status"] == "ready_for_mission"

    gap_revision = intent_workflow.register_grounding_revision(
        root_sha,
        {
            "entries": [verified_fact()],
            "unresolved_gaps": ["Still unknown."],
            "status": "grounding",
        },
    )
    with pytest.raises(intent_registry.BrokenLineageError, match="unresolved_gaps"):
        intent_workflow.build_grounding_revision(
            gap_revision["intent_sha"], {"status": "ready_for_mission"}
        )


def test_direct_register_cannot_bypass_readiness(root_manifest, root_sha):
    grounding = deepcopy(root_manifest)
    grounding["status"] = "grounding"
    grounding["parent_intent_sha"] = root_sha
    grounding_sha = intent_registry.register(grounding)["intent_sha"]
    child = deepcopy(root_manifest)
    child["status"] = "ready_for_mission"
    child["parent_intent_sha"] = grounding_sha

    with pytest.raises(intent_registry.BrokenLineageError, match="verified_fact"):
        intent_registry.register(child)


def test_clarification_questions_and_answers_are_traceable(root_sha):
    grounding = intent_workflow.register_grounding_revision(
        root_sha, {"entries": [verified_fact()]}
    )
    grounding_sha = grounding["intent_sha"]
    questioned = intent_workflow.register_clarification_revision(
        grounding_sha,
        {
            "questions": [
                {"id": "deployment-owner", "question": "Who owns deployment?"},
                {"id": "target-host", "question": "Which host runs the service?"},
            ]
        },
    )
    questioned_manifest = intent_registry.read(questioned["intent_sha"])["manifest"]
    assert questioned["status"] == "clarification_needed"
    assert [entry["id"] for entry in questioned_manifest["clarifications"]] == [
        "deployment-owner",
        "target-host",
    ]

    answered = intent_workflow.register_clarification_revision(
        questioned["intent_sha"],
        {
            "answers": [
                {
                    "id": "deployment-owner",
                    "answer": "The platform maintainer.",
                }
            ]
        },
    )
    answered_manifest = intent_registry.read(answered["intent_sha"])["manifest"]
    assert answered["status"] == "grounding"
    by_id = {entry["id"]: entry for entry in answered_manifest["clarifications"]}
    assert by_id["deployment-owner"]["status"] == "answered"
    assert by_id["target-host"]["status"] == "open"
    assert answered_manifest["grounding_entries"] == questioned_manifest[
        "grounding_entries"
    ]


def test_clarification_rejects_unknown_duplicate_and_reanswered_ids(root_sha):
    grounding_sha = intent_workflow.register_grounding_revision(
        root_sha, {"entries": [verified_fact()]}
    )["intent_sha"]
    questioned_sha = intent_workflow.register_clarification_revision(
        grounding_sha,
        {"questions": [{"id": "owner", "question": "Who owns this?"}]},
    )["intent_sha"]

    with pytest.raises(intent_registry.InvalidIntentError, match="not found"):
        intent_workflow.build_clarification_revision(
            questioned_sha, {"answers": [{"id": "missing", "answer": "Nobody."}]}
        )
    with pytest.raises(intent_registry.InvalidIntentError, match="already exists"):
        intent_workflow.build_clarification_revision(
            questioned_sha,
            {"questions": [{"id": "owner", "question": "Duplicate?"}]},
        )

    answered_sha = intent_workflow.register_clarification_revision(
        questioned_sha, {"answers": [{"id": "owner", "answer": "The maintainer."}]}
    )["intent_sha"]
    with pytest.raises(intent_registry.InvalidIntentError, match="already answered"):
        intent_workflow.build_clarification_revision(
            answered_sha, {"answers": [{"id": "owner", "answer": "Again."}]}
        )


def test_ready_rejects_open_clarification(root_sha):
    grounding_sha = intent_workflow.register_grounding_revision(
        root_sha, {"entries": [verified_fact()]}
    )["intent_sha"]
    questioned_sha = intent_workflow.register_clarification_revision(
        grounding_sha,
        {"questions": [{"id": "owner", "question": "Who owns this?"}]},
    )["intent_sha"]
    resumed_sha = intent_workflow.register_grounding_revision(
        questioned_sha, {"status": "grounding"}
    )["intent_sha"]

    with pytest.raises(intent_registry.BrokenLineageError, match="clarifications"):
        intent_workflow.build_grounding_revision(
            resumed_sha, {"status": "ready_for_mission"}
        )

import json
from pathlib import Path

import pytest

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


def register_root(client, root_manifest):
    return client.post("/intents/register", json=root_manifest).json()["intent_sha"]


def test_grounding_endpoint_creates_child_without_mutating_parent(client, root_manifest):
    root_sha = register_root(client, root_manifest)
    parent_before = client.get(f"/intents/{root_sha}").json()
    response = client.post(
        f"/intents/{root_sha}/grounding",
        json={
            "entries": [
                {
                    "kind": "verified_fact",
                    "statement": "The repository contains app/main.py.",
                    "sources": ["repo:app/main.py"],
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parent_intent_sha"] == root_sha
    assert payload["status"] == "grounding"
    child = client.get(f"/intents/{payload['intent_sha']}").json()["manifest"]
    assert child["grounding_entries"][0]["kind"] == "verified_fact"
    assert client.get(f"/intents/{root_sha}").json() == parent_before


def test_clarification_endpoint_questions_then_answers(client, root_manifest):
    root_sha = register_root(client, root_manifest)
    grounding_sha = client.post(
        f"/intents/{root_sha}/grounding",
        json={
            "entries": [
                {
                    "kind": "verified_fact",
                    "statement": "The repository contains app/main.py.",
                    "sources": ["repo:app/main.py"],
                }
            ]
        },
    ).json()["intent_sha"]
    questioned = client.post(
        f"/intents/{grounding_sha}/clarifications",
        json={
            "questions": [
                {"id": "owner", "question": "Who owns deployment?"}
            ]
        },
    )
    assert questioned.status_code == 200
    assert questioned.json()["status"] == "clarification_needed"
    listing = client.get("/intents").json()["intents"]
    questioned_summary = next(
        item for item in listing if item["intent_sha"] == questioned.json()["intent_sha"]
    )
    assert questioned_summary["clarifications_needed_count"] == 2

    answered = client.post(
        f"/intents/{questioned.json()['intent_sha']}/clarifications",
        json={"answers": [{"id": "owner", "answer": "The maintainer."}]},
    )
    assert answered.status_code == 200
    assert answered.json()["status"] == "grounding"
    detail = client.get(f"/intents/{answered.json()['intent_sha']}").json()
    assert detail["manifest"]["clarifications"][0]["answer"] == "The maintainer."


def test_ready_endpoint_requires_grounding_and_closed_questions(client, root_manifest):
    root_sha = register_root(client, root_manifest)
    response = client.post(
        f"/intents/{root_sha}/grounding",
        json={"status": "ready_for_mission"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "broken_lineage"


def test_mutation_endpoint_rejects_unsupported_fields(client, root_manifest):
    root_sha = register_root(client, root_manifest)
    response = client.post(
        f"/intents/{root_sha}/grounding",
        json={"raw_intent": "replacement"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_intent"


def test_complete_workflow_reaches_ready_for_mission(client, root_manifest):
    root_sha = register_root(client, root_manifest)
    grounding_sha = client.post(
        f"/intents/{root_sha}/grounding",
        json={
            "entries": [
                {
                    "kind": "verified_fact",
                    "statement": "The repository contains app/main.py.",
                    "sources": ["repo:app/main.py"],
                }
            ],
            "unresolved_gaps": ["Confirm deployment owner."],
        },
    ).json()["intent_sha"]
    questioned_sha = client.post(
        f"/intents/{grounding_sha}/clarifications",
        json={
            "questions": [
                {"id": "owner", "question": "Who owns deployment?"}
            ]
        },
    ).json()["intent_sha"]
    answered_sha = client.post(
        f"/intents/{questioned_sha}/clarifications",
        json={"answers": [{"id": "owner", "answer": "The maintainer."}]},
    ).json()["intent_sha"]
    ready = client.post(
        f"/intents/{answered_sha}/grounding",
        json={"unresolved_gaps": [], "status": "ready_for_mission"},
    )

    assert ready.status_code == 200
    assert ready.json()["status"] == "ready_for_mission"
    manifest = client.get(f"/intents/{ready.json()['intent_sha']}").json()["manifest"]
    assert manifest["grounding_entries"][0]["kind"] == "verified_fact"
    assert manifest["clarifications"][0]["status"] == "answered"
    assert "unresolved_gaps" not in manifest

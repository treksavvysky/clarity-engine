"""Tests for Stage-07 raw intent draft endpoint."""

import pytest

from app import registry


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    yield


def test_intents_draft_returns_linted_manifest_without_registering(client):
    response = client.post(
        "/intents/draft",
        json={
            "raw_intent": "I should work on code-server.",
            "context": ["code-server is part of the active dev environment."],
            "constraints": ["Do not change code-server configuration yet."],
            "route": ["SMI", "Clarity Engine", "Infrastructure Registry"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert payload["warnings"] == []
    assert payload["registered"] is False

    manifest = payload["manifest"]
    assert manifest["stage"] == "Stage-07"
    assert manifest["substage"] == "raw-intent-draft"
    assert "Raw intent received: I should work on code-server." in manifest["current_reality"]
    assert "Caller supplied context: code-server is part of the active dev environment." in manifest["current_reality"]
    assert "Do not change code-server configuration yet." in manifest["constraints"]
    assert "Route through: SMI -> Clarity Engine -> Infrastructure Registry." in manifest["constraints"]
    assert (
        "Smallest next action: Create a short inventory note for code-server "
        "that records current state, access path, known constraint, and first improvement target."
    ) in manifest["required_artifacts"]
    assert registry.read(payload["context_sha"]) is None


def test_intents_draft_requires_raw_intent(client):
    response = client.post("/intents/draft", json={"context": ["known fact"]})

    assert response.status_code == 400
    assert response.json()["detail"] == "'raw_intent' must be a non-empty string."


def test_intents_draft_rejects_non_string_route_entries(client):
    response = client.post(
        "/intents/draft",
        json={"raw_intent": "Inventory code-server.", "route": ["SMI", 7]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "'route' entry at index 1 must be a non-empty string."


def test_intents_draft_is_deterministic(client):
    body = {"raw_intent": "Inventory code-server.", "route": ["Clarity Engine"]}

    first = client.post("/intents/draft", json=body)
    second = client.post("/intents/draft", json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()

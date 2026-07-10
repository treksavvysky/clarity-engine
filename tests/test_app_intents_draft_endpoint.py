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
    assert manifest["stage"] == "Strategic Clarification"
    assert manifest["substage"] == "Clarified Intent"
    assert "Raw intent captured: I should work on code-server." in manifest["current_reality"]
    assert "code-server is part of the active dev environment." in manifest["current_reality"]
    assert "Do not change code-server configuration yet." in manifest["constraints"]
    assert "Route: SMI -> Clarity Engine -> Infrastructure Registry." in manifest["constraints"]
    assert "Strategic mission packet for: code-server" in manifest["required_artifacts"]
    assert "Smallest next action: Create a short strategy note for 'code-server' defining access path, constraints, and first milestone." in manifest["required_artifacts"]
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


def test_intents_draft_devops_diagnosis_warning(client):
    body = {"raw_intent": "Please fix a bug in the build pipeline."}
    response = client.post("/intents/draft", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    warnings = payload["warnings"]
    assert any("DevOps Route" in w for w in warnings)
    manifest = payload["manifest"]
    assert "DIAGNOSIS WARNING: This intent relates to DevOps continuous improvement (issue tracker) rather than strategic design." in manifest["current_reality"]
    assert "Route: DevOps Issue Tracker -> Continuous Improvement Cycle." in manifest["constraints"]


def test_intents_draft_2_0_conversational_keys(client):
    response = client.post(
        "/intents/draft",
        json={
            "raw_intent": "Refactor interface to support step wizard.",
            "human_constraints": "Only 30 minutes left.\nNo TailwindCSS allowed.",
            "additional_context": "Vite project configuration.\nSMI routing is active.",
            "route": "Strategic Plan",
            "known_project_context": "UI directory is static for now.",
            "desired_output_mode": "mission"
        }
    )

    assert response.status_code == 200
    payload = response.json()
    manifest = payload["manifest"]

    # Constraints extraction (newline split)
    assert "Only 30 minutes left." in manifest["constraints"]
    assert "No TailwindCSS allowed." in manifest["constraints"]
    assert "Route: Strategic Plan." in manifest["constraints"]

    # Context & Project context extraction (newline split)
    assert "Raw intent captured: Refactor interface to support step wizard." in manifest["current_reality"]
    assert "Known project context: UI directory is static for now." in manifest["current_reality"]
    assert "Vite project configuration." in manifest["current_reality"]
    assert "SMI routing is active." in manifest["current_reality"]


def test_intents_draft_rejects_invalid_output_mode(client):
    response = client.post(
        "/intents/draft",
        json={
            "raw_intent": "Refactor interface.",
            "desired_output_mode": "invalid_mode"
        }
    )
    assert response.status_code == 400
    assert "desired_output_mode" in response.json()["detail"]


def test_intents_draft_rejects_non_string_project_context(client):
    response = client.post(
        "/intents/draft",
        json={
            "raw_intent": "Refactor interface.",
            "known_project_context": 12345
        }
    )
    assert response.status_code == 400
    assert "known_project_context" in response.json()["detail"]

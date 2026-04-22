"""Tests for Stage-03.1 registry endpoints."""

import pytest


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    """Point the registry at a temp dir for every test in this module."""
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    yield


def test_register_creates_packet_and_is_idempotent(client, example_manifest):
    first = client.post("/packets/register", json=example_manifest)
    assert first.status_code == 200
    payload = first.json()
    assert payload["registered"] is True
    assert len(payload["context_sha"]) == 64

    second = client.post("/packets/register", json=example_manifest)
    assert second.status_code == 200
    repeat = second.json()
    assert repeat["context_sha"] == payload["context_sha"]
    assert repeat["registered"] is False


def test_get_packet_returns_stored_artifacts(client, example_manifest):
    registered = client.post("/packets/register", json=example_manifest).json()
    sha = registered["context_sha"]

    response = client.get(f"/packets/{sha}")
    assert response.status_code == 200
    body = response.json()
    assert body["context_sha"] == sha
    assert body["manifest"]["mission"] == example_manifest["mission"]
    assert body["packet_md"].startswith("# Context Packet")


def test_get_packet_unknown_sha_returns_404(client):
    response = client.get("/packets/" + "0" * 64)
    assert response.status_code == 404


def test_list_packets_returns_registered_entries(client, example_manifest):
    assert client.get("/packets").json() == {"packets": []}

    registered = client.post("/packets/register", json=example_manifest).json()
    listing = client.get("/packets").json()
    assert listing == {
        "packets": [
            {
                "context_sha": registered["context_sha"],
                "mission": example_manifest["mission"],
            }
        ]
    }


def test_compose_endpoint_remains_side_effect_free(client, example_manifest):
    response = client.post("/packets/compose", json=example_manifest)
    assert response.status_code == 200
    assert client.get("/packets").json() == {"packets": []}

"""Tests for Stage-03.2 /packets/diff endpoint."""

import copy

import pytest


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    yield


def test_diff_identical_manifests_is_empty(client, example_manifest):
    response = client.post(
        "/packets/diff",
        json={"left": example_manifest, "right": example_manifest},
    )
    assert response.status_code == 200
    assert response.json() == {"added": {}, "removed": {}, "changed": {}}


def test_diff_reports_added_removed_changed(client, example_manifest):
    left = copy.deepcopy(example_manifest)
    right = copy.deepcopy(example_manifest)

    left["project"] = "Old Project"
    right["project"] = "New Project"
    right["risk_flags"] = ["missing_info"]
    del right["notes"]

    response = client.post("/packets/diff", json={"left": left, "right": right})
    assert response.status_code == 200
    body = response.json()

    assert body["added"] == {"risk_flags": ["missing_info"]}
    assert body["removed"] == {"notes": left["notes"]}
    assert body["changed"] == {
        "project": {"before": "Old Project", "after": "New Project"},
    }


def test_diff_accepts_sha_references(client, example_manifest):
    left_manifest = copy.deepcopy(example_manifest)
    right_manifest = copy.deepcopy(example_manifest)
    right_manifest["mission"] = "A different mission statement entirely."

    left_sha = client.post("/packets/register", json=left_manifest).json()["context_sha"]
    right_sha = client.post("/packets/register", json=right_manifest).json()["context_sha"]

    response = client.post("/packets/diff", json={"left": left_sha, "right": right_sha})
    assert response.status_code == 200
    body = response.json()
    assert "mission" in body["changed"]
    assert body["added"] == {} and body["removed"] == {}


def test_diff_unknown_sha_returns_404(client, example_manifest):
    response = client.post(
        "/packets/diff",
        json={"left": "0" * 64, "right": example_manifest},
    )
    assert response.status_code == 404


def test_diff_missing_sides_returns_400(client, example_manifest):
    response = client.post("/packets/diff", json={"left": example_manifest})
    assert response.status_code == 400

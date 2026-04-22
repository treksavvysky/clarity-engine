"""Tests for Stage-04: /packets/enqueue and callback_url field."""

import copy

import pytest

from tools import lint_packet


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    yield


def _errors_only(issues):
    return [i for i in issues if not i.startswith("[warning]")]


def test_enqueue_returns_jct_envelope(client, example_manifest):
    response = client.post("/packets/enqueue", json=example_manifest)
    assert response.status_code == 200
    body = response.json()

    assert body["task_id"] == body["context_sha"]
    assert len(body["context_sha"]) == 64
    assert body["mission"] == example_manifest["mission"]
    assert body["manifest"]["mission"] == example_manifest["mission"]
    assert body["packet_md"].startswith("# Context Packet")
    assert body["allowed_actions"] == []
    assert body["evidence_requirements"] == []
    assert body["risk_flags"] == []
    assert body["callback_url"] is None
    assert body["registered"] is True


def test_enqueue_is_idempotent(client, example_manifest):
    first = client.post("/packets/enqueue", json=example_manifest).json()
    second = client.post("/packets/enqueue", json=example_manifest).json()
    assert first["task_id"] == second["task_id"]
    assert first["context_sha"] == second["context_sha"]
    assert first["packet_md"] == second["packet_md"]
    assert second["registered"] is False


def test_enqueue_persists_to_registry(client, example_manifest):
    envelope = client.post("/packets/enqueue", json=example_manifest).json()
    fetched = client.get(f"/packets/{envelope['context_sha']}")
    assert fetched.status_code == 200


def test_enqueue_roundtrips_callback_and_action_fields(client, example_manifest):
    manifest = copy.deepcopy(example_manifest)
    manifest["callback_url"] = "https://jct.example.com/hook"
    manifest["allowed_actions"] = ["git_read", "filesystem_read"]
    manifest["evidence_requirements"] = ["pr_link", "test_output"]
    manifest["risk_flags"] = ["needs_human_signoff"]

    body = client.post("/packets/enqueue", json=manifest).json()
    assert body["callback_url"] == "https://jct.example.com/hook"
    assert body["allowed_actions"] == ["git_read", "filesystem_read"]
    assert body["evidence_requirements"] == ["pr_link", "test_output"]
    assert body["risk_flags"] == ["needs_human_signoff"]


def test_callback_url_accepts_http_and_https(example_manifest):
    schema = lint_packet.load_schema()
    for url in ("http://hooks.local/x", "https://orchestrator/cb?task=1"):
        m = copy.deepcopy(example_manifest)
        m["callback_url"] = url
        assert _errors_only(lint_packet.lint_manifest(m, schema)) == []


def test_callback_url_rejects_non_url(example_manifest):
    schema = lint_packet.load_schema()
    m = copy.deepcopy(example_manifest)
    m["callback_url"] = "not a url"
    issues = _errors_only(lint_packet.lint_manifest(m, schema))
    assert any("callback_url" in i for i in issues)

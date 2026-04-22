"""Tests for Stage-03.3 /packets/{sha}/ancestors endpoint and parent_sha schema field."""

import copy

import pytest

from tools import lint_packet


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    yield


def _register(client, manifest: dict) -> str:
    return client.post("/packets/register", json=manifest).json()["context_sha"]


def _errors_only(issues: list[str]) -> list[str]:
    return [i for i in issues if not i.startswith("[warning]")]


def test_parent_sha_is_optional_and_passes_lint(example_manifest):
    schema = lint_packet.load_schema()
    assert _errors_only(lint_packet.lint_manifest(example_manifest, schema)) == []

    with_parent = copy.deepcopy(example_manifest)
    with_parent["parent_sha"] = "a" * 64
    assert _errors_only(lint_packet.lint_manifest(with_parent, schema)) == []


def test_parent_sha_rejects_non_hex(example_manifest):
    schema = lint_packet.load_schema()
    bad = copy.deepcopy(example_manifest)
    bad["parent_sha"] = "not-a-sha"
    issues = lint_packet.lint_manifest(bad, schema)
    assert any("parent_sha" in i for i in issues)


def test_ancestors_empty_for_rootless_packet(client, example_manifest):
    sha = _register(client, example_manifest)
    response = client.get(f"/packets/{sha}/ancestors")
    assert response.status_code == 200
    assert response.json() == {"context_sha": sha, "ancestors": []}


def test_ancestors_walk_parent_chain(client, example_manifest):
    a = copy.deepcopy(example_manifest)
    sha_a = _register(client, a)

    b = copy.deepcopy(example_manifest)
    b["mission"] = "Derived from A."
    b["parent_sha"] = sha_a
    sha_b = _register(client, b)

    c = copy.deepcopy(example_manifest)
    c["mission"] = "Derived from B."
    c["parent_sha"] = sha_b
    sha_c = _register(client, c)

    response = client.get(f"/packets/{sha_c}/ancestors")
    assert response.status_code == 200
    assert response.json() == {"context_sha": sha_c, "ancestors": [sha_b, sha_a]}


def test_ancestors_unknown_sha_returns_404(client):
    response = client.get(f"/packets/{'0' * 64}/ancestors")
    assert response.status_code == 404


def test_packet_md_includes_parent_sha_when_present(client, example_manifest):
    sha_a = _register(client, example_manifest)
    derived = copy.deepcopy(example_manifest)
    derived["mission"] = "A child packet."
    derived["parent_sha"] = sha_a
    sha_b = _register(client, derived)
    packet_md = client.get(f"/packets/{sha_b}").json()["packet_md"]
    assert f"Parent SHA:** {sha_a}" in packet_md

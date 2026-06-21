import json
from copy import deepcopy
from pathlib import Path

import pytest

from app import intent_registry

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "packets" / "examples" / "raw_intent_packet_example.json"


@pytest.fixture(autouse=True)
def isolated_intent_registry(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLARITY_INTENT_REGISTRY_ROOT", str(tmp_path / "intent-registry")
    )


@pytest.fixture
def intent_manifest():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_lint_and_compose_are_side_effect_free(client, intent_manifest):
    lint = client.post("/intents/lint", json=intent_manifest)
    assert lint.status_code == 200
    assert lint.json() == {"ok": True, "errors": [], "warnings": []}

    compose = client.post("/intents/compose", json=intent_manifest)
    assert compose.status_code == 200
    assert compose.json()["intent_sha"] == (
        "0d0c7657719231ad5f8d778dbe64b58f4bb26a664afaeb4ded590fb6620aa478"
    )
    assert client.get("/intents").json() == {"intents": []}


def test_lint_reports_invalid_manifest_without_http_failure(client, intent_manifest):
    del intent_manifest["provenance"]
    response = client.post("/intents/lint", json=intent_manifest)
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "$.provenance is required." in response.json()["errors"]


def test_compose_invalid_manifest_returns_stable_error(client, intent_manifest):
    intent_manifest["status"] = "unknown"
    response = client.post("/intents/compose", json=intent_manifest)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_intent"


def test_register_list_and_get(client, intent_manifest):
    registered = client.post("/intents/register", json=intent_manifest)
    assert registered.status_code == 200
    payload = registered.json()
    assert payload["registered"] is True

    repeat = client.post("/intents/register", json=intent_manifest)
    assert repeat.json() == {
        "intent_sha": payload["intent_sha"],
        "registered": False,
    }

    listing = client.get("/intents").json()["intents"]
    assert listing == [
        {
            "intent_sha": payload["intent_sha"],
            "status": "captured",
            "raw_intent_preview": (
                "The Clarity Engine may need a durable context layer so coding agents can "
                "ground vague human intent before drafting a ..."
            ),
            "source": "ui",
            "parent_intent_sha": None,
            "clarifications_needed_count": 1,
            "unresolved_gaps_count": 0,
        }
    ]

    detail = client.get(f"/intents/{payload['intent_sha']}")
    assert detail.status_code == 200
    assert detail.json()["manifest"] == intent_manifest
    assert detail.json()["intent_md"].startswith("# Raw Intent Packet")


def test_register_rejects_illegal_revision(client, intent_manifest):
    root_sha = client.post("/intents/register", json=intent_manifest).json()["intent_sha"]
    child = deepcopy(intent_manifest)
    child["status"] = "ready_for_mission"
    child["parent_intent_sha"] = root_sha

    response = client.post("/intents/register", json=child)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "broken_lineage"


def test_ancestors_returns_nearest_parent_first(client, intent_manifest):
    root_sha = client.post("/intents/register", json=intent_manifest).json()["intent_sha"]
    grounding = deepcopy(intent_manifest)
    grounding["status"] = "grounding"
    grounding["parent_intent_sha"] = root_sha
    grounding_sha = client.post("/intents/register", json=grounding).json()["intent_sha"]
    ready = deepcopy(intent_manifest)
    ready["status"] = "ready_for_mission"
    ready["parent_intent_sha"] = grounding_sha
    ready["grounding_entries"] = [
        {
            "kind": "verified_fact",
            "statement": "The repository contains app/main.py.",
            "sources": ["repo:app/main.py"],
        }
    ]
    ready_sha = client.post("/intents/register", json=ready).json()["intent_sha"]

    response = client.get(f"/intents/{ready_sha}/ancestors")
    assert response.status_code == 200
    assert response.json()["ancestors"] == [
        {
            "intent_sha": grounding_sha,
            "status": "grounding",
            "parent_intent_sha": root_sha,
        },
        {
            "intent_sha": root_sha,
            "status": "captured",
            "parent_intent_sha": None,
        },
    ]


def test_get_unknown_invalid_and_corrupt_return_stable_errors(
    client, intent_manifest
):
    unknown = client.get("/intents/" + "0" * 64)
    assert unknown.status_code == 404
    assert unknown.json()["detail"]["code"] == "unknown_intent"

    invalid = client.get("/intents/not-a-sha")
    assert invalid.status_code == 400
    assert invalid.json()["detail"]["code"] == "invalid_intent"

    result = client.post("/intents/compose", json=intent_manifest).json()
    record_dir = intent_registry.root_path() / result["intent_sha"]
    record_dir.mkdir(parents=True)
    (record_dir / "manifest.json").write_text(
        json.dumps(intent_manifest), encoding="utf-8"
    )
    corrupt = client.get(f"/intents/{result['intent_sha']}")
    assert corrupt.status_code == 409
    assert corrupt.json()["detail"]["code"] == "corrupt_intent_record"


def test_diff_inline_and_registered_intents(client, intent_manifest):
    root = client.post("/intents/register", json=intent_manifest).json()["intent_sha"]
    changed = deepcopy(intent_manifest)
    changed["status"] = "grounding"
    changed["parent_intent_sha"] = root
    changed_sha = client.post("/intents/register", json=changed).json()["intent_sha"]

    response = client.post(
        "/intents/diff", json={"left": root, "right": changed_sha}
    )
    assert response.status_code == 200
    assert response.json()["added"] == {"parent_intent_sha": root}
    assert response.json()["changed"]["status"] == {
        "before": "captured",
        "after": "grounding",
    }

    inline = client.post(
        "/intents/diff", json={"left": intent_manifest, "right": intent_manifest}
    )
    assert inline.json() == {"added": {}, "removed": {}, "changed": {}}


def test_diff_rejects_invalid_inline_manifest(client, intent_manifest):
    invalid = deepcopy(intent_manifest)
    invalid["mission"] = "not allowed"
    response = client.post(
        "/intents/diff", json={"left": invalid, "right": intent_manifest}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_intent"


def test_legacy_intents_draft_response_is_unchanged(client):
    body = {
        "raw_intent": "Inventory code-server.",
        "route": ["Clarity Engine"],
    }
    response = client.post("/intents/draft", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["context_sha"] == (
        "96d2c2f6a076963a0a79e823a4fb1c46e08b52001e7eab67048ed9dda65b738f"
    )
    assert payload["registered"] is False
    assert client.get("/intents").json() == {"intents": []}

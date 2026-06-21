import copy
import json
from pathlib import Path

import pytest

from app import intent_links, intent_registry, registry

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "packets" / "examples" / "raw_intent_packet_example.json"


@pytest.fixture(autouse=True)
def isolated_registries(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    monkeypatch.setenv(
        "CLARITY_INTENT_REGISTRY_ROOT", str(tmp_path / "intent-registry")
    )
    monkeypatch.setenv(
        "CLARITY_INTENT_LINK_ROOT", str(tmp_path / "intent-links")
    )


@pytest.fixture
def ready_intent(client):
    root = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    root_sha = client.post("/intents/register", json=root).json()["intent_sha"]
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
    ready = client.post(
        f"/intents/{grounding_sha}/grounding",
        json={"status": "ready_for_mission"},
    )
    assert ready.status_code == 200
    return ready.json()["intent_sha"]


@pytest.fixture
def promotion_request():
    return {
        "mission_packet": {
            "project": "Clarity Engine",
            "stage": "Cycle 6",
            "substage": "promotion",
            "version": "1.0.0",
            "mission": "Verify the promotion workflow.",
            "current_reality": ["The repository contains app/main.py."],
            "constraints": ["Do not build a general-purpose context platform."],
            "acceptance": ["The promotion API returns all registered identities."],
            "required_artifacts": ["Promotion records exist in all three registries."],
            "failure_modes": ["Promotion enqueues or executes work."],
            "substage_gate": ["Only approved promotion is in scope."],
        },
        "approval": {
            "approved": True,
            "approved_by": "Human product owner",
            "reference": "CLARITY-EN-28",
        },
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


def test_promotion_registers_three_records_and_is_idempotent(
    client, ready_intent, promotion_request
):
    first = client.post(
        f"/intents/{ready_intent}/promote", json=promotion_request
    )
    assert first.status_code == 200
    payload = first.json()
    assert payload["mission_registered"] is True
    assert payload["link_registered"] is True
    assert payload["intent_registered"] is True
    assert registry.read(payload["context_sha"]) is not None
    assert intent_registry.read(payload["promoted_intent_sha"])["manifest"]["status"] == "promoted"
    assert intent_links.read(ready_intent, payload["context_sha"])["link"] == payload["link"]

    second = client.post(
        f"/intents/{ready_intent}/promote", json=promotion_request
    )
    assert second.status_code == 200
    repeat = second.json()
    assert repeat["context_sha"] == payload["context_sha"]
    assert repeat["promoted_intent_sha"] == payload["promoted_intent_sha"]
    assert repeat["mission_registered"] is False
    assert repeat["link_registered"] is False
    assert repeat["intent_registered"] is False


def test_promotion_requires_ready_intent(client, promotion_request):
    root = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    root_sha = client.post("/intents/register", json=root).json()["intent_sha"]

    response = client.post(
        f"/intents/{root_sha}/promote", json=promotion_request
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_promotion"
    assert registry.list_shas() == []
    assert not intent_links.root_path().exists()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda request: request["approval"].update({"approved": False}),
        lambda request: request["approval"].update({"approved_by": " "}),
        lambda request: request.update({"grounding_references": []}),
        lambda request: request["grounding_references"].pop(),
        lambda request: request["grounding_references"][0].update(
            {"intent_field": "constraints"}
        ),
        lambda request: request["mission_packet"].pop("acceptance"),
    ],
)
def test_invalid_promotion_has_no_registry_side_effects(
    client, ready_intent, promotion_request, mutate
):
    request = copy.deepcopy(promotion_request)
    mutate(request)
    response = client.post(f"/intents/{ready_intent}/promote", json=request)

    assert response.status_code == 400
    assert registry.list_shas() == []
    assert not intent_links.root_path().exists()
    assert len(intent_registry.list_shas()) == 3


def test_conflicting_approval_fails_without_new_records(
    client, ready_intent, promotion_request
):
    first = client.post(
        f"/intents/{ready_intent}/promote", json=promotion_request
    ).json()
    before_missions = registry.list_shas()
    before_intents = intent_registry.list_shas()
    conflicting = copy.deepcopy(promotion_request)
    conflicting["approval"]["approved_by"] = "Different owner"

    response = client.post(
        f"/intents/{ready_intent}/promote", json=conflicting
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "conflicting_intent_link"
    assert registry.list_shas() == before_missions
    assert intent_registry.list_shas() == before_intents
    assert intent_links.read(ready_intent, first["context_sha"])["link"]["approval"][
        "approved_by"
    ] == "Human product owner"


def test_linked_missions_endpoint_returns_promoted_packet(
    client, ready_intent, promotion_request
):
    promoted = client.post(
        f"/intents/{ready_intent}/promote", json=promotion_request
    ).json()
    response = client.get(f"/intents/{ready_intent}/missions")

    assert response.status_code == 200
    assert response.json() == {
        "intent_sha": ready_intent,
        "missions": [
            {
                "context_sha": promoted["context_sha"],
                "mission": "Verify the promotion workflow.",
                "promoted_intent_sha": promoted["promoted_intent_sha"],
                "approval": promotion_request["approval"],
                "grounding_references": promotion_request["grounding_references"],
            }
        ],
    }

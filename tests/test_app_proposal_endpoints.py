import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
PROPOSAL_EXAMPLE = (
    ROOT / "packets" / "examples" / "agent_refinement_proposal_example.json"
)
INTENT_EXAMPLE = ROOT / "packets" / "examples" / "raw_intent_packet_example.json"


@pytest.fixture(autouse=True)
def isolated_registries(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_INTENT_REGISTRY_ROOT", str(tmp_path / "intents"))
    monkeypatch.setenv("CLARITY_PROPOSAL_REGISTRY_ROOT", str(tmp_path / "proposals"))


def source_and_proposal(client):
    intent = json.loads(INTENT_EXAMPLE.read_text(encoding="utf-8"))
    source_sha = client.post("/intents/register", json=intent).json()["intent_sha"]
    proposal = json.loads(PROPOSAL_EXAMPLE.read_text(encoding="utf-8"))
    proposal["source_intent_sha"] = source_sha
    return source_sha, proposal


def test_lint_compose_are_side_effect_free(client):
    _, proposal = source_and_proposal(client)
    assert client.post("/proposals/lint", json=proposal).json()["ok"] is True
    composed = client.post("/proposals/compose", json=proposal)
    assert composed.status_code == 200
    assert composed.json()["proposal_md"].startswith("# Agent Refinement Proposal")
    assert client.get("/proposals").json() == {"proposals": []}


def test_register_list_filter_and_get(client):
    source_sha, proposal = source_and_proposal(client)
    first = client.post("/proposals/register", json=proposal)
    assert first.status_code == 200
    repeat = client.post("/proposals/register", json=proposal)
    assert repeat.json()["registered"] is False
    proposal_sha = first.json()["proposal_sha"]

    listing = client.get("/proposals", params={"source_intent_sha": source_sha})
    assert listing.status_code == 200
    assert listing.json()["proposals"][0]["proposal_sha"] == proposal_sha
    detail = client.get(f"/proposals/{proposal_sha}")
    assert detail.status_code == 200
    assert detail.json()["manifest"] == proposal


def test_register_missing_source_and_get_errors(client):
    proposal = json.loads(PROPOSAL_EXAMPLE.read_text(encoding="utf-8"))
    proposal["source_intent_sha"] = "0" * 64
    response = client.post("/proposals/register", json=proposal)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "proposal_source_error"

    invalid = client.get("/proposals/not-a-sha")
    assert invalid.status_code == 400
    assert invalid.json()["detail"]["code"] == "invalid_proposal"
    unknown = client.get("/proposals/" + "0" * 64)
    assert unknown.status_code == 404
    assert unknown.json()["detail"]["code"] == "unknown_proposal"

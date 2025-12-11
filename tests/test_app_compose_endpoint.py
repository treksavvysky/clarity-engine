import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from tools import compose_packet


EXAMPLE_MANIFEST_PATH = Path("packets/examples/context_packet_example.json")


def load_example_manifest() -> dict:
    with EXAMPLE_MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def expected_outputs(manifest: dict) -> tuple[str, dict, str]:
    normalized = compose_packet.normalize_manifest(manifest)
    packet_md = compose_packet.render_packet_md(manifest) + "\n"
    context_sha = compose_packet.compute_context_sha(normalized)
    return packet_md, json.loads(normalized), context_sha


def test_compose_endpoint_matches_stage_zero_logic():
    manifest = load_example_manifest()
    packet_md_expected, manifest_expected, context_sha_expected = expected_outputs(manifest)

    client = TestClient(app)
    response = client.post("/packets/compose", json=manifest)
    assert response.status_code == 200

    payload = response.json()
    assert payload == {
        "packet_md": packet_md_expected,
        "manifest": manifest_expected,
        "context_sha": context_sha_expected,
    }

    repeat_response = client.post("/packets/compose", json=manifest)
    assert repeat_response.status_code == 200
    assert repeat_response.json() == payload

import json
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


EXAMPLE_MANIFEST_PATH = Path("packets/examples/context_packet_example.json")


def load_example_manifest() -> dict:
    with EXAMPLE_MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_lint_endpoint_accepts_valid_manifest():
    manifest = load_example_manifest()

    client = TestClient(app)
    response = client.post("/packets/lint", json=manifest)

    assert response.status_code == 200
    assert response.json() == {"ok": True, "issues": []}


def test_lint_endpoint_reports_required_field_issue():
    manifest = load_example_manifest()
    invalid_manifest = deepcopy(manifest)
    invalid_manifest.pop("acceptance")

    client = TestClient(app)
    response = client.post("/packets/lint", json=invalid_manifest)

    assert response.status_code == 200
    assert response.json() == {
        "ok": False,
        "issues": ["Missing required field: acceptance / definition_of_done (acceptance)."],
    }

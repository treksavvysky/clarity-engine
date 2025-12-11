from copy import deepcopy


def test_lint_endpoint_accepts_valid_manifest(client, example_manifest):
    manifest = example_manifest

    response = client.post("/packets/lint", json=manifest)

    assert response.status_code == 200
    assert response.json() == {"ok": True, "issues": []}


def test_lint_endpoint_reports_required_field_issue(client, example_manifest):
    manifest = example_manifest
    invalid_manifest = deepcopy(manifest)
    invalid_manifest.pop("acceptance")

    response = client.post("/packets/lint", json=invalid_manifest)

    assert response.status_code == 200
    assert response.json() == {
        "ok": False,
        "issues": ["Missing required field: acceptance / definition_of_done (acceptance)."],
    }

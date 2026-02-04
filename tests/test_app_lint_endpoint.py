from copy import deepcopy


def test_lint_endpoint_accepts_valid_manifest(client, example_manifest):
    manifest = example_manifest

    response = client.post("/packets/lint", json=manifest)

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["errors"] == []
    # Warnings may be present (ambiguity detection) but don't affect ok status


def test_lint_endpoint_reports_required_field_issue(client, example_manifest):
    manifest = example_manifest
    invalid_manifest = deepcopy(manifest)
    invalid_manifest.pop("acceptance")

    response = client.post("/packets/lint", json=invalid_manifest)

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Missing required field: acceptance / definition_of_done (acceptance)." in data["errors"]


def test_lint_endpoint_returns_warnings_for_vague_language(client, example_manifest):
    manifest = deepcopy(example_manifest)
    manifest["acceptance"] = ["Maybe this should work"]

    response = client.post("/packets/lint", json=manifest)

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True  # Warnings don't fail validation
    assert any("Vague language" in w for w in data["warnings"])


def test_lint_endpoint_returns_warnings_for_untestable_acceptance(client, example_manifest):
    manifest = deepcopy(example_manifest)
    manifest["acceptance"] = ["Good code quality"]  # No action verb

    response = client.post("/packets/lint", json=manifest)

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True  # Warnings don't fail validation
    assert any("may not be testable" in w for w in data["warnings"])

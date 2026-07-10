"""Tests for Stage-06 UI static serving."""


def test_root_serves_ui_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Clarity Engine" in response.text
    assert 'id="packet-list"' in response.text
    assert 'data-tab="intent"' in response.text
    assert 'id="intent-raw"' in response.text
    assert 'id="intent-constraints"' in response.text
    assert 'id="intent-context"' in response.text
    assert 'id="intent-route-select"' in response.text
    assert 'id="intent-mode-select"' in response.text
    assert "1. Diagnosis" in response.text
    assert "2. Clarified Mission" in response.text
    assert "3. Smallest Next Action" in response.text
    assert "4. Optional Packet Manifest" in response.text
    assert "/intents/draft" in response.text


def test_ui_static_assets_mounted(client):
    response = client.get("/ui/index.html")
    assert response.status_code == 200
    assert "Clarity Engine" in response.text

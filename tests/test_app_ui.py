"""Tests for Stage-06 UI static serving."""


def test_root_serves_ui_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Clarity Engine" in response.text
    assert 'id="packet-list"' in response.text
    assert 'data-tab="raw-intents"' in response.text
    assert 'id="intent-list"' in response.text
    assert 'id="raw-intent-detail"' in response.text
    assert "/intents/' + intentSha" in response.text
    assert "'/ancestors'" in response.text
    assert "'/missions'" in response.text
    assert 'data-tab="intent"' in response.text
    assert 'id="intent-raw"' in response.text
    assert "/intents/draft" in response.text
    assert "@media (max-width: 820px)" in response.text


def test_ui_static_assets_mounted(client):
    response = client.get("/ui/index.html")
    assert response.status_code == 200
    assert "Clarity Engine" in response.text

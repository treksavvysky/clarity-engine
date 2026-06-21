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
    assert 'id="intent-workflow-panel"' in response.text
    assert 'id="grounding-kind"' in response.text
    assert 'id="grounding-statement"' in response.text
    assert 'id="grounding-sources"' in response.text
    assert 'id="grounding-gaps"' in response.text
    assert 'id="grounding-submit"' in response.text
    assert 'id="clarification-id"' in response.text
    assert 'id="clarification-question"' in response.text
    assert 'id="clarification-ask"' in response.text
    assert 'id="clarification-answer-id"' in response.text
    assert 'id="clarification-answer"' in response.text
    assert 'id="clarification-answer-submit"' in response.text
    assert 'id="readiness-checklist"' in response.text
    assert 'id="intent-ready-submit"' in response.text
    assert 'id="intent-workflow-status"' in response.text
    assert "/grounding`" in response.text
    assert "/clarifications`" in response.text
    assert "status: 'ready_for_mission'" in response.text
    assert "unresolved_gaps: []" in response.text
    assert "captureWorkflowDraft()" in response.text
    assert "clearWorkflowDraft(clearedGroup)" in response.text
    assert "It does not approve, promote, register, or execute" in response.text
    assert 'id="intent-promotion-panel"' in response.text
    assert 'id="promotion-candidate"' in response.text
    assert 'id="promotion-load-candidate"' in response.text
    assert 'id="promotion-lint"' in response.text
    assert 'id="promotion-lint-result"' in response.text
    assert 'class="promotion-mapping"' in response.text
    assert 'id="promotion-approved-by"' in response.text
    assert 'id="promotion-approval-reference"' in response.text
    assert 'id="promotion-approved"' in response.text
    assert 'id="promotion-submit"' in response.text
    assert 'id="promotion-open-packet"' in response.text
    assert "'/packets/lint'" in response.text
    assert "/promote`" in response.text
    assert "grounding_references: groundingReferences" in response.text
    assert "openMissionPacket" in response.text
    assert "does not enqueue or execute work" in response.text
    assert 'data-tab="intent"' in response.text
    assert 'id="intent-raw"' in response.text
    assert "/intents/draft" in response.text
    assert "@media (max-width: 820px)" in response.text


def test_ui_static_assets_mounted(client):
    response = client.get("/ui/index.html")
    assert response.status_code == 200
    assert "Clarity Engine" in response.text

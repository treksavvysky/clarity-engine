"""Tests for Stage-05 MCP server tools.

Invokes tools via FastMCP.call_tool to exercise the real registration path,
then verifies output matches the HTTP endpoints for parity.
"""

import asyncio
import copy
import json

import pytest

from app import mcp_server


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARITY_REGISTRY_ROOT", str(tmp_path / "registry"))
    yield


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _call(name: str, args: dict) -> dict:
    """Invoke an MCP tool and return the parsed structured result."""
    result = _run(mcp_server.mcp.call_tool(name, args))
    if isinstance(result, list) and result and hasattr(result[0], "text"):
        return json.loads(result[0].text)
    if isinstance(result, tuple):
        for item in result:
            if isinstance(item, dict):
                return item
    if isinstance(result, dict):
        return result
    raise AssertionError(f"Unexpected result type: {type(result)!r}: {result!r}")


def test_compose_tool_matches_http(client, example_manifest):
    http_body = client.post("/packets/compose", json=example_manifest).json()
    mcp_body = _call("compose_packet_tool", {"manifest": example_manifest})
    assert mcp_body == http_body


def test_lint_tool_returns_ok_for_valid(example_manifest):
    body = _call("lint_packet_tool", {"manifest": example_manifest})
    assert body["ok"] is True
    assert body["errors"] == []


def test_lint_tool_reports_missing_required_fields():
    body = _call("lint_packet_tool", {"manifest": {"mission": "only mission"}})
    assert body["ok"] is False
    assert len(body["errors"]) > 0


def test_register_tool_is_idempotent_and_matches_http(client, example_manifest):
    first = _call("register_packet_tool", {"manifest": example_manifest})
    second = _call("register_packet_tool", {"manifest": example_manifest})
    http_sha = client.post("/packets/register", json=example_manifest).json()["context_sha"]

    assert first["context_sha"] == http_sha
    assert first["registered"] is True
    assert second["registered"] is False


def test_get_and_list_tools(client, example_manifest):
    sha = _call("register_packet_tool", {"manifest": example_manifest})["context_sha"]

    fetched = _call("get_packet_tool", {"context_sha": sha})
    assert fetched["manifest"]["mission"] == example_manifest["mission"]

    listing = _call("list_packets_tool", {})
    assert listing == {"packets": [{"context_sha": sha, "mission": example_manifest["mission"]}]}


def test_diff_tool_matches_http(client, example_manifest):
    right = copy.deepcopy(example_manifest)
    right["mission"] = "Something else."
    http_body = client.post(
        "/packets/diff",
        json={"left": example_manifest, "right": right},
    ).json()
    mcp_body = _call("diff_packets_tool", {"left": example_manifest, "right": right})
    assert mcp_body == http_body


def test_enqueue_tool_matches_http(client, example_manifest):
    http_body = client.post("/packets/enqueue", json=example_manifest).json()
    # Clear the registry effect from the HTTP call — it ran in the same isolated dir.
    # The second call should be idempotent but registered=False; to get a clean compare
    # we call the MCP tool and let it register again. Adjust expectation for registered.
    mcp_body = _call("enqueue_packet_tool", {"manifest": example_manifest})
    # The MCP call sees the packet already registered from the HTTP call.
    expected = dict(http_body)
    expected["registered"] = False
    assert mcp_body == expected


def test_check_action_permitted(example_manifest):
    manifest = copy.deepcopy(example_manifest)
    manifest["allowed_actions"] = ["git_read", "filesystem_read"]
    sha = _call("register_packet_tool", {"manifest": manifest})["context_sha"]

    assert _call("check_action_tool", {"context_sha": sha, "action": "git_read"}) == {
        "allowed": True,
        "reason": "permitted",
    }


def test_check_action_not_permitted(example_manifest):
    manifest = copy.deepcopy(example_manifest)
    manifest["allowed_actions"] = ["git_read"]
    sha = _call("register_packet_tool", {"manifest": manifest})["context_sha"]

    assert _call("check_action_tool", {"context_sha": sha, "action": "git_write"}) == {
        "allowed": False,
        "reason": "not_in_allowed_actions",
    }


def test_check_action_unknown_packet():
    assert _call(
        "check_action_tool", {"context_sha": "0" * 64, "action": "git_read"}
    ) == {"allowed": False, "reason": "unknown_packet"}


def test_server_lists_expected_tools():
    tools = _run(mcp_server.mcp.list_tools())
    names = {t.name for t in tools}
    assert {
        "compose_packet_tool",
        "lint_packet_tool",
        "register_packet_tool",
        "get_packet_tool",
        "list_packets_tool",
        "diff_packets_tool",
        "enqueue_packet_tool",
        "check_action_tool",
    }.issubset(names)

import json
from copy import deepcopy
from pathlib import Path

import pytest

from app import intent_registry
from tools import raw_intent_packet

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "packets" / "examples" / "raw_intent_packet_example.json"


@pytest.fixture(autouse=True)
def isolated_intent_registry(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLARITY_INTENT_REGISTRY_ROOT", str(tmp_path / "intent-registry")
    )


@pytest.fixture
def root_manifest():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def child_of(parent_sha, root_manifest, status):
    child = deepcopy(root_manifest)
    child["status"] = status
    child["parent_intent_sha"] = parent_sha
    return child


def test_register_read_list_and_idempotency(root_manifest):
    first = intent_registry.register(root_manifest)
    assert first["registered"] is True
    assert intent_registry.register(root_manifest) == {
        "intent_sha": first["intent_sha"],
        "registered": False,
    }

    record = intent_registry.read(first["intent_sha"])
    assert record["manifest"] == root_manifest
    assert record["intent_md"].startswith("# Raw Intent Packet")
    assert intent_registry.list_shas() == [first["intent_sha"]]
    assert intent_registry.list_summaries()[0]["status"] == "captured"


def test_invalid_manifest_does_not_create_registry(root_manifest):
    del root_manifest["provenance"]
    with pytest.raises(intent_registry.InvalidIntentError):
        intent_registry.register(root_manifest)
    assert not intent_registry.root_path().exists()


def test_root_must_begin_captured(root_manifest):
    root_manifest["status"] = "grounding"
    with pytest.raises(intent_registry.BrokenLineageError, match="must begin"):
        intent_registry.register(root_manifest)


def test_read_detects_missing_file_hash_mismatch_and_markdown_mismatch(root_manifest):
    result = raw_intent_packet.compose_manifest(root_manifest)
    record_dir = intent_registry.root_path() / result["intent_sha"]
    record_dir.mkdir(parents=True)
    (record_dir / "manifest.json").write_text(
        result["normalized_json"], encoding="utf-8"
    )
    with pytest.raises(intent_registry.CorruptIntentError, match="missing"):
        intent_registry.read(result["intent_sha"])

    (record_dir / "intent.md").write_text(result["intent_md"], encoding="utf-8")
    wrong_dir = intent_registry.root_path() / ("f" * 64)
    record_dir.rename(wrong_dir)
    with pytest.raises(intent_registry.CorruptIntentError, match="identity"):
        intent_registry.read("f" * 64)

    wrong_dir.rename(record_dir)
    (record_dir / "intent.md").write_text("changed", encoding="utf-8")
    with pytest.raises(intent_registry.CorruptIntentError, match="Markdown"):
        intent_registry.read(result["intent_sha"])


def test_listing_ignores_temp_non_sha_and_corrupt_records(root_manifest):
    valid = intent_registry.register(root_manifest)["intent_sha"]
    root = intent_registry.root_path()
    (root / ".intent-leftover").mkdir()
    (root / "not-a-sha").mkdir()
    (root / ("f" * 64)).mkdir()

    assert intent_registry.list_shas() == [valid]


def test_register_cleans_temporary_directory(root_manifest):
    intent_registry.register(root_manifest)
    assert not any(
        path.name.startswith(intent_registry.TEMP_PREFIX)
        for path in intent_registry.root_path().iterdir()
    )


@pytest.mark.parametrize(
    ("parent_status", "child_status"),
    [
        ("captured", "grounding"),
        ("captured", "abandoned"),
        ("grounding", "clarification_needed"),
        ("grounding", "ready_for_mission"),
        ("grounding", "abandoned"),
        ("clarification_needed", "grounding"),
        ("clarification_needed", "abandoned"),
        ("ready_for_mission", "grounding"),
        ("ready_for_mission", "promoted"),
        ("ready_for_mission", "abandoned"),
    ],
)
def test_all_legal_transitions(root_manifest, parent_status, child_status):
    root_sha = intent_registry.register(root_manifest)["intent_sha"]
    if parent_status == "captured":
        parent_sha = root_sha
    else:
        grounding = child_of(root_sha, root_manifest, "grounding")
        grounding_sha = intent_registry.register(grounding)["intent_sha"]
        if parent_status == "grounding":
            parent_sha = grounding_sha
        elif parent_status == "clarification_needed":
            clarification = child_of(
                grounding_sha, root_manifest, "clarification_needed"
            )
            parent_sha = intent_registry.register(clarification)["intent_sha"]
        else:
            ready = child_of(grounding_sha, root_manifest, "ready_for_mission")
            parent_sha = intent_registry.register(ready)["intent_sha"]

    child = child_of(parent_sha, root_manifest, child_status)
    assert intent_registry.register(child)["registered"] is True


def test_revision_requires_parent_exact_intent_and_legal_transition(root_manifest):
    root_sha = intent_registry.register(root_manifest)["intent_sha"]

    unknown_parent = child_of("f" * 64, root_manifest, "grounding")
    with pytest.raises(intent_registry.BrokenLineageError, match="not found"):
        intent_registry.register(unknown_parent)

    changed = child_of(root_sha, root_manifest, "grounding")
    changed["raw_intent"] += " changed"
    with pytest.raises(intent_registry.BrokenLineageError, match="preserve"):
        intent_registry.register(changed)

    illegal = child_of(root_sha, root_manifest, "ready_for_mission")
    with pytest.raises(intent_registry.BrokenLineageError, match="Illegal"):
        intent_registry.register(illegal)


def test_terminal_parent_rejects_child(root_manifest):
    root_sha = intent_registry.register(root_manifest)["intent_sha"]
    abandoned = child_of(root_sha, root_manifest, "abandoned")
    abandoned_sha = intent_registry.register(abandoned)["intent_sha"]
    child = child_of(abandoned_sha, root_manifest, "grounding")

    with pytest.raises(intent_registry.BrokenLineageError, match="terminal"):
        intent_registry.register(child)


def test_ancestors_are_nearest_parent_first(root_manifest):
    root_sha = intent_registry.register(root_manifest)["intent_sha"]
    grounding = child_of(root_sha, root_manifest, "grounding")
    grounding_sha = intent_registry.register(grounding)["intent_sha"]
    ready = child_of(grounding_sha, root_manifest, "ready_for_mission")
    ready_sha = intent_registry.register(ready)["intent_sha"]

    assert intent_registry.ancestors(ready_sha) == [
        {
            "intent_sha": grounding_sha,
            "status": "grounding",
            "parent_intent_sha": root_sha,
        },
        {
            "intent_sha": root_sha,
            "status": "captured",
            "parent_intent_sha": None,
        },
    ]


def test_ancestors_detect_broken_parent(root_manifest):
    result = raw_intent_packet.compose_manifest(
        child_of("f" * 64, root_manifest, "grounding")
    )
    record_dir = intent_registry.root_path() / result["intent_sha"]
    record_dir.mkdir(parents=True)
    (record_dir / "manifest.json").write_text(
        result["normalized_json"], encoding="utf-8"
    )
    (record_dir / "intent.md").write_text(result["intent_md"], encoding="utf-8")

    with pytest.raises(intent_registry.BrokenLineageError, match="cannot resolve"):
        intent_registry.ancestors(result["intent_sha"])


def test_ancestors_detect_cycle(monkeypatch):
    first_sha = "a" * 64
    second_sha = "b" * 64
    records = {
        first_sha: {
            "intent_sha": first_sha,
            "manifest": {
                "raw_intent": "same",
                "status": "grounding",
                "parent_intent_sha": second_sha,
            },
        },
        second_sha: {
            "intent_sha": second_sha,
            "manifest": {
                "raw_intent": "same",
                "status": "clarification_needed",
                "parent_intent_sha": first_sha,
            },
        },
    }
    monkeypatch.setattr(intent_registry, "read", lambda intent_sha: records[intent_sha])

    with pytest.raises(intent_registry.BrokenLineageError, match="cycle"):
        intent_registry.ancestors(first_sha)


def test_listing_excludes_semantically_broken_root(root_manifest):
    root_manifest["status"] = "grounding"
    result = raw_intent_packet.compose_manifest(root_manifest)
    record_dir = intent_registry.root_path() / result["intent_sha"]
    record_dir.mkdir(parents=True)
    (record_dir / "manifest.json").write_text(
        result["normalized_json"], encoding="utf-8"
    )
    (record_dir / "intent.md").write_text(result["intent_md"], encoding="utf-8")

    assert intent_registry.list_shas() == []

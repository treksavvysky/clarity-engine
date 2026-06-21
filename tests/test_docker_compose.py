from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_compose_mounts_all_runtime_registries_with_shared_user_mapping():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert 'user: "${CLARITY_UID:-1000}:${CLARITY_GID:-1000}"' in compose
    assert "./packets/registry:/app/packets/registry" in compose
    assert "./packets/intents:/app/packets/intents" in compose
    assert "./packets/links:/app/packets/links" in compose
    assert "CLARITY_REGISTRY_ROOT: /app/packets/registry" in compose
    assert "CLARITY_INTENT_REGISTRY_ROOT: /app/packets/intents" in compose
    assert "CLARITY_INTENT_LINK_ROOT: /app/packets/links/intent-missions" in compose


def test_runtime_intent_records_are_ignored_but_placeholder_is_tracked():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "packets/intents/*" in gitignore
    assert "!packets/intents/.gitkeep" in gitignore
    assert (ROOT / "packets" / "intents" / ".gitkeep").exists()
    assert "packets/links/*" in gitignore
    assert "!packets/links/.gitkeep" in gitignore
    assert (ROOT / "packets" / "links" / ".gitkeep").exists()

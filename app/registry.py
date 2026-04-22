"""Filesystem-backed content-addressed packet registry.

Layout:
    <root>/<sha>/manifest.json    — normalized manifest (stable JSON)
    <root>/<sha>/packet.md        — rendered packet markdown

The registry is append-only at the API surface and idempotent: writing a sha
that already exists is a no-op.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "packets" / "registry"


def _root() -> Path:
    override = os.environ.get("CLARITY_REGISTRY_ROOT")
    return Path(override) if override else DEFAULT_ROOT


def _packet_dir(sha: str) -> Path:
    return _root() / sha


def exists(sha: str) -> bool:
    return _packet_dir(sha).is_dir()


def write(sha: str, normalized_manifest_json: str, packet_md: str) -> bool:
    """Write a packet. Returns True if newly written, False if already present."""
    pdir = _packet_dir(sha)
    if pdir.is_dir():
        return False
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "manifest.json").write_text(normalized_manifest_json, encoding="utf-8")
    (pdir / "packet.md").write_text(packet_md, encoding="utf-8")
    return True


def read(sha: str) -> dict | None:
    """Return {manifest, packet_md} or None if sha unknown."""
    pdir = _packet_dir(sha)
    if not pdir.is_dir():
        return None
    manifest = json.loads((pdir / "manifest.json").read_text(encoding="utf-8"))
    packet_md = (pdir / "packet.md").read_text(encoding="utf-8")
    return {"manifest": manifest, "packet_md": packet_md}


def list_shas() -> list[str]:
    root = _root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())

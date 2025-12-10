#!/usr/bin/env python3
"""Deterministically compose Context Packet artifacts from a manifest."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_manifest(path: str | None) -> dict:
    """Load a JSON manifest from a file path or stdin."""
    try:
        if path:
            with open(path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
        else:
            manifest = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Invalid JSON input: {exc}\n")
        sys.exit(1)

    if not isinstance(manifest, dict):
        sys.stderr.write("Manifest must be a JSON object.\n")
        sys.exit(1)

    return manifest


def normalize_manifest(manifest: dict) -> str:
    """Return a normalized JSON string with sorted keys."""
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute_context_sha(normalized_manifest: str) -> str:
    """Compute the SHA-256 digest of the normalized manifest."""
    digest = hashlib.sha256(normalized_manifest.encode("utf-8"))
    return digest.hexdigest()


def render_header_lines(manifest: dict) -> list[str]:
    return [
        "# Context Packet Template (PCP-lite)",
        "",
        f"- **Project:** {manifest.get('project', '')}",
        f"- **Stage:** {manifest.get('stage', '')}",
        f"- **Substage:** {manifest.get('substage', '')}",
        f"- **Version:** {manifest.get('version', '')}",
        "",
    ]


def render_list_section(title: str, items: list | None) -> list[str]:
    lines = [f"## {title}"]
    if items:
        for entry in items:
            lines.append(f"- {entry}")
    lines.append("")
    return lines


def render_packet_md(manifest: dict) -> str:
    lines: list[str] = []
    lines.extend(render_header_lines(manifest))

    lines.append("## Mission")
    lines.append(f"- {manifest.get('mission', '')}")
    lines.append("")

    sections = [
        ("Current Reality (Facts Only)", manifest.get("current_reality")),
        ("Constraints", manifest.get("constraints")),
        ("Acceptance / Definition of Done", manifest.get("acceptance")),
        ("Required Artifacts", manifest.get("required_artifacts")),
        ("Failure Modes", manifest.get("failure_modes")),
        ("Substage Gate / Work Envelope", manifest.get("substage_gate")),
        ("Notes or Scope Warnings (Optional)", manifest.get("notes")),
        ("Sources of Truth (Optional)", manifest.get("sources_of_truth")),
    ]

    for title, items in sections:
        lines.extend(render_list_section(title, items if isinstance(items, list) else None))

    lines.extend(
        [
            "---",
            "",
            "**Usage Notes**",
            "- Keep each bullet factual, testable, and concise.",
            "- Maintain section order; do not omit required sections even if a list is brief.",
            "- Align field names and content with `pcp_lite.schema.json`.",
            "- Update `Version` when the schema or template meaning changes.",
            "- If a field is intentionally empty, state why rather than omitting it.",
            "",
        ]
    )

    return "\n".join(lines)


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def compose(manifest_path: str | None) -> None:
    manifest = load_manifest(manifest_path)
    normalized = normalize_manifest(manifest)
    context_sha = compute_context_sha(normalized)
    packet_md = render_packet_md(manifest)

    write_file(Path("manifest.json"), normalized)
    write_file(Path("packet.md"), packet_md + "\n")
    write_file(Path("context_sha"), context_sha + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose a Context Packet from a PCP-lite manifest."
    )
    parser.add_argument(
        "manifest_path",
        nargs="?",
        help="Path to the manifest JSON file. If omitted, reads from stdin.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    compose(args.manifest_path)


if __name__ == "__main__":
    main()

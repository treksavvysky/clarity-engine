"""Content-addressed registry for immutable Agent Refinement Proposals."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app import intent_registry
from tools import agent_refinement_proposal

DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "packets" / "proposals"
SHA_PATTERN = re.compile(r"^[a-f0-9]{64}$")
TEMP_PREFIX = ".proposal-"


class ProposalRegistryError(Exception):
    code = "proposal_registry_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidProposalError(ProposalRegistryError):
    code = "invalid_proposal"


class UnknownProposalError(ProposalRegistryError):
    code = "unknown_proposal"


class CorruptProposalError(ProposalRegistryError):
    code = "corrupt_proposal_record"


class ProposalSourceError(ProposalRegistryError):
    code = "proposal_source_error"


def root_path() -> Path:
    override = os.environ.get("CLARITY_PROPOSAL_REGISTRY_ROOT")
    return Path(override) if override else DEFAULT_ROOT


def _validate_sha(value: str, field: str) -> None:
    if not isinstance(value, str) or SHA_PATTERN.fullmatch(value) is None:
        raise InvalidProposalError(
            f"{field} must be a lowercase 64-character SHA-256 value."
        )


def _record_dir(source_intent_sha: str, proposal_sha: str) -> Path:
    return root_path() / source_intent_sha / proposal_sha


def _verify_source(source_intent_sha: str) -> None:
    try:
        intent_registry.read(source_intent_sha)
    except intent_registry.IntentRegistryError as exc:
        raise ProposalSourceError(
            f"Source Raw Intent {source_intent_sha} is unavailable: "
            f"{exc.code}: {exc.message}"
        ) from exc


def _find_record_dir(proposal_sha: str) -> Path:
    _validate_sha(proposal_sha, "proposal_sha")
    root = root_path()
    if root.is_dir():
        matches = [
            source_dir / proposal_sha
            for source_dir in root.iterdir()
            if source_dir.is_dir()
            and SHA_PATTERN.fullmatch(source_dir.name)
            and (source_dir / proposal_sha).is_dir()
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CorruptProposalError(
                f"Proposal {proposal_sha} exists under multiple source intents."
            )
    raise UnknownProposalError(f"Agent Refinement Proposal {proposal_sha} was not found.")


def read(proposal_sha: str) -> dict[str, Any]:
    record_dir = _find_record_dir(proposal_sha)
    source_intent_sha = record_dir.parent.name
    manifest_path = record_dir / "manifest.json"
    markdown_path = record_dir / "proposal.md"
    if not manifest_path.is_file() or not markdown_path.is_file():
        raise CorruptProposalError(
            f"Agent Refinement Proposal {proposal_sha} is missing "
            "manifest.json or proposal.md."
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        proposal_md = markdown_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorruptProposalError(
            f"Agent Refinement Proposal {proposal_sha} cannot be read: {exc}."
        ) from exc
    if not isinstance(manifest, dict):
        raise CorruptProposalError(
            f"Agent Refinement Proposal {proposal_sha} manifest must be a JSON object."
        )
    try:
        result = agent_refinement_proposal.compose_manifest(manifest)
    except ValueError as exc:
        raise CorruptProposalError(
            f"Agent Refinement Proposal {proposal_sha} failed validation: {exc}"
        ) from exc
    if result["proposal_sha"] != proposal_sha:
        raise CorruptProposalError(
            f"Agent Refinement Proposal {proposal_sha} does not match its identity."
        )
    if result["manifest"]["source_intent_sha"] != source_intent_sha:
        raise CorruptProposalError(
            f"Agent Refinement Proposal {proposal_sha} does not match its source directory."
        )
    if result["proposal_md"] != proposal_md:
        raise CorruptProposalError(
            f"Agent Refinement Proposal {proposal_sha} rendered Markdown is invalid."
        )
    _verify_source(source_intent_sha)
    return {
        "proposal_sha": proposal_sha,
        "source_intent_sha": source_intent_sha,
        "manifest": result["manifest"],
        "proposal_md": proposal_md,
    }


def register(manifest: dict[str, Any]) -> dict[str, Any]:
    try:
        result = agent_refinement_proposal.compose_manifest(manifest)
    except ValueError as exc:
        raise InvalidProposalError(str(exc)) from exc
    source_intent_sha = result["manifest"]["source_intent_sha"]
    _verify_source(source_intent_sha)
    proposal_sha = result["proposal_sha"]
    target = _record_dir(source_intent_sha, proposal_sha)
    if target.exists():
        read(proposal_sha)
        return {"proposal_sha": proposal_sha, "registered": False}

    source_root = root_path() / source_intent_sha
    source_root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=source_root))
    try:
        (temp_dir / "manifest.json").write_text(
            result["normalized_json"], encoding="utf-8"
        )
        (temp_dir / "proposal.md").write_text(
            result["proposal_md"], encoding="utf-8"
        )
        try:
            temp_dir.rename(target)
        except FileExistsError:
            read(proposal_sha)
            return {"proposal_sha": proposal_sha, "registered": False}
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    read(proposal_sha)
    return {"proposal_sha": proposal_sha, "registered": True}


def summarize(record: dict[str, Any]) -> dict[str, Any]:
    manifest = record["manifest"]
    return {
        "proposal_sha": record["proposal_sha"],
        "source_intent_sha": record["source_intent_sha"],
        "summary": manifest["summary"],
        "agent": manifest["proposer"]["agent"],
        "created_at": manifest["created_at"],
        "grounding_entries_count": len(manifest["grounding_entries"]),
        "clarification_questions_count": len(manifest["clarification_questions"]),
        "unresolved_gaps_count": len(manifest["unresolved_gaps"]),
    }


def list_summaries(source_intent_sha: str | None = None) -> list[dict[str, Any]]:
    if source_intent_sha is not None:
        _validate_sha(source_intent_sha, "source_intent_sha")
    root = root_path()
    if not root.is_dir():
        return []
    summaries: list[dict[str, Any]] = []
    source_dirs = (
        [root / source_intent_sha]
        if source_intent_sha is not None
        else sorted(root.iterdir(), key=lambda item: item.name)
    )
    for source_dir in source_dirs:
        if not source_dir.is_dir() or SHA_PATTERN.fullmatch(source_dir.name) is None:
            continue
        for proposal_dir in sorted(source_dir.iterdir(), key=lambda item: item.name):
            if not proposal_dir.is_dir() or SHA_PATTERN.fullmatch(proposal_dir.name) is None:
                continue
            try:
                summaries.append(summarize(read(proposal_dir.name)))
            except ProposalRegistryError:
                continue
    return summaries

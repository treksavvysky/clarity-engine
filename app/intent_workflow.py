"""Immutable grounding and clarification revision builders."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from app import intent_registry
from tools import raw_intent_packet

CLARIFICATION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def readiness_errors(manifest: dict[str, Any]) -> list[str]:
    grounding_entries = manifest.get("grounding_entries", [])
    has_verified_fact = any(
        isinstance(entry, dict)
        and entry.get("kind") == "verified_fact"
        and bool(entry.get("sources"))
        for entry in grounding_entries
    )
    open_clarifications = [
        entry
        for entry in manifest.get("clarifications", [])
        if isinstance(entry, dict) and entry.get("status") == "open"
    ]
    unresolved_gaps = manifest.get("unresolved_gaps", [])

    errors: list[str] = []
    if not has_verified_fact:
        errors.append(
            "ready_for_mission requires at least one sourced verified_fact grounding entry."
        )
    if open_clarifications:
        errors.append("ready_for_mission requires all clarifications to be answered.")
    if unresolved_gaps:
        errors.append("ready_for_mission requires unresolved_gaps to be empty.")
    return errors


def validate_readiness(manifest: dict[str, Any]) -> None:
    if manifest.get("status") != "ready_for_mission":
        return
    errors = readiness_errors(manifest)
    if errors:
        raise intent_registry.BrokenLineageError(" ".join(errors))


def _strict_body(
    body: Any,
    allowed_fields: set[str],
    operation: str,
) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise intent_registry.InvalidIntentError(
            f"{operation} request body must be a JSON object."
        )
    unexpected = sorted(set(body) - allowed_fields)
    if unexpected:
        raise intent_registry.InvalidIntentError(
            f"{operation} request contains unsupported fields: {', '.join(unexpected)}."
        )
    return body


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise intent_registry.InvalidIntentError(f"'{field}' must be a list of strings.")
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise intent_registry.InvalidIntentError(
                f"'{field}' entry at index {index} must be a non-empty string."
            )
        items.append(item)
    return items


def _grounding_entries(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise intent_registry.InvalidIntentError(
            "'entries' must be a non-empty list of grounding entries."
        )
    entries = deepcopy(value)
    candidate = {
        "version": "1.0.0",
        "raw_intent": "validation",
        "status": "captured",
        "provenance": {"source": "api"},
        "grounding_entries": entries,
    }
    errors = raw_intent_packet.validate_manifest(candidate)
    grounding_errors = [
        error for error in errors if error.startswith("$.grounding_entries")
    ]
    if grounding_errors:
        raise intent_registry.InvalidIntentError(" ".join(grounding_errors))
    return entries


def build_grounding_revision(
    parent_sha: str,
    body: Any,
) -> dict[str, Any]:
    request = _strict_body(
        body, {"entries", "unresolved_gaps", "status"}, "Grounding"
    )
    if not request:
        raise intent_registry.InvalidIntentError(
            "Grounding request must include entries, unresolved_gaps, or status."
        )

    parent = intent_registry.read(parent_sha)
    child = deepcopy(parent["manifest"])
    child["parent_intent_sha"] = parent_sha
    child["status"] = request.get("status", "grounding")

    if "entries" in request:
        child.setdefault("grounding_entries", [])
        child["grounding_entries"].extend(_grounding_entries(request["entries"]))
    if "unresolved_gaps" in request:
        gaps = _string_list(request["unresolved_gaps"], "unresolved_gaps")
        if gaps:
            child["unresolved_gaps"] = gaps
        else:
            child.pop("unresolved_gaps", None)

    errors = raw_intent_packet.validate_manifest(child)
    if errors:
        raise intent_registry.InvalidIntentError(" ".join(errors))
    validate_readiness(child)
    return child


def build_clarification_revision(
    parent_sha: str,
    body: Any,
) -> dict[str, Any]:
    request = _strict_body(
        body, {"questions", "answers", "status"}, "Clarification"
    )
    questions = request.get("questions", [])
    answers = request.get("answers", [])
    if not questions and not answers:
        raise intent_registry.InvalidIntentError(
            "Clarification request must include questions or answers."
        )
    if not isinstance(questions, list) or not isinstance(answers, list):
        raise intent_registry.InvalidIntentError(
            "'questions' and 'answers' must be lists."
        )

    parent = intent_registry.read(parent_sha)
    child = deepcopy(parent["manifest"])
    child["parent_intent_sha"] = parent_sha
    clarifications = child.setdefault("clarifications", [])
    by_id = {
        entry["id"]: entry
        for entry in clarifications
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }

    for index, question in enumerate(questions):
        if not isinstance(question, dict) or set(question) != {"id", "question"}:
            raise intent_registry.InvalidIntentError(
                f"'questions' entry at index {index} must contain only id and question."
            )
        clarification_id = question.get("id")
        question_text = question.get("question")
        if (
            not isinstance(clarification_id, str)
            or CLARIFICATION_ID_PATTERN.fullmatch(clarification_id) is None
        ):
            raise intent_registry.InvalidIntentError(
                f"'questions' entry at index {index} has an invalid id."
            )
        if not isinstance(question_text, str) or not question_text.strip():
            raise intent_registry.InvalidIntentError(
                f"'questions' entry at index {index} has an invalid question."
            )
        if clarification_id in by_id:
            raise intent_registry.InvalidIntentError(
                f"Clarification id '{clarification_id}' already exists."
            )
        entry = {
            "id": clarification_id,
            "question": question_text,
            "status": "open",
        }
        clarifications.append(entry)
        if isinstance(clarification_id, str):
            by_id[clarification_id] = entry

    answered_ids: set[str] = set()
    for index, answer in enumerate(answers):
        if not isinstance(answer, dict) or set(answer) != {"id", "answer"}:
            raise intent_registry.InvalidIntentError(
                f"'answers' entry at index {index} must contain only id and answer."
            )
        clarification_id = answer.get("id")
        answer_text = answer.get("answer")
        if not isinstance(clarification_id, str):
            raise intent_registry.InvalidIntentError(
                f"'answers' entry at index {index} has an invalid id."
            )
        if not isinstance(answer_text, str) or not answer_text.strip():
            raise intent_registry.InvalidIntentError(
                f"'answers' entry at index {index} has an invalid answer."
            )
        if clarification_id in answered_ids:
            raise intent_registry.InvalidIntentError(
                f"Clarification id '{clarification_id}' is answered more than once."
            )
        answered_ids.add(clarification_id)
        entry = by_id.get(clarification_id)
        if entry is None:
            raise intent_registry.InvalidIntentError(
                f"Clarification id '{clarification_id}' was not found."
            )
        if entry.get("status") == "answered":
            raise intent_registry.InvalidIntentError(
                f"Clarification id '{clarification_id}' is already answered."
            )
        entry["status"] = "answered"
        entry["answer"] = answer_text

    child["status"] = request.get(
        "status", "clarification_needed" if questions else "grounding"
    )
    errors = raw_intent_packet.validate_manifest(child)
    if errors:
        raise intent_registry.InvalidIntentError(" ".join(errors))
    validate_readiness(child)
    return child


def register_grounding_revision(parent_sha: str, body: Any) -> dict[str, Any]:
    child = build_grounding_revision(parent_sha, body)
    result = intent_registry.register(child)
    return {
        "parent_intent_sha": parent_sha,
        "intent_sha": result["intent_sha"],
        "status": child["status"],
        "registered": result["registered"],
    }


def register_clarification_revision(parent_sha: str, body: Any) -> dict[str, Any]:
    child = build_clarification_revision(parent_sha, body)
    result = intent_registry.register(child)
    return {
        "parent_intent_sha": parent_sha,
        "intent_sha": result["intent_sha"],
        "status": child["status"],
        "registered": result["registered"],
    }

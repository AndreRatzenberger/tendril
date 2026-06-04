from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


BASE_REQUIRED_FIELDS = (
    "id",
    "artifact_id",
    "topic_id",
    "action",
    "target",
    "rationale",
    "evidence",
    "risk_tier",
    "status",
)


def validate_proposal_schema(proposal: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in BASE_REQUIRED_FIELDS:
        if not proposal.get(field):
            errors.append(field)

    target = proposal.get("target")
    if not isinstance(target, Mapping):
        errors.append("target")
    else:
        _require_target(errors, target, "id")
        _require_target(errors, target, "type")
        action = proposal.get("action")
        target_type = target.get("type")
        if action == "add_node":
            if target_type != "node":
                errors.append("target.type")
            _require_target(errors, target, "title")
        elif action == "add_edge":
            if target_type != "edge":
                errors.append("target.type")
            for field in ["source_id", "target_id", "relationship"]:
                _require_target(errors, target, field)

    evidence = proposal.get("evidence")
    if evidence and (
        not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes))
    ):
        errors.append("evidence")
    elif isinstance(evidence, Sequence):
        for index, item in enumerate(evidence):
            if not isinstance(item, Mapping):
                errors.append(f"evidence[{index}]")
                continue
            if not item.get("artifact_id"):
                errors.append(f"evidence[{index}].artifact_id")
            if not item.get("quote"):
                errors.append(f"evidence[{index}].quote")

    return sorted(set(errors))


def _require_target(
    errors: list[str],
    target: Mapping[str, Any],
    field: str,
) -> None:
    if not target.get(field):
        errors.append(f"target.{field}")

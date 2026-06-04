from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tendril.proof_policy import read_proof_policy
from tendril.proposal_schema import validate_proposal_schema
from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now
from tendril.topics import topic_exists


class ProofError(Exception):
    """Raised when proof cannot run."""


def run_proof(store: Store, proposal_id: str) -> dict[str, Any]:
    try:
        proposal = store.read_record("proposals", proposal_id)
    except RecordNotFoundError as exc:
        raise ProofError(f"Unknown proposal: {proposal_id}") from exc

    graph = store.read_graph()
    policy = read_proof_policy(store)
    schema_errors = validate_proposal_schema(proposal)
    checks = [
        _check(
            "schema_valid",
            not schema_errors,
            "schema validation failed",
            detail=", ".join(schema_errors),
        ),
        _check(
            "action_allowed",
            str(proposal.get("action")) in set(policy["allowed_actions"]),
            "action is not allowed by proof policy",
        ),
        _check(
            "artifact_exists",
            store.record_exists("artifacts", str(proposal.get("artifact_id"))),
            "source artifact is missing",
        ),
        _check(
            "topic_exists",
            topic_exists(str(proposal.get("topic_id"))),
            "target topic is unknown",
        ),
        _check(
            "evidence_present",
            bool(proposal.get("evidence")),
            "missing evidence",
        ),
        _check(
            "risk_tier_present",
            str(proposal.get("risk_tier")) in set(policy["allowed_risk_tiers"]),
            "missing risk tier",
        ),
        _check(
            "source_grounded",
            _evidence_is_source_grounded(store, proposal),
            "evidence quote not found in source artifact",
        ),
        _check(
            "rationale_strong_enough",
            _rationale_is_strong_enough(proposal, policy),
            "rationale is too weak",
        ),
        _check(
            "no_unresolved_contradiction",
            not proposal.get("contradicts"),
            "proposal declares unresolved contradiction",
        ),
        _check(
            "not_duplicate",
            not _target_exists(graph, proposal),
            "target already exists",
        ),
    ]
    if proposal.get("action") == "add_edge":
        checks.append(
            _check(
                "edge_endpoints_exist",
                _edge_endpoints_exist(graph, proposal),
                "edge endpoint node is missing",
            )
        )

    risk_tier = str(proposal.get("risk_tier", ""))
    topology_change = bool(proposal.get("topology_change"))
    review_required = risk_tier in {"review", "high"} or topology_change
    checks.append(
        _check(
            "review_required_for_risk",
            True,
            "",
            detail="human review required" if review_required else "auto-apply allowed",
        )
    )
    if topology_change:
        checks.append(
            _check(
                "review_required_for_topology_change",
                review_required,
                "topology changes require human review",
                detail="human review required",
            )
        )

    warnings = [str(check["warning"]) for check in checks if not check["passed"]]
    if warnings:
        verdict = "reject"
        required_decision = "none"
    elif review_required:
        verdict = "hold"
        required_decision = "human_review"
    else:
        verdict = "accept"
        required_decision = "none"

    proof = {
        "proposal_id": proposal_id,
        "created_at": utc_now(),
        "checks_run": checks,
        "verdict": verdict,
        "warnings": warnings,
        "required_decision": required_decision,
        "policy": _policy_snapshot(policy),
        "casefile": _casefile(proposal, verdict, warnings, required_decision, policy),
    }
    store.write_record("proofs", proposal_id, proof, overwrite=True)
    return proof


def _check(
    name: str,
    passed: bool,
    warning: str,
    *,
    detail: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {"name": name, "passed": passed}
    if warning and not passed:
        result["warning"] = warning
    if detail:
        result["detail"] = detail
    return result


def _target_exists(graph: dict[str, Any], proposal: dict[str, Any]) -> bool:
    target = proposal.get("target") or {}
    target_id = target.get("id") if isinstance(target, dict) else None
    if proposal.get("action") == "add_edge" and isinstance(target, dict):
        return any(
            edge.get("id") == target_id
            or (
                edge.get("source_id") == target.get("source_id")
                and edge.get("target_id") == target.get("target_id")
                and edge.get("relationship") == target.get("relationship")
            )
            for edge in graph.get("edges", [])
        )
    return any(node.get("id") == target_id for node in graph.get("nodes", []))


def _edge_endpoints_exist(graph: dict[str, Any], proposal: dict[str, Any]) -> bool:
    target = proposal.get("target") or {}
    if not isinstance(target, dict):
        return False
    node_ids = {node.get("id") for node in graph.get("nodes", [])}
    return target.get("source_id") in node_ids and target.get("target_id") in node_ids


def _evidence_is_source_grounded(store: Store, proposal: dict[str, Any]) -> bool:
    evidence = proposal.get("evidence")
    if not evidence:
        return True
    if not isinstance(evidence, list):
        return False

    for item in evidence:
        if not isinstance(item, Mapping):
            return False
        artifact_id = str(item.get("artifact_id", ""))
        quote = str(item.get("quote", "")).strip()
        if not artifact_id or not quote:
            return False
        try:
            artifact = store.read_record("artifacts", artifact_id)
        except RecordNotFoundError:
            return False
        normalized_quote = _normalize(quote)
        normalized_content = _normalize(str(artifact.get("content", "")))
        if normalized_quote.endswith("..."):
            normalized_quote = normalized_quote[:-3].rstrip()
        if normalized_quote not in normalized_content:
            return False
    return True


def _rationale_is_strong_enough(
    proposal: dict[str, Any],
    policy: dict[str, Any],
) -> bool:
    rationale = str(proposal.get("rationale", "")).strip()
    return len(rationale) >= int(policy["min_rationale_chars"])


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _policy_snapshot(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": policy["id"],
        "version": policy["version"],
        "allowed_actions": policy["allowed_actions"],
        "allowed_risk_tiers": policy["allowed_risk_tiers"],
        "model_assisted_proof": policy["model_assisted_proof"],
    }


def _casefile(
    proposal: dict[str, Any],
    verdict: str,
    warnings: list[str],
    required_decision: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    target = proposal.get("target") if isinstance(proposal.get("target"), dict) else {}
    action = str(proposal.get("action", "unknown"))
    target_id = str(target.get("id", "unknown"))
    return {
        "proposal_id": str(proposal.get("id", "")),
        "artifact_id": str(proposal.get("artifact_id", "")),
        "topic_id": str(proposal.get("topic_id", "")),
        "action": action,
        "target_id": target_id,
        "evidence_count": len(proposal.get("evidence") or []),
        "verdict": verdict,
        "warnings": warnings,
        "required_decision": required_decision,
        "policy_id": str(policy["id"]),
        "policy_version": str(policy["version"]),
        "summary": (
            f"{verdict} {action} proposal for {target_id}; "
            f"{len(warnings)} warning(s); decision={required_decision}"
        ),
    }

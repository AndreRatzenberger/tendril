from __future__ import annotations

from typing import Any

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
    checks = [
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
            bool(proposal.get("risk_tier")),
            "missing risk tier",
        ),
        _check(
            "not_duplicate",
            not _target_exists(graph, proposal),
            "target already exists",
        ),
    ]

    risk_tier = str(proposal.get("risk_tier", ""))
    review_required = risk_tier in {"review", "high"}
    checks.append(
        _check(
            "review_required_for_risk",
            True,
            "",
            detail="human review required" if review_required else "auto-apply allowed",
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
    return any(node.get("id") == target_id for node in graph.get("nodes", []))

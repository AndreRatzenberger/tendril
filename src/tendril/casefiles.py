from __future__ import annotations

from typing import Any

from tendril.store import RecordNotFoundError, Store


def list_pending_proposals(store: Store) -> dict[str, Any]:
    items = []
    for proposal in store.list_records("proposals"):
        status = _proposal_status(store, proposal)
        if status in {"pending_proof", "pending_review", "accepted_pending_apply"}:
            items.append(_queue_item(store, proposal, status))

    items.sort(key=lambda item: (item.get("created_at", ""), item["proposal_id"]))
    return {"count": len(items), "items": items}


def build_casefile(store: Store, proposal_id: str) -> dict[str, Any]:
    proposal = store.read_record("proposals", proposal_id)
    proof = _read_optional(store, "proofs", proposal_id)
    decision = _read_optional(store, "decisions", proposal_id)
    graph = store.read_graph()
    mutation = _find_mutation(graph, proposal_id)
    meta_change = _read_optional(store, "meta_changes", proposal_id)
    artifact_id = str(proposal.get("artifact_id", ""))
    artifact = _read_optional(store, "artifacts", artifact_id)
    status = _proposal_status(store, proposal)
    target = proposal.get("target") if isinstance(proposal.get("target"), dict) else {}
    target_id = str(target.get("id", ""))

    records = {
        "proposal": _record_pointer(store, "proposals", proposal_id),
        "graph": {"path": ".tendril/graph.json", "present": True},
    }
    if artifact:
        records["artifact"] = _record_pointer(store, "artifacts", artifact_id)
    if proof:
        records["proof"] = _record_pointer(store, "proofs", proposal_id)
    if decision:
        records["decision"] = _record_pointer(store, "decisions", proposal_id)
    if meta_change:
        records["meta_change"] = _record_pointer(store, "meta_changes", proposal_id)

    return {
        "proposal_id": proposal_id,
        "artifact_id": artifact_id,
        "topic_id": proposal.get("topic_id"),
        "action": proposal.get("action"),
        "target_id": target_id,
        "status": status,
        "summary": f"{status} {proposal.get('action')} proposal for {target_id}",
        "records": records,
        "proof": _proof_summary(proof),
        "decision": _decision_summary(decision),
        "mutation": mutation,
        "meta_change": meta_change,
        "artifact": _artifact_summary(artifact),
    }


def _queue_item(
    store: Store,
    proposal: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    proposal_id = str(proposal["id"])
    target = proposal.get("target") if isinstance(proposal.get("target"), dict) else {}
    return {
        "proposal_id": proposal_id,
        "artifact_id": proposal.get("artifact_id"),
        "topic_id": proposal.get("topic_id"),
        "action": proposal.get("action"),
        "target_id": target.get("id"),
        "status": status,
        "created_at": proposal.get("created_at"),
        "summary": f"{status} {proposal.get('action')} proposal for {target.get('id')}",
        "record_path": _record_pointer(store, "proposals", proposal_id)["path"],
    }


def _proposal_status(store: Store, proposal: dict[str, Any]) -> str:
    proposal_id = str(proposal["id"])
    if proposal.get("status") == "applied":
        return "applied"

    proof = _read_optional(store, "proofs", proposal_id)
    if not proof:
        return "pending_proof"
    if proof.get("verdict") == "reject":
        return "proof_rejected"

    decision = _read_optional(store, "decisions", proposal_id)
    if decision:
        if decision.get("decision") == "reject":
            return "rejected"
        if decision.get("decision") == "accept":
            return "accepted_pending_apply"

    if proof.get("required_decision") == "human_review":
        return "pending_review"
    return "accepted_pending_apply"


def _read_optional(
    store: Store,
    collection: str,
    record_id: str,
) -> dict[str, Any] | None:
    try:
        return store.read_record(collection, record_id)
    except RecordNotFoundError:
        return None


def _record_pointer(
    store: Store,
    collection: str,
    record_id: str,
) -> dict[str, Any]:
    path = store.record_path(collection, record_id)
    return {
        "path": f".tendril/{collection}/{record_id}.json",
        "present": path.exists(),
    }


def _find_mutation(
    graph: dict[str, Any],
    proposal_id: str,
) -> dict[str, Any] | None:
    for mutation in graph.get("mutations", []):
        if mutation.get("proposal_id") == proposal_id:
            return mutation
    return None


def _proof_summary(proof: dict[str, Any] | None) -> dict[str, Any] | None:
    if not proof:
        return None
    return {
        "verdict": proof.get("verdict"),
        "warnings": proof.get("warnings", []),
        "required_decision": proof.get("required_decision"),
        "casefile": proof.get("casefile"),
    }


def _decision_summary(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not decision:
        return None
    return {
        "decision": decision.get("decision"),
        "reviewer": decision.get("reviewer"),
        "reason": decision.get("reason"),
        "decided_at": decision.get("decided_at"),
    }


def _artifact_summary(artifact: dict[str, Any] | None) -> dict[str, Any] | None:
    if not artifact:
        return None
    return {
        "id": artifact.get("id"),
        "source_type": artifact.get("source_type"),
        "sha256": artifact.get("sha256"),
        "extracted_topics": artifact.get("extracted_topics", []),
    }

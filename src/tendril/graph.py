from __future__ import annotations

from typing import Any

from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now


class ApplyError(Exception):
    """Raised when a proposal cannot be applied to the graph."""


def apply_proposal(store: Store, proposal_id: str) -> dict[str, Any]:
    try:
        proposal = store.read_record("proposals", proposal_id)
    except RecordNotFoundError as exc:
        raise ApplyError(f"Unknown proposal: {proposal_id}") from exc

    try:
        proof = store.read_record("proofs", proposal_id)
    except RecordNotFoundError as exc:
        raise ApplyError(f"Proposal requires proof before apply: {proposal_id}") from exc

    if proof["verdict"] == "reject":
        raise ApplyError(f"Proposal proof rejected: {proposal_id}")

    if proof["required_decision"] == "human_review":
        decision = _read_decision(store, proposal_id)
        if decision.get("decision") != "accept":
            raise ApplyError(f"Proposal is not accepted: {proposal_id}")

    graph = store.read_graph()
    if any(
        mutation.get("proposal_id") == proposal_id
        for mutation in graph.get("mutations", [])
    ):
        return {"proposal_id": proposal_id, "applied": False, "reason": "already_applied"}

    target = proposal["target"]
    if proposal["action"] != "add_node":
        raise ApplyError(f"Unsupported proposal action: {proposal['action']}")

    if not any(node.get("id") == target["id"] for node in graph["nodes"]):
        graph["nodes"].append(
            {
                "id": target["id"],
                "title": target["title"],
                "topic_id": proposal["topic_id"],
                "source_artifact_id": proposal["artifact_id"],
                "proposal_id": proposal_id,
                "created_at": utc_now(),
            }
        )

    graph["mutations"].append(
        {
            "proposal_id": proposal_id,
            "proof_id": proposal_id,
            "artifact_id": proposal["artifact_id"],
            "action": proposal["action"],
            "target_id": target["id"],
            "applied_at": utc_now(),
        }
    )
    store.write_graph(graph)

    proposal["status"] = "applied"
    store.write_record("proposals", proposal_id, proposal, overwrite=True)
    return {"proposal_id": proposal_id, "applied": True}


def _read_decision(store: Store, proposal_id: str) -> dict[str, Any]:
    try:
        return store.read_record("decisions", proposal_id)
    except RecordNotFoundError as exc:
        raise ApplyError(f"Proposal is not accepted: {proposal_id}") from exc

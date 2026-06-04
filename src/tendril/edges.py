from __future__ import annotations

import re
from typing import Any

from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now


class EdgeProposalError(Exception):
    """Raised when an edge proposal cannot be created."""


def create_edge_proposal(
    store: Store,
    artifact_id: str,
    *,
    source_id: str,
    target_id: str,
    relationship: str,
    evidence_quote: str,
    topic_id: str = "bounded-autonomy-software",
) -> dict[str, Any]:
    source_id = source_id.strip()
    target_id = target_id.strip()
    relationship = relationship.strip()
    evidence_quote = evidence_quote.strip()

    try:
        artifact = store.read_record("artifacts", artifact_id)
    except RecordNotFoundError as exc:
        raise EdgeProposalError(f"Unknown artifact: {artifact_id}") from exc

    graph = store.read_graph()
    node_ids = {str(node.get("id")) for node in graph.get("nodes", [])}
    missing_nodes = [
        node_id for node_id in [source_id, target_id] if node_id not in node_ids
    ]
    if missing_nodes:
        raise EdgeProposalError(f"Unknown edge endpoint nodes: {missing_nodes}")
    if source_id == target_id:
        raise EdgeProposalError("Edge source and target must be different nodes")
    if not relationship:
        raise EdgeProposalError("Edge relationship is required")
    if not evidence_quote:
        raise EdgeProposalError("Edge evidence is required")

    edge_id = _edge_id(source_id, relationship, target_id)
    proposal_id = f"prop_edge_{artifact_id}_{edge_id}"
    proposal = {
        "id": proposal_id,
        "artifact_id": artifact_id,
        "topic_id": topic_id,
        "created_at": utc_now(),
        "action": "add_edge",
        "target": {
            "type": "edge",
            "id": edge_id,
            "source_id": source_id,
            "target_id": target_id,
            "relationship": relationship,
            "title": f"{source_id} {relationship} {target_id}",
        },
        "rationale": (
            "The artifact provides evidence for a relationship between existing "
            "graph nodes."
        ),
        "evidence": [
            {
                "artifact_id": str(artifact["id"]),
                "quote": evidence_quote,
            }
        ],
        "risk_tier": "review",
        "status": "proposed",
        "topology_change": True,
    }
    store.write_record("proposals", proposal_id, proposal)
    return proposal


def _edge_id(source_id: str, relationship: str, target_id: str) -> str:
    raw = f"edge_{source_id}_{relationship}_{target_id}"
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-")

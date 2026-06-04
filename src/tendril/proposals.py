from __future__ import annotations

import re
from typing import Any

from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now
from tendril.topics import get_topic


class ProposalValidationError(Exception):
    """Raised when a graph-change proposal cannot be created."""


def create_proposals(store: Store, artifact_id: str) -> list[dict[str, Any]]:
    try:
        artifact = store.read_record("artifacts", artifact_id)
    except RecordNotFoundError as exc:
        raise ProposalValidationError(f"Unknown artifact: {artifact_id}") from exc

    proposals = []
    topic_ids = artifact.get("extracted_topics") or ["bounded-autonomy-software"]
    for topic_id in topic_ids:
        topic = get_topic(str(topic_id))
        proposal_id = f"prop_{artifact_id}_{_slug(topic.id)}"
        evidence = _evidence_from_artifact(artifact)
        proposal: dict[str, Any] = {
            "id": proposal_id,
            "artifact_id": artifact_id,
            "topic_id": topic.id,
            "created_at": utc_now(),
            "action": "add_node",
            "target": {
                "type": "node",
                "id": f"node_{artifact_id}_{_slug(topic.id)}",
                "title": f"{topic.title} note from {artifact_id}",
            },
            "rationale": (
                f"The artifact appears relevant to {topic.title}: "
                f"{topic.description}"
            ),
            "evidence": evidence,
            "risk_tier": "review",
            "status": "proposed",
        }
        _validate_proposal(proposal)
        store.write_record("proposals", proposal_id, proposal)
        proposals.append(proposal)

    return proposals


def _validate_proposal(proposal: dict[str, Any]) -> None:
    required = [
        "id",
        "artifact_id",
        "topic_id",
        "action",
        "target",
        "rationale",
        "evidence",
        "risk_tier",
        "status",
    ]
    missing = [field for field in required if not proposal.get(field)]
    if missing:
        raise ProposalValidationError(f"Malformed proposal missing: {missing}")


def _evidence_from_artifact(artifact: dict[str, Any]) -> list[dict[str, str]]:
    content = str(artifact.get("content", ""))
    excerpt = " ".join(content.strip().split())
    if len(excerpt) > 240:
        excerpt = excerpt[:237].rstrip() + "..."
    return [
        {
            "artifact_id": str(artifact["id"]),
            "quote": excerpt,
        }
    ]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

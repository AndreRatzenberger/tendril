from __future__ import annotations

import re
from typing import Any

from tendril.runtime import get_runtime
from tendril.runtime.base import ProposalRequest, validate_runtime_batch
from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now
from tendril.topics import get_topic


class ProposalValidationError(Exception):
    """Raised when a graph-change proposal cannot be created."""


def create_proposals(
    store: Store,
    artifact_id: str,
    *,
    runtime_name: str = "codex",
) -> list[dict[str, Any]]:
    try:
        artifact = store.read_record("artifacts", artifact_id)
    except RecordNotFoundError as exc:
        raise ProposalValidationError(f"Unknown artifact: {artifact_id}") from exc

    topic_ids = artifact.get("extracted_topics") or ["bounded-autonomy-software"]
    topics = [get_topic(str(topic_id)) for topic_id in topic_ids]
    runtime = get_runtime(runtime_name)
    batch = runtime.create_proposals(ProposalRequest(artifact=artifact, topics=topics))
    validate_runtime_batch(batch, allowed_topic_ids={topic.id for topic in topics})

    proposals = []
    for runtime_proposal in batch["proposals"]:
        topic = get_topic(str(runtime_proposal["topic_id"]))
        proposal_id = f"prop_{artifact_id}_{_slug(topic.id)}"
        proposal: dict[str, Any] = {
            "id": proposal_id,
            "artifact_id": artifact_id,
            "topic_id": topic.id,
            "created_at": utc_now(),
            "action": runtime_proposal["action"],
            "target": runtime_proposal["target"],
            "rationale": runtime_proposal["rationale"],
            "evidence": runtime_proposal["evidence"],
            "risk_tier": runtime_proposal["risk_tier"],
            "status": runtime_proposal["status"],
            "runtime": batch["runtime"],
            "runtime_ref": _runtime_ref(batch["runtime"]),
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


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _runtime_ref(runtime: dict[str, Any]) -> dict[str, str]:
    ref = {
        "runtime_name": str(runtime["name"]),
        "runtime_kind": str(runtime["kind"]),
    }
    for source, target in [
        ("thread_id", "thread_id"),
        ("turn_id", "turn_id"),
        ("casefile_id", "casefile_id"),
        ("model", "model"),
    ]:
        if runtime.get(source):
            ref[target] = str(runtime[source])
    return ref

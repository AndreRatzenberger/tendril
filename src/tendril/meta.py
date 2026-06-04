from __future__ import annotations

import re
from typing import Any

from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now


class MetaProposalError(Exception):
    """Raised when a meta proposal cannot be created."""


def create_meta_proposal(
    store: Store,
    artifact_id: str,
    *,
    change_type: str,
    target: str,
    expected_benefit: str,
    evidence_quote: str,
    blast_radius: str,
    rollback_path: str,
) -> dict[str, Any]:
    change_type = change_type.strip()
    target = target.strip()
    expected_benefit = expected_benefit.strip()
    evidence_quote = evidence_quote.strip()
    blast_radius = blast_radius.strip()
    rollback_path = rollback_path.strip()

    try:
        artifact = store.read_record("artifacts", artifact_id)
    except RecordNotFoundError as exc:
        raise MetaProposalError(f"Unknown artifact: {artifact_id}") from exc

    missing = [
        name
        for name, value in [
            ("change_type", change_type),
            ("target", target),
            ("expected_benefit", expected_benefit),
            ("evidence", evidence_quote),
            ("blast_radius", blast_radius),
            ("rollback_path", rollback_path),
        ]
        if not value
    ]
    if missing:
        raise MetaProposalError(f"Meta proposal missing required fields: {missing}")

    meta_id = _meta_id(change_type, target)
    proposal_id = f"prop_meta_{artifact_id}_{meta_id}"
    proposal = {
        "id": proposal_id,
        "artifact_id": artifact_id,
        "topic_id": "proof-and-governance",
        "created_at": utc_now(),
        "action": "meta_change",
        "target": {
            "type": "meta_change",
            "id": meta_id,
            "change_type": change_type,
            "target": target,
            "title": f"{change_type} change for {target}",
        },
        "rationale": (
            "This meta proposal requests a bounded authority-affecting change "
            "that must remain reviewable before implementation."
        ),
        "evidence": [
            {
                "artifact_id": str(artifact["id"]),
                "quote": evidence_quote,
            }
        ],
        "risk_tier": "high",
        "status": "proposed",
        "authority_change": True,
        "expected_benefit": expected_benefit,
        "blast_radius": blast_radius,
        "rollback_path": rollback_path,
    }
    store.write_record("proposals", proposal_id, proposal)
    return proposal


def _meta_id(change_type: str, target: str) -> str:
    raw = f"meta_{change_type}_{target}"
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-")

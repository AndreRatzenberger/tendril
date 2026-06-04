from __future__ import annotations

from typing import Any

from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now


class ReviewError(Exception):
    """Raised when a review decision cannot be recorded."""


def record_review(
    store: Store,
    proposal_id: str,
    decision: str,
    reason: str,
    *,
    reviewer: str = "operator",
) -> dict[str, Any]:
    if decision not in {"accept", "reject"}:
        raise ReviewError("Decision must be accept or reject")
    if not reason.strip():
        raise ReviewError("Review reason is required")
    if not store.record_exists("proposals", proposal_id):
        raise ReviewError(f"Unknown proposal: {proposal_id}")

    previous_history: list[dict[str, Any]] = []
    try:
        previous = store.read_record("decisions", proposal_id)
        previous_history = list(previous.get("history", []))
        previous_history.append(
            {
                "decision": previous["decision"],
                "reason": previous["reason"],
                "reviewer": previous["reviewer"],
                "decided_at": previous["decided_at"],
            }
        )
    except RecordNotFoundError:
        pass

    review = {
        "proposal_id": proposal_id,
        "decision": decision,
        "reviewer": reviewer,
        "decided_at": utc_now(),
        "reason": reason,
        "history": previous_history,
    }
    store.write_record("decisions", proposal_id, review, overwrite=True)
    return review

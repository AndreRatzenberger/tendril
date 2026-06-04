from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from tendril.topics import Topic


class TendrilRuntimeError(Exception):
    """Raised when a proposal runtime cannot produce a valid batch."""


@dataclass(frozen=True)
class ProposalRequest:
    artifact: Mapping[str, Any]
    topics: Sequence[Topic]


class ProposalRuntime(Protocol):
    name: str

    def create_proposals(self, request: ProposalRequest) -> dict[str, Any]:
        """Return a runtime metadata object and proposed graph changes."""


REQUIRED_RUNTIME_FIELDS = ("name", "kind")
REQUIRED_PROPOSAL_FIELDS = (
    "topic_id",
    "action",
    "target",
    "rationale",
    "evidence",
    "risk_tier",
    "status",
)


def validate_runtime_batch(
    batch: Mapping[str, Any],
    *,
    allowed_topic_ids: set[str],
) -> None:
    runtime = batch.get("runtime")
    if not isinstance(runtime, Mapping):
        raise TendrilRuntimeError("Runtime batch missing runtime metadata")

    missing_runtime = [
        field for field in REQUIRED_RUNTIME_FIELDS if not runtime.get(field)
    ]
    if missing_runtime:
        raise TendrilRuntimeError(
            f"Runtime metadata missing fields: {missing_runtime}"
        )

    proposals = batch.get("proposals")
    if not isinstance(proposals, Sequence) or isinstance(proposals, (str, bytes)):
        raise TendrilRuntimeError("Runtime batch missing proposals")
    if not proposals:
        raise TendrilRuntimeError("Runtime batch must include at least one proposal")

    for proposal in proposals:
        if not isinstance(proposal, Mapping):
            raise TendrilRuntimeError("Runtime proposal must be an object")

        missing = [
            field for field in REQUIRED_PROPOSAL_FIELDS if not proposal.get(field)
        ]
        if missing:
            raise TendrilRuntimeError(f"Runtime proposal missing fields: {missing}")

        topic_id = str(proposal["topic_id"])
        if topic_id not in allowed_topic_ids:
            raise TendrilRuntimeError(
                f"Runtime proposal used unrequested topic: {topic_id}"
            )

        target = proposal["target"]
        if not isinstance(target, Mapping) or not target.get("id"):
            raise TendrilRuntimeError("Runtime proposal target missing id")

        evidence = proposal["evidence"]
        if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes)):
            raise TendrilRuntimeError("Runtime proposal evidence must be a list")

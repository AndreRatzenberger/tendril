from __future__ import annotations

import re
from typing import Any

from tendril.runtime.base import ProposalRequest


class FakeRuntime:
    name = "fake"

    def create_proposals(self, request: ProposalRequest) -> dict[str, Any]:
        artifact = request.artifact
        proposals = []
        for topic in request.topics:
            proposals.append(
                {
                    "topic_id": topic.id,
                    "action": "add_node",
                    "target": {
                        "type": "node",
                        "id": f"node_{artifact['id']}_{_slug(topic.id)}",
                        "title": f"{topic.title} note from {artifact['id']}",
                    },
                    "rationale": (
                        f"The artifact appears relevant to {topic.title}: "
                        f"{topic.description}"
                    ),
                    "evidence": _evidence_from_artifact(artifact),
                    "risk_tier": "review",
                    "status": "proposed",
                }
            )

        return {
            "runtime": {
                "name": self.name,
                "kind": "deterministic",
                "turn_id": f"fake-turn-{artifact['id']}",
                "casefile_id": f"case_{artifact['id']}",
            },
            "proposals": proposals,
        }


def _evidence_from_artifact(artifact: Any) -> list[dict[str, str]]:
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

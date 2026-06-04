from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    description: str
    keywords: tuple[str, ...]


TOPICS: tuple[Topic, ...] = (
    Topic(
        id="codex-runtime",
        title="Codex Runtime",
        description="Codex SDK, app-server, threads, turns, and runtime state.",
        keywords=("codex", "sdk", "app-server", "thread", "turn", "sandbox"),
    ),
    Topic(
        id="proof-and-governance",
        title="Proof And Governance",
        description="Evidence, proof checks, approvals, and governed mutation.",
        keywords=(
            "proof",
            "approval",
            "governance",
            "evidence",
            "provenance",
            "verdict",
        ),
    ),
    Topic(
        id="bounded-autonomy-software",
        title="Bounded Autonomy Software",
        description="Domain objects carrying bounded, reviewable agent work.",
        keywords=("autonomy", "agent", "bounded", "proposal", "graph"),
    ),
)


def topic_exists(topic_id: str) -> bool:
    return any(topic.id == topic_id for topic in TOPICS)


def get_topic(topic_id: str) -> Topic:
    for topic in TOPICS:
        if topic.id == topic_id:
            return topic
    raise KeyError(topic_id)


def select_topics(content: str) -> list[dict[str, object]]:
    lowered = content.lower()
    matches: list[dict[str, object]] = []

    for topic in TOPICS:
        matched_terms = [term for term in topic.keywords if term in lowered]
        if matched_terms:
            matches.append(
                {
                    "topic_id": topic.id,
                    "matched_terms": matched_terms,
                    "reason": f"matched terms: {', '.join(matched_terms)}",
                }
            )

    if matches:
        return matches

    return [
        {
            "topic_id": "bounded-autonomy-software",
            "matched_terms": [],
            "reason": "default topic for M0 artifacts",
        }
    ]

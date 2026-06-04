from __future__ import annotations

from typing import Any

from tendril.runtime import RUNTIME_CHOICES
from tendril.store import RecordNotFoundError, Store
from tendril.time import utc_now
from tendril.topics import TOPICS, Topic


class TopicStateError(Exception):
    """Raised when persisted topic state cannot be updated."""


def list_topic_records(store: Store) -> list[dict[str, Any]]:
    ensure_topic_records(store)
    return [read_topic_record(store, topic.id) for topic in TOPICS]


def read_topic_record(store: Store, topic_id: str) -> dict[str, Any]:
    ensure_topic_records(store)
    try:
        return store.read_record("topics", topic_id)
    except RecordNotFoundError as exc:
        raise TopicStateError(f"Unknown topic: {topic_id}") from exc


def bind_topic_runtime(
    store: Store,
    topic_id: str,
    *,
    runtime_name: str,
    thread_id: str,
    model: str | None = None,
) -> dict[str, Any]:
    if runtime_name not in RUNTIME_CHOICES:
        raise TopicStateError(f"Unknown runtime: {runtime_name}")
    if not thread_id.strip():
        raise TopicStateError("Runtime thread ID is required")

    record = read_topic_record(store, topic_id)
    now = utc_now()
    record["runtime"] = {
        "name": runtime_name,
        "kind": _runtime_kind(runtime_name),
        "thread_id": thread_id,
        "model": model,
        "bound_at": record.get("runtime", {}).get("bound_at") or now,
        "updated_at": now,
    }
    record["updated_at"] = now
    store.write_record("topics", topic_id, record, overwrite=True)
    return record


def clear_topic_runtime(store: Store, topic_id: str) -> dict[str, Any]:
    record = read_topic_record(store, topic_id)
    record["runtime"] = _empty_runtime()
    record["updated_at"] = utc_now()
    store.write_record("topics", topic_id, record, overwrite=True)
    return record


def ensure_topic_records(store: Store) -> None:
    store.initialize()
    for topic in TOPICS:
        if not store.record_exists("topics", topic.id):
            store.write_record("topics", topic.id, _topic_record(topic))


def _topic_record(topic: Topic) -> dict[str, Any]:
    now = utc_now()
    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "scope": f"Artifacts and proposals relevant to {topic.title}.",
        "keywords": list(topic.keywords),
        "authority_envelope": {
            "allowed_actions": ["add_node"],
            "default_risk_tier": "review",
            "requires_review": True,
            "can_auto_apply": False,
            "notes": (
                "Topic runtime state may propose graph changes, but proof, "
                "review, and apply remain separate."
            ),
        },
        "runtime": _empty_runtime(),
        "created_at": now,
        "updated_at": now,
    }


def _empty_runtime() -> dict[str, None]:
    return {
        "name": None,
        "kind": None,
        "thread_id": None,
        "model": None,
        "bound_at": None,
        "updated_at": None,
    }


def _runtime_kind(runtime_name: str) -> str:
    if runtime_name == "codex":
        return "openai-codex-python-sdk"
    return "deterministic"

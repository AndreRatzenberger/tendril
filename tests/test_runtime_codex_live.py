import os
from pathlib import Path

import pytest

from tendril.artifacts import ingest_artifact
from tendril.runtime.base import ProposalRequest, validate_runtime_batch
from tendril.runtime.codex import CodexRuntime
from tendril.store import Store
from tendril.topics import get_topic


pytestmark = pytest.mark.skipif(
    os.environ.get("TENDRIL_LIVE_CODEX") != "1",
    reason="live Codex runtime smoke test is opt-in",
)


def test_live_codex_runtime_returns_proposal_contract(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text(
        "Codex topic agents should propose grounded graph changes.",
        encoding="utf-8",
    )
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    topics = [get_topic(str(topic_id)) for topic_id in artifact["extracted_topics"]]

    batch = CodexRuntime().create_proposals(
        ProposalRequest(artifact=artifact, topics=topics)
    )

    validate_runtime_batch(batch, allowed_topic_ids={topic.id for topic in topics})
    assert batch["runtime"]["name"] == "codex"

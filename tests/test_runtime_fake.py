from pathlib import Path

from tendril.artifacts import ingest_artifact
from tendril.runtime.base import ProposalRequest, validate_runtime_batch
from tendril.runtime.fake import FakeRuntime
from tendril.store import Store
from tendril.topics import get_topic


def test_fake_runtime_produces_valid_proposal_batch(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex threads need proof evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    topics = [get_topic(str(topic_id)) for topic_id in artifact["extracted_topics"]]

    batch = FakeRuntime().create_proposals(
        ProposalRequest(artifact=artifact, topics=topics)
    )

    validate_runtime_batch(batch, allowed_topic_ids={topic.id for topic in topics})
    assert batch["runtime"]["name"] == "fake"
    assert batch["runtime"]["kind"] == "deterministic"
    assert batch["runtime"]["turn_id"] == f"fake-turn-{artifact['id']}"

    proposal = batch["proposals"][0]
    assert proposal["topic_id"] == topics[0].id
    assert proposal["action"] == "add_node"
    assert proposal["evidence"][0]["artifact_id"] == artifact["id"]

from pathlib import Path

import pytest

from tendril.artifacts import ingest_artifact
from tendril.runtime.fake import FakeRuntime
from tendril.proposals import ProposalValidationError, create_proposals
from tendril.store import Store


def test_create_proposals_references_existing_artifact_and_topic(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex needs proof evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)

    proposals = create_proposals(store, artifact["id"], runtime_name="fake")

    assert proposals
    proposal = proposals[0]
    assert proposal["artifact_id"] == artifact["id"]
    assert proposal["topic_id"] in {
        "bounded-autonomy-software",
        "codex-runtime",
        "proof-and-governance",
    }
    assert proposal["evidence"]
    assert proposal["risk_tier"] == "review"
    assert proposal["status"] == "proposed"
    assert proposal["runtime"]["name"] == "fake"
    assert proposal["runtime"]["turn_id"] == f"fake-turn-{artifact['id']}"
    assert proposal["runtime_ref"]["runtime_name"] == "fake"
    assert proposal["runtime_ref"]["turn_id"] == f"fake-turn-{artifact['id']}"
    assert proposal["runtime_ref"]["casefile_id"] == f"case_{artifact['id']}"


def test_create_proposals_can_select_fake_runtime_explicitly(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex needs proof evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)

    proposals = create_proposals(store, artifact["id"], runtime_name="fake")

    assert proposals
    assert {proposal["runtime"]["name"] for proposal in proposals} == {"fake"}


def test_create_proposals_defaults_to_codex_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_runtime = None

    def fake_get_runtime(runtime_name: str) -> FakeRuntime:
        nonlocal selected_runtime
        selected_runtime = runtime_name
        return FakeRuntime()

    monkeypatch.setattr("tendril.proposals.get_runtime", fake_get_runtime)
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex needs proof evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)

    create_proposals(store, artifact["id"])

    assert selected_runtime == "codex"


def test_create_proposals_requires_existing_artifact(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    store.initialize()

    with pytest.raises(ProposalValidationError, match="Unknown artifact"):
        create_proposals(store, "art_missing")

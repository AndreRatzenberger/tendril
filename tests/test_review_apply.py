from pathlib import Path

import pytest

from tendril.artifacts import ingest_artifact
from tendril.graph import ApplyError, apply_proposal
from tendril.proof import run_proof
from tendril.proposals import create_proposals
from tendril.review import record_review
from tendril.store import Store


def test_accepted_proposal_updates_graph_with_provenance(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex proof approval evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    proposal = create_proposals(store, artifact["id"])[0]
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "grounded enough")

    result = apply_proposal(store, proposal["id"])

    assert result["applied"] is True
    graph = store.read_graph()
    assert graph["nodes"][0]["source_artifact_id"] == artifact["id"]
    assert graph["mutations"][0]["proposal_id"] == proposal["id"]
    assert graph["mutations"][0]["proof_id"] == proposal["id"]


def test_rejected_proposal_does_not_update_graph(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex proof approval evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    proposal = create_proposals(store, artifact["id"])[0]
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "reject", "too broad")

    with pytest.raises(ApplyError, match="not accepted"):
        apply_proposal(store, proposal["id"])

    assert store.read_graph()["nodes"] == []


def test_applying_without_proof_fails(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex proof approval evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    proposal = create_proposals(store, artifact["id"])[0]
    record_review(store, proposal["id"], "accept", "grounded enough")

    with pytest.raises(ApplyError, match="requires proof"):
        apply_proposal(store, proposal["id"])


def test_applying_twice_is_idempotent(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex proof approval evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    proposal = create_proposals(store, artifact["id"])[0]
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "grounded enough")

    first = apply_proposal(store, proposal["id"])
    second = apply_proposal(store, proposal["id"])

    assert first["applied"] is True
    assert second["applied"] is False
    assert second["reason"] == "already_applied"

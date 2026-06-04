from pathlib import Path

from tendril.artifacts import ingest_artifact
from tendril.proof import run_proof
from tendril.proposals import create_proposals
from tendril.store import Store


def test_valid_review_risk_proposal_is_held_for_approval(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex proof approval evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    proposal = create_proposals(store, artifact["id"])[0]

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "hold"
    assert proof["required_decision"] == "human_review"
    assert {check["name"] for check in proof["checks_run"]} >= {
        "artifact_exists",
        "topic_exists",
        "evidence_present",
        "risk_tier_present",
        "not_duplicate",
        "review_required_for_risk",
    }


def test_missing_evidence_fails_proof(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    artifact_path.write_text("Codex proof approval evidence.", encoding="utf-8")
    store = Store(tmp_path / ".tendril")
    artifact = ingest_artifact(store, artifact_path)
    proposal = create_proposals(store, artifact["id"])[0]
    proposal["evidence"] = []
    store.write_record("proposals", proposal["id"], proposal, overwrite=True)

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "reject"
    assert "missing evidence" in proof["warnings"]

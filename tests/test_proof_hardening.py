import hashlib
from pathlib import Path
from typing import Any

from tendril.artifacts import ingest_artifact
from tendril.proof import run_proof
from tendril.proof_policy import read_proof_policy
from tendril.proposals import create_proposals
from tendril.review import record_review
from tendril.graph import apply_proposal
from tendril.store import Store


def test_run_proof_persists_policy_snapshot_and_casefile(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Codex proof evidence.")
    proposal = create_proposals(store, artifact["id"])[0]

    proof = run_proof(store, proposal["id"])
    policy = read_proof_policy(store)

    assert policy["id"] == "default-proof-policy"
    assert (tmp_path / ".tendril" / "proof-policy.json").is_file()
    assert proof["policy"]["id"] == policy["id"]
    assert proof["policy"]["version"] == policy["version"]
    assert proof["casefile"]["proposal_id"] == proposal["id"]
    assert proof["casefile"]["artifact_id"] == artifact["id"]
    assert proof["casefile"]["action"] == "add_node"
    assert proof["casefile"]["summary"]


def test_malformed_proposal_schema_is_rejected(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Codex proof evidence.")
    proposal = _valid_node_proposal(artifact["id"])
    proposal["target"] = {"type": "node"}
    store.write_record("proposals", proposal["id"], proposal)

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "reject"
    assert "schema validation failed" in proof["warnings"]
    schema_check = _check(proof, "schema_valid")
    assert schema_check["passed"] is False
    assert "target.id" in schema_check["detail"]


def test_unsupported_action_is_rejected_by_policy(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Codex proof evidence.")
    proposal = _valid_node_proposal(artifact["id"])
    proposal["id"] = "prop_bad_action"
    proposal["action"] = "rewrite_graph"
    store.write_record("proposals", proposal["id"], proposal)

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "reject"
    assert "action is not allowed by proof policy" in proof["warnings"]


def test_evidence_quote_must_be_grounded_in_source_artifact(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Actual grounded source sentence.")
    proposal = _valid_node_proposal(artifact["id"])
    proposal["evidence"] = [
        {"artifact_id": artifact["id"], "quote": "A sentence that is not present."}
    ]
    store.write_record("proposals", proposal["id"], proposal)

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "reject"
    assert "evidence quote not found in source artifact" in proof["warnings"]


def test_weak_rationale_is_rejected(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Actual grounded source sentence.")
    proposal = _valid_node_proposal(artifact["id"])
    proposal["rationale"] = "seems ok"
    store.write_record("proposals", proposal["id"], proposal)

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "reject"
    assert "rationale is too weak" in proof["warnings"]


def test_unresolved_contradiction_is_rejected(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Actual grounded source sentence.")
    proposal = _valid_node_proposal(artifact["id"])
    proposal["contradicts"] = [
        {"target_id": "node_existing", "reason": "source says the opposite"}
    ]
    store.write_record("proposals", proposal["id"], proposal)

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "reject"
    assert "proposal declares unresolved contradiction" in proof["warnings"]


def test_duplicate_node_fixture_is_rejected_with_casefile_warning(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Actual grounded source sentence.")
    proposal = _valid_node_proposal(artifact["id"])
    store.write_record("proposals", proposal["id"], proposal)
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "grounded enough")
    apply_proposal(store, proposal["id"])
    duplicate = dict(proposal)
    duplicate["id"] = "prop_duplicate_node"
    store.write_record("proposals", duplicate["id"], duplicate)

    proof = run_proof(store, duplicate["id"])

    assert proof["verdict"] == "reject"
    assert "target already exists" in proof["warnings"]
    assert proof["casefile"]["warnings"] == proof["warnings"]


def _artifact(store: Store, tmp_path: Path, content: str) -> dict[str, Any]:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
    path = tmp_path / f"{digest}.md"
    path.write_text(content, encoding="utf-8")
    return ingest_artifact(store, path)


def _valid_node_proposal(artifact_id: str) -> dict[str, Any]:
    return {
        "id": "prop_valid_manual",
        "artifact_id": artifact_id,
        "topic_id": "bounded-autonomy-software",
        "created_at": "2026-06-04T00:00:00Z",
        "action": "add_node",
        "target": {
            "type": "node",
            "id": "node_manual",
            "title": "Manual node",
        },
        "rationale": "The source artifact directly supports adding this node.",
        "evidence": [{"artifact_id": artifact_id, "quote": "Actual grounded source"}],
        "risk_tier": "review",
        "status": "proposed",
    }


def _check(proof: dict[str, Any], name: str) -> dict[str, Any]:
    return next(check for check in proof["checks_run"] if check["name"] == name)

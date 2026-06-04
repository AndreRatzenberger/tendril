import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tendril.artifacts import ingest_artifact
from tendril.graph import ApplyError, apply_proposal
from tendril.meta import create_meta_proposal
from tendril.proof import run_proof
from tendril.proof_policy import read_proof_policy
from tendril.review import record_review
from tendril.store import Store


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tendril.cli", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_create_meta_proposal_records_authority_change_fields(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path)

    proposal = create_meta_proposal(
        store,
        artifact["id"],
        change_type="proof_policy",
        target="default-proof-policy",
        expected_benefit="Reject noisy proposals before review.",
        evidence_quote="Proof checks should reject noisy proposals.",
        blast_radius="Affects proof decisions for all proposals.",
        rollback_path="Restore the previous proof policy file.",
    )

    assert proposal["action"] == "meta_change"
    assert proposal["target"]["type"] == "meta_change"
    assert proposal["target"]["change_type"] == "proof_policy"
    assert proposal["expected_benefit"]
    assert proposal["blast_radius"]
    assert proposal["rollback_path"]
    assert proposal["authority_change"] is True
    assert proposal["risk_tier"] == "high"


def test_meta_proof_holds_authority_change_for_review(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path)
    proposal = _meta_proposal(store, artifact["id"])

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "hold"
    assert proof["required_decision"] == "human_review"
    assert {check["name"] for check in proof["checks_run"]} >= {
        "meta_required_fields_present",
        "review_required_for_authority_change",
    }


def test_under_specified_meta_proposal_is_rejected(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path)
    proposal = _meta_proposal(store, artifact["id"])
    proposal["rollback_path"] = ""
    store.write_record("proposals", proposal["id"], proposal, overwrite=True)

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "reject"
    assert "meta proposal missing required fields" in proof["warnings"]


def test_accepted_meta_proposal_records_change_without_mutating_policy_or_graph(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path)
    before_policy = read_proof_policy(store)
    proposal = _meta_proposal(store, artifact["id"])
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "safe to record as proposal")

    result = apply_proposal(store, proposal["id"])

    assert result["applied"] is True
    stored = store.read_record("meta_changes", proposal["id"])
    assert stored["proposal_id"] == proposal["id"]
    assert stored["status"] == "accepted"
    assert read_proof_policy(store) == before_policy
    assert store.read_graph()["mutations"] == []


def test_rejected_meta_proposal_does_not_record_change(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path)
    proposal = _meta_proposal(store, artifact["id"])
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "reject", "not worth changing authority")

    with pytest.raises(ApplyError, match="not accepted"):
        apply_proposal(store, proposal["id"])

    assert not store.record_exists("meta_changes", proposal["id"])


def test_cli_can_create_meta_proposal(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path)

    result = run_cli(
        "propose-meta",
        "--artifact",
        str(artifact["id"]),
        "--change-type",
        "proof_policy",
        "--target",
        "default-proof-policy",
        "--expected-benefit",
        "Reject noisy proposals before review.",
        "--evidence",
        "Proof checks should reject noisy proposals.",
        "--blast-radius",
        "Affects proof decisions for all proposals.",
        "--rollback-path",
        "Restore the previous proof policy file.",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["proposal"]["action"] == "meta_change"


def _artifact(store: Store, tmp_path: Path) -> dict[str, Any]:
    path = tmp_path / "meta.md"
    path.write_text(
        "Proof checks should reject noisy proposals.",
        encoding="utf-8",
    )
    return ingest_artifact(store, path)


def _meta_proposal(store: Store, artifact_id: str) -> dict[str, Any]:
    return create_meta_proposal(
        store,
        artifact_id,
        change_type="proof_policy",
        target="default-proof-policy",
        expected_benefit="Reject noisy proposals before review.",
        evidence_quote="Proof checks should reject noisy proposals.",
        blast_radius="Affects proof decisions for all proposals.",
        rollback_path="Restore the previous proof policy file.",
    )

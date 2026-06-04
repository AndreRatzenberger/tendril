import json
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tendril.artifacts import ingest_artifact
from tendril.edges import create_edge_proposal
from tendril.graph import ApplyError, apply_proposal
from tendril.proof import run_proof
from tendril.proposals import create_proposals
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


def test_create_edge_proposal_references_nodes_and_artifact(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _ingest_edge_artifact(store, tmp_path)
    source_id = _applied_node(store, tmp_path, "Source node evidence.")
    target_id = _applied_node(store, tmp_path, "Target node evidence.")

    proposal = create_edge_proposal(
        store,
        artifact["id"],
        source_id=source_id,
        target_id=target_id,
        relationship="supports",
        evidence_quote="Source node supports target node.",
    )

    assert proposal["action"] == "add_edge"
    assert proposal["target"]["type"] == "edge"
    assert proposal["target"]["source_id"] == source_id
    assert proposal["target"]["target_id"] == target_id
    assert proposal["target"]["relationship"] == "supports"
    assert proposal["risk_tier"] == "review"
    assert proposal["topology_change"] is True
    assert proposal["evidence"][0]["artifact_id"] == artifact["id"]


def test_edge_proof_holds_for_review_and_checks_endpoints(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _ingest_edge_artifact(store, tmp_path)
    source_id = _applied_node(store, tmp_path, "Source node evidence.")
    target_id = _applied_node(store, tmp_path, "Target node evidence.")
    proposal = create_edge_proposal(
        store,
        artifact["id"],
        source_id=source_id,
        target_id=target_id,
        relationship="supports",
        evidence_quote="Source node supports target node.",
    )

    proof = run_proof(store, proposal["id"])

    assert proof["verdict"] == "hold"
    assert proof["required_decision"] == "human_review"
    assert {check["name"] for check in proof["checks_run"]} >= {
        "edge_endpoints_exist",
        "not_duplicate",
        "review_required_for_topology_change",
    }


def test_accepted_edge_proposal_updates_graph_with_provenance(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _ingest_edge_artifact(store, tmp_path)
    source_id = _applied_node(store, tmp_path, "Source node evidence.")
    target_id = _applied_node(store, tmp_path, "Target node evidence.")
    proposal = create_edge_proposal(
        store,
        artifact["id"],
        source_id=source_id,
        target_id=target_id,
        relationship="supports",
        evidence_quote="Source node supports target node.",
    )
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "edge is grounded")

    result = apply_proposal(store, proposal["id"])

    assert result["applied"] is True
    graph = store.read_graph()
    edge = graph["edges"][0]
    assert edge["source_id"] == source_id
    assert edge["target_id"] == target_id
    assert edge["relationship"] == "supports"
    assert edge["source_artifact_id"] == artifact["id"]
    assert graph["mutations"][-1]["action"] == "add_edge"


def test_rejected_edge_proposal_does_not_update_graph(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _ingest_edge_artifact(store, tmp_path)
    source_id = _applied_node(store, tmp_path, "Source node evidence.")
    target_id = _applied_node(store, tmp_path, "Target node evidence.")
    proposal = create_edge_proposal(
        store,
        artifact["id"],
        source_id=source_id,
        target_id=target_id,
        relationship="supports",
        evidence_quote="Source node supports target node.",
    )
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "reject", "edge is too broad")

    with pytest.raises(ApplyError, match="not accepted"):
        apply_proposal(store, proposal["id"])

    assert store.read_graph()["edges"] == []


def test_duplicate_edge_proof_rejects_exact_topology_duplicate(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _ingest_edge_artifact(store, tmp_path)
    source_id = _applied_node(store, tmp_path, "Source node evidence.")
    target_id = _applied_node(store, tmp_path, "Target node evidence.")
    proposal = create_edge_proposal(
        store,
        artifact["id"],
        source_id=source_id,
        target_id=target_id,
        relationship="supports",
        evidence_quote="Source node supports target node.",
    )
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "edge is grounded")
    apply_proposal(store, proposal["id"])
    duplicate = dict(proposal)
    duplicate["id"] = "prop_duplicate_edge"
    store.write_record("proposals", duplicate["id"], duplicate)

    proof = run_proof(store, duplicate["id"])

    assert proof["verdict"] == "reject"
    assert "target already exists" in proof["warnings"]


def test_cli_can_create_edge_proposal(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _ingest_edge_artifact(store, tmp_path)
    source_id = _applied_node(store, tmp_path, "Source node evidence.")
    target_id = _applied_node(store, tmp_path, "Target node evidence.")

    result = run_cli(
        "propose-edge",
        "--artifact",
        str(artifact["id"]),
        "--source",
        source_id,
        "--target",
        target_id,
        "--relationship",
        "supports",
        "--evidence",
        "Source node supports target node.",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["proposal"]["action"] == "add_edge"


def _ingest_edge_artifact(store: Store, tmp_path: Path) -> dict[str, Any]:
    artifact_path = tmp_path / "edge.md"
    artifact_path.write_text(
        "Source node supports target node.",
        encoding="utf-8",
    )
    return ingest_artifact(store, artifact_path)


def _applied_node(store: Store, tmp_path: Path, content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
    artifact_path = tmp_path / f"{digest}.md"
    artifact_path.write_text(content, encoding="utf-8")
    artifact = ingest_artifact(store, artifact_path)
    proposal = create_proposals(store, artifact["id"])[0]
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "node is grounded")
    apply_proposal(store, proposal["id"])
    return str(proposal["target"]["id"])

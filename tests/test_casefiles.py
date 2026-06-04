import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tendril.artifacts import ingest_artifact
from tendril.casefiles import build_casefile, list_pending_proposals
from tendril.graph import apply_proposal
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


def test_queue_tracks_pending_proposal_states(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    proposal = _proposal(store, tmp_path, "Proof queue evidence.")

    assert list_pending_proposals(store)["items"][0]["status"] == "pending_proof"

    run_proof(store, proposal["id"])
    assert list_pending_proposals(store)["items"][0]["status"] == "pending_review"

    record_review(store, proposal["id"], "accept", "ready to apply")
    assert (
        list_pending_proposals(store)["items"][0]["status"]
        == "accepted_pending_apply"
    )

    apply_proposal(store, proposal["id"])
    assert list_pending_proposals(store)["items"] == []


def test_rejected_proposal_is_not_pending(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    proposal = _proposal(store, tmp_path, "Proof reject evidence.")
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "reject", "not grounded enough")

    assert list_pending_proposals(store)["items"] == []


def test_casefile_points_to_raw_records_after_apply(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    artifact = _artifact(store, tmp_path, "Proof casefile evidence.")
    proposal = create_proposals(store, artifact["id"])[0]
    run_proof(store, proposal["id"])
    record_review(store, proposal["id"], "accept", "grounded enough")
    apply_proposal(store, proposal["id"])

    casefile = build_casefile(store, proposal["id"])

    assert casefile["proposal_id"] == proposal["id"]
    assert casefile["summary"]
    assert casefile["records"]["artifact"]["path"] == (
        f".tendril/artifacts/{artifact['id']}.json"
    )
    assert casefile["records"]["proposal"]["path"] == (
        f".tendril/proposals/{proposal['id']}.json"
    )
    assert casefile["records"]["proof"]["path"] == (
        f".tendril/proofs/{proposal['id']}.json"
    )
    assert casefile["records"]["decision"]["path"] == (
        f".tendril/decisions/{proposal['id']}.json"
    )
    assert casefile["records"]["graph"]["path"] == ".tendril/graph.json"
    assert casefile["mutation"]["proposal_id"] == proposal["id"]


def test_cli_can_list_queue_and_show_casefile(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    proposal = _proposal(store, tmp_path, "Proof CLI evidence.")
    run_proof(store, proposal["id"])

    queue = run_cli("queue", cwd=tmp_path)
    assert queue.returncode == 0, queue.stderr
    assert json.loads(queue.stdout)["items"][0]["proposal_id"] == proposal["id"]

    casefile = run_cli("casefile", "--proposal", proposal["id"], cwd=tmp_path)
    assert casefile.returncode == 0, casefile.stderr
    payload = json.loads(casefile.stdout)
    assert payload["proposal_id"] == proposal["id"]
    assert payload["records"]["proposal"]["path"].endswith(f"{proposal['id']}.json")


def _proposal(store: Store, tmp_path: Path, content: str) -> dict[str, Any]:
    artifact = _artifact(store, tmp_path, content)
    return create_proposals(store, artifact["id"])[0]


def _artifact(store: Store, tmp_path: Path, content: str) -> dict[str, Any]:
    path = tmp_path / f"{len(content)}.md"
    path.write_text(content, encoding="utf-8")
    return ingest_artifact(store, path)

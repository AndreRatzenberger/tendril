import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tendril.artifacts import ingest_artifact
from tendril.runtime.base import ProposalRequest, validate_runtime_batch
from tendril.runtime.codex import CodexRuntime
from tendril.store import Store
from tendril.topics import get_topic


pytestmark = pytest.mark.skipif(
    shutil.which("codex") is None,
    reason="live Codex runtime smoke test requires the codex CLI",
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


def test_live_codex_runtime_cli_loop_reaches_proof(tmp_path: Path) -> None:
    artifact_path = tmp_path / "live-codex-artifact.md"
    artifact_path.write_text(
        (
            "Codex runtime proposals should stay grounded in artifact evidence "
            "before graph changes reach review."
        ),
        encoding="utf-8",
    )

    ingest = _run_cli("ingest", str(artifact_path), cwd=tmp_path)
    assert ingest.returncode == 0, ingest.stderr
    artifact_id = json.loads(ingest.stdout)["artifact_id"]

    propose = _run_cli(
        "propose",
        "--artifact",
        artifact_id,
        "--runtime",
        "codex",
        cwd=tmp_path,
    )
    assert propose.returncode == 0, propose.stderr
    propose_payload = json.loads(propose.stdout)
    proposal = propose_payload["proposals"][0]
    assert propose_payload["runtime"] == "codex"
    assert proposal["runtime"]["name"] == "codex"
    assert proposal["runtime_ref"]["runtime_name"] == "codex"

    proof = _run_cli("proof", "--proposal", proposal["id"], cwd=tmp_path)
    assert proof.returncode == 0, proof.stderr
    proof_payload = json.loads(proof.stdout)
    assert proof_payload["verdict"] in {"accept", "hold"}
    assert proof_payload["warnings"] == []


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tendril.cli", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )

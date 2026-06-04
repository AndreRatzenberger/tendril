import json
import subprocess
import sys
from pathlib import Path


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tendril.cli", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_help_lists_m0_commands(tmp_path: Path) -> None:
    result = run_cli("--help", cwd=tmp_path)

    assert result.returncode == 0
    for command in ["ingest", "propose", "proof", "review", "apply"]:
        assert command in result.stdout


def test_cli_runs_full_m0_loop(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.md"
    artifact.write_text(
        "# Codex proof note\n\nCodex threads need proof and approval state.\n",
        encoding="utf-8",
    )

    ingest = run_cli("ingest", str(artifact), cwd=tmp_path)
    assert ingest.returncode == 0, ingest.stderr
    artifact_id = json.loads(ingest.stdout)["artifact_id"]

    propose = run_cli(
        "propose",
        "--artifact",
        artifact_id,
        "--runtime",
        "fake",
        cwd=tmp_path,
    )
    assert propose.returncode == 0, propose.stderr
    propose_payload = json.loads(propose.stdout)
    proposal_id = propose_payload["proposal_ids"][0]
    assert propose_payload["runtime"] == "fake"
    assert propose_payload["proposals"][0]["runtime"]["name"] == "fake"

    proof = run_cli("proof", "--proposal", proposal_id, cwd=tmp_path)
    assert proof.returncode == 0, proof.stderr
    assert json.loads(proof.stdout)["verdict"] == "hold"

    rejected = run_cli(
        "review",
        "--proposal",
        proposal_id,
        "--decision",
        "reject",
        "--reason",
        "too broad",
        cwd=tmp_path,
    )
    assert rejected.returncode == 0, rejected.stderr

    rejected_apply = run_cli("apply", "--proposal", proposal_id, cwd=tmp_path)
    assert rejected_apply.returncode != 0
    assert "not accepted" in rejected_apply.stderr

    accepted = run_cli(
        "review",
        "--proposal",
        proposal_id,
        "--decision",
        "accept",
        "--reason",
        "grounded enough for M0",
        cwd=tmp_path,
    )
    assert accepted.returncode == 0, accepted.stderr

    applied = run_cli("apply", "--proposal", proposal_id, cwd=tmp_path)
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)["applied"] is True

    graph = json.loads((tmp_path / ".tendril" / "graph.json").read_text())
    assert graph["nodes"]
    assert graph["mutations"][0]["proposal_id"] == proposal_id


def test_missing_required_arguments_fail_clearly(tmp_path: Path) -> None:
    result = run_cli("propose", cwd=tmp_path)

    assert result.returncode != 0
    assert "required" in result.stderr.lower()

import json
import subprocess

import pytest

from tendril.runtime.base import ProposalRequest, TendrilRuntimeError
from tendril.runtime.codex import CodexRuntime, CODEX_PROPOSAL_SCHEMA
from tendril.topics import get_topic


def test_codex_prompt_includes_artifact_topics_and_schema() -> None:
    artifact = {
        "id": "art_123",
        "content": "Codex topic agents should produce grounded graph proposals.",
        "path": "example.md",
    }
    topic = get_topic("codex-runtime")

    prompt = CodexRuntime(model="gpt-5.4").build_prompt(
        ProposalRequest(artifact=artifact, topics=[topic])
    )

    assert "art_123" in prompt
    assert "codex-runtime" in prompt
    assert "JSON only" in prompt
    assert CODEX_PROPOSAL_SCHEMA["required"] == ["proposals"]


def test_codex_response_parser_accepts_contract_shape() -> None:
    response = {
        "proposals": [
            {
                "topic_id": "codex-runtime",
                "action": "add_node",
                "target": {
                    "type": "node",
                    "id": "node_art_123_codex-runtime",
                    "title": "Codex runtime note",
                },
                "rationale": "The artifact discusses Codex runtime state.",
                "evidence": [{"artifact_id": "art_123", "quote": "Codex runtime"}],
                "risk_tier": "review",
                "status": "proposed",
            }
        ]
    }

    parsed = CodexRuntime.parse_response(json.dumps(response))

    assert parsed == response


def test_codex_response_parser_rejects_missing_proposals() -> None:
    with pytest.raises(TendrilRuntimeError, match="proposals"):
        CodexRuntime.parse_response("{}")


def test_codex_response_parser_rejects_empty_proposal_batch() -> None:
    runtime = CodexRuntime()

    with pytest.raises(TendrilRuntimeError, match="at least one proposal"):
        runtime.parse_response('{"proposals": []}')


def test_codex_runtime_invokes_codex_cli(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = {
        "id": "art_123",
        "content": "Codex topic agents should produce grounded graph proposals.",
        "path": "example.md",
    }
    topic = get_topic("codex-runtime")
    response = {
        "proposals": [
            {
                "topic_id": "codex-runtime",
                "action": "add_node",
                "target": {
                    "type": "node",
                    "id": "node_art_123_codex-runtime",
                    "title": "Codex runtime note",
                },
                "rationale": "The artifact discusses Codex runtime state.",
                "evidence": [{"artifact_id": "art_123", "quote": "Codex runtime"}],
                "risk_tier": "review",
                "status": "proposed",
            }
        ]
    }
    calls = []

    def fake_run(command, *, input, text, capture_output, check):
        calls.append(
            {
                "command": command,
                "input": input,
                "text": text,
                "capture_output": capture_output,
                "check": check,
            }
        )
        response_path = command[command.index("--output-last-message") + 1]
        with open(response_path, "w", encoding="utf-8") as handle:
            json.dump(response, handle)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("tendril.runtime.codex.shutil.which", lambda name: "/bin/codex")
    monkeypatch.setattr("tendril.runtime.codex.subprocess.run", fake_run)
    monkeypatch.chdir(tmp_path)

    batch = CodexRuntime(model="gpt-5.4").create_proposals(
        ProposalRequest(artifact=artifact, topics=[topic])
    )

    command = calls[0]["command"]
    assert command[:2] == ["/bin/codex", "exec"]
    assert "--output-schema" in command
    assert "--output-last-message" in command
    assert calls[0]["input"]
    assert batch["runtime"]["kind"] == "codex-cli"
    assert batch["proposals"] == response["proposals"]

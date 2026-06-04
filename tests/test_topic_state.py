import json
import subprocess
import sys
from pathlib import Path

from tendril.store import Store
from tendril.topic_state import (
    bind_topic_runtime,
    clear_topic_runtime,
    list_topic_records,
    read_topic_record,
)


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tendril.cli", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_topic_records_include_runtime_and_authority_envelope(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / ".tendril")

    topics = list_topic_records(store)

    codex_topic = next(topic for topic in topics if topic["id"] == "codex-runtime")
    assert codex_topic["runtime"]["name"] is None
    assert codex_topic["authority_envelope"]["default_risk_tier"] == "review"
    assert "add_node" in codex_topic["authority_envelope"]["allowed_actions"]
    assert (tmp_path / ".tendril" / "topics" / "codex-runtime.json").is_file()


def test_topic_runtime_binding_survives_store_reopen(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")

    bound = bind_topic_runtime(
        store,
        "codex-runtime",
        runtime_name="codex",
        thread_id="thr_123",
        model="gpt-5.4",
    )
    reopened = read_topic_record(Store(tmp_path / ".tendril"), "codex-runtime")

    assert bound["runtime"]["name"] == "codex"
    assert bound["runtime"]["kind"] == "openai-codex-python-sdk"
    assert reopened["runtime"]["thread_id"] == "thr_123"
    assert reopened["runtime"]["model"] == "gpt-5.4"
    assert reopened["authority_envelope"]["requires_review"] is True


def test_topic_runtime_clear_preserves_authority_envelope(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    bind_topic_runtime(
        store,
        "codex-runtime",
        runtime_name="codex",
        thread_id="thr_123",
        model="gpt-5.4",
    )

    cleared = clear_topic_runtime(store, "codex-runtime")

    assert cleared["runtime"]["name"] is None
    assert cleared["runtime"]["thread_id"] is None
    assert cleared["authority_envelope"]["requires_review"] is True


def test_cli_can_show_bind_and_clear_topic_runtime(tmp_path: Path) -> None:
    shown = run_cli("topic", "show", "codex-runtime", cwd=tmp_path)
    assert shown.returncode == 0, shown.stderr
    assert json.loads(shown.stdout)["id"] == "codex-runtime"

    bound = run_cli(
        "topic",
        "bind-runtime",
        "codex-runtime",
        "--runtime",
        "codex",
        "--thread-id",
        "thr_123",
        "--model",
        "gpt-5.4",
        cwd=tmp_path,
    )
    assert bound.returncode == 0, bound.stderr
    assert json.loads(bound.stdout)["runtime"]["thread_id"] == "thr_123"

    reshown = run_cli("topic", "show", "codex-runtime", cwd=tmp_path)
    assert json.loads(reshown.stdout)["runtime"]["thread_id"] == "thr_123"

    cleared = run_cli("topic", "clear-runtime", "codex-runtime", cwd=tmp_path)
    assert cleared.returncode == 0, cleared.stderr
    assert json.loads(cleared.stdout)["runtime"]["thread_id"] is None

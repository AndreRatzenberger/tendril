import json
from pathlib import Path

import pytest

from tendril.store import DuplicateRecordError, Store


def test_store_initialization_creates_expected_directories(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    store.initialize()

    for name in ["artifacts", "proposals", "proofs", "decisions", "topics"]:
        assert (tmp_path / ".tendril" / name).is_dir()
    assert json.loads((tmp_path / ".tendril" / "graph.json").read_text()) == {
        "nodes": [],
        "edges": [],
        "mutations": [],
    }


def test_write_json_refuses_to_overwrite_existing_records(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")
    store.initialize()

    store.write_record("artifacts", "artifact-1", {"id": "artifact-1"})

    with pytest.raises(DuplicateRecordError):
        store.write_record("artifacts", "artifact-1", {"id": "artifact-1"})

import hashlib
from pathlib import Path

import pytest

from tendril.artifacts import ingest_artifact
from tendril.store import Store


def test_ingest_artifact_records_metadata_and_content_hash(tmp_path: Path) -> None:
    artifact_path = tmp_path / "note.md"
    content = "# Note\n\nCodex needs approval evidence.\n"
    artifact_path.write_text(content, encoding="utf-8")
    store = Store(tmp_path / ".tendril")

    artifact = ingest_artifact(store, artifact_path)

    assert artifact["id"].startswith("art_")
    assert artifact["path"] == str(artifact_path)
    assert artifact["source_type"] == "markdown"
    assert artifact["sha256"] == hashlib.sha256(content.encode()).hexdigest()
    assert artifact["content"] == content


def test_ingest_missing_file_fails_clearly(tmp_path: Path) -> None:
    store = Store(tmp_path / ".tendril")

    with pytest.raises(FileNotFoundError, match="Artifact not found"):
        ingest_artifact(store, tmp_path / "missing.md")

import hashlib
from pathlib import Path

import pytest

from tendril.artifacts import ingest_artifact, ingest_research_digest
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


def test_ingest_research_digest_records_findings_and_sources(
    tmp_path: Path,
) -> None:
    store = Store(tmp_path / ".tendril")

    artifact = ingest_research_digest(
        store,
        query="latest merger news about ExampleCo and SampleCorp",
        findings=[
            "ExampleCo agreed to acquire SampleCorp for 4.2 billion dollars.",
            "The companies expect the merger to close after regulator review.",
        ],
        sources=[
            {
                "title": "ExampleCo press release",
                "url": "https://example.com/news/exampleco-samplecorp",
                "published_at": "2026-06-04",
            },
            {
                "title": "Wire report",
                "url": "https://example.com/wire/exampleco-samplecorp",
                "published_at": "2026-06-04",
            },
        ],
        caveats=["Terms may change before closing."],
    )

    assert artifact["id"].startswith("art_")
    assert artifact["path"] is None
    assert artifact["source_type"] == "research_digest"
    assert artifact["research"]["query"] == (
        "latest merger news about ExampleCo and SampleCorp"
    )
    assert artifact["research"]["findings"][0].startswith("ExampleCo agreed")
    assert artifact["research"]["sources"][0]["title"] == "ExampleCo press release"
    assert artifact["research"]["caveats"] == ["Terms may change before closing."]
    assert "## Findings" in artifact["content"]
    assert "ExampleCo agreed to acquire SampleCorp" in artifact["content"]
    assert "https://example.com/news/exampleco-samplecorp" in artifact["content"]

    stored = store.read_record("artifacts", artifact["id"])
    assert stored == artifact

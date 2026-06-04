from __future__ import annotations

import hashlib
from pathlib import Path

from tendril.store import Store
from tendril.time import utc_now
from tendril.topics import select_topics


def ingest_artifact(store: Store, artifact_path: Path) -> dict[str, object]:
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    if not artifact_path.is_file():
        raise FileNotFoundError(f"Artifact is not a file: {artifact_path}")

    content = artifact_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    artifact_id = f"art_{digest[:16]}"
    source_type = "markdown" if artifact_path.suffix.lower() == ".md" else "text"
    topic_matches = select_topics(content)

    artifact: dict[str, object] = {
        "id": artifact_id,
        "path": str(artifact_path),
        "source_type": source_type,
        "created_at": utc_now(),
        "sha256": digest,
        "content": content,
        "extracted_topics": [match["topic_id"] for match in topic_matches],
        "topic_matches": topic_matches,
    }
    store.write_record("artifacts", artifact_id, artifact, overwrite=True)
    return artifact

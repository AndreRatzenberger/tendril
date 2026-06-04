from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tendril.store import Store
from tendril.time import utc_now
from tendril.topics import select_topics


class ResearchDigestError(Exception):
    """Raised when a research digest cannot be ingested."""


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


def ingest_research_digest(
    store: Store,
    *,
    query: str,
    findings: list[str],
    sources: list[dict[str, str]],
    caveats: list[str] | None = None,
) -> dict[str, Any]:
    query = query.strip()
    findings = [finding.strip() for finding in findings if finding.strip()]
    caveats = [caveat.strip() for caveat in caveats or [] if caveat.strip()]
    sources = [_normalize_source(source) for source in sources]

    if not query:
        raise ResearchDigestError("Research query is required")
    if not findings:
        raise ResearchDigestError("At least one research finding is required")
    if not sources:
        raise ResearchDigestError("At least one research source is required")

    content = _research_digest_content(
        query=query,
        findings=findings,
        sources=sources,
        caveats=caveats,
    )
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    artifact_id = f"art_{digest[:16]}"
    topic_matches = select_topics(content)

    artifact: dict[str, Any] = {
        "id": artifact_id,
        "path": None,
        "source_type": "research_digest",
        "created_at": utc_now(),
        "sha256": digest,
        "content": content,
        "extracted_topics": [match["topic_id"] for match in topic_matches],
        "topic_matches": topic_matches,
        "research": {
            "query": query,
            "findings": findings,
            "sources": sources,
            "caveats": caveats,
        },
    }
    store.write_record("artifacts", artifact_id, artifact, overwrite=True)
    return artifact


def _normalize_source(source: dict[str, str]) -> dict[str, str]:
    normalized = {
        "title": str(source.get("title", "")).strip(),
        "url": str(source.get("url", "")).strip(),
        "published_at": str(source.get("published_at", "")).strip(),
    }
    missing = [key for key, value in normalized.items() if not value]
    if missing:
        raise ResearchDigestError(f"Research source missing fields: {missing}")
    return normalized


def _research_digest_content(
    *,
    query: str,
    findings: list[str],
    sources: list[dict[str, str]],
    caveats: list[str],
) -> str:
    lines = [
        "# Research Digest",
        "",
        f"Query: {query}",
        "",
        "## Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in findings)
    lines.extend(["", "## Sources", ""])
    lines.extend(
        (
            f"- {source['title']} ({source['published_at']}): "
            f"{source['url']}"
        )
        for source in sources
    )
    if caveats:
        lines.extend(["", "## Caveats", ""])
        lines.extend(f"- {caveat}" for caveat in caveats)
    lines.append("")
    return "\n".join(lines)

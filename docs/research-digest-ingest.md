# Research Digest Ingest

## Purpose

Research digest ingest lets an operator turn live research into a normal
Tendril artifact without making web search a hidden mutation path.

The research can happen outside Tendril: in a browser, through an agent with web
access, or through another research tool. Tendril receives the sourced digest
and then uses the existing loop:

```text
research digest -> proposal -> proof -> review -> apply -> casefile
```

## CLI

```bash
uv run tendril ingest \
  --research-query "latest merger news about ExampleCo and SampleCorp" \
  --finding "ExampleCo agreed to acquire SampleCorp for 4.2 billion dollars." \
  --finding "The companies expect the merger to close after regulator review." \
  --source "ExampleCo press release|https://example.com/news|2026-06-04" \
  --source "Wire report|https://example.com/wire|2026-06-04" \
  --caveat "Terms may change before closing."
```

Each source uses:

```text
title|url|published_at
```

The command writes an artifact with:

- `source_type: research_digest`
- `research.query`
- `research.findings`
- `research.sources`
- `research.caveats`
- generated markdown `content`
- normal topic matches and content hash

## Safety Shape

The digest is not applied to the graph directly. It is just an artifact.

After ingest, use the normal commands:

```bash
uv run tendril propose --artifact <artifact-id>
uv run tendril proof --proposal <proposal-id>
uv run tendril queue
uv run tendril review --proposal <proposal-id> --decision accept --reason "..."
uv run tendril apply --proposal <proposal-id>
uv run tendril casefile --proposal <proposal-id>
```

This keeps live research useful while preserving the same proof, review, and
provenance rules as file-based ingest.

## Current Boundary

Tendril does not perform built-in web search in this milestone. That is
intentional. A future runtime adapter can automate the research phase, but it
should still produce a sourced digest artifact before proposing graph changes.

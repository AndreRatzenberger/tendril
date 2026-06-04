# M0 Perfect Loop Goal Prompt

Use this prompt to start the first implementation pass for Tendril.

## Short Prompt

```text
Build Tendril M0 from docs/goals/m0-perfect-loop.md. Keep the loop tiny,
deterministic, public-safe, and fully testable.
```

## Full Goal Prompt

```text
You are implementing Tendril M0.

Tendril is a public prototype for a self-tending knowledge graph. The M0 goal is
not to build a large agent system. The goal is to make one local graph-change
loop real, inspectable, and trustworthy:

artifact ingested
-> topic selected
-> graph-change proposal created
-> proof checks run
-> human decision recorded
-> accepted proposal mutates the graph with provenance

Read these first:

1. README.md
2. AGENTS.md
3. docs/prd.md
4. docs/architecture.md
5. docs/decisions.md
6. docs/implementation-plan.md

Then implement M0 only.

## M0 Deliverable

Create a Python CLI named `tendril` with these commands:

- `tendril ingest path/to/artifact.md`
- `tendril propose --artifact <artifact-id>`
- `tendril proof --proposal <proposal-id>`
- `tendril review --proposal <proposal-id> --decision accept|reject --reason "..."`
- `tendril apply --proposal <proposal-id>`

Use a local `.tendril/` working store. Keep it simple and inspectable.

## Perfect M0 Means

- A clean checkout can run the full loop from a sample markdown artifact.
- Every stored object is human-readable JSON.
- Every proposal references an existing artifact and topic.
- Every proof result records checks, warnings, and verdict.
- No graph mutation happens without proposal plus proof.
- No review-required proposal applies without explicit acceptance.
- Rejected proposals remain recorded.
- Applying a proposal twice is impossible or clearly idempotent.
- Tests cover the happy path and the important hold/reject paths.
- README documents the exact commands for the demo.

## Scope

Implement:

- project package skeleton
- CLI argument parsing
- local JSON store
- artifact ingest
- deterministic topic selection
- deterministic proposal generation
- deterministic proof checks
- review decision recording
- graph apply logic
- sample artifact
- README demo commands
- tests

Do not implement:

- Codex SDK calls
- app-server integration
- web UI
- daemon/background polling
- model-assisted proof
- automatic high-risk application
- complex graph database
- ontology migration

M0 should make the substrate credible before adding live Codex-backed agents.

## Design Bias

Prefer boring clarity over clever architecture.

Use a few focused modules:

- `src/tendril/cli.py`
- `src/tendril/store.py`
- `src/tendril/artifacts.py`
- `src/tendril/topics.py`
- `src/tendril/proposals.py`
- `src/tendril/proof.py`
- `src/tendril/review.py`
- `src/tendril/graph.py`

Use `uv` for Python project setup and commands.

Use tests as the main spec. The CLI should be pleasant for a human operator,
but the core behavior should be testable without shelling out for every case.

## Public-Safety Rule

This repository is public. Do not add repo-local continuity vaults, private
source maps, local absolute paths, private research captures, secrets, or chat
session files.

## Suggested Verification

Run:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
git diff --check
```

Then run the documented README demo from a clean `.tendril/` store.

## Final Report

When done, report:

- commands implemented
- files created
- tests run
- README demo result
- any M1 questions discovered
```

## Why This Is The Right First Goal

The temptation is to start with Codex integration because Tendril is a Codex
project. Resist that for M0.

The first proof of value is not that a model can suggest graph links. The first
proof of value is that Tendril has a trustworthy acceptance surface for graph
growth. Once the proposal, proof, review, and apply loop is real, Codex-backed
topic agents can plug into the proposal step without changing the governance
shape.

# Tendril Implementation Plan

> **For agentic workers:** implement this plan task by task. Keep commits
> small. Do not add repo-local continuity vaults or private source maps.

**Goal:** Build the M0 local graph-change proposal loop, then add Codex-backed
proposal generation in M1.

**Architecture:** M0 is a deterministic local CLI over inspectable files. M1
adds Codex-backed topic-agent turns while preserving the same proposal, proof,
review, and apply surfaces.

**Tech Stack:** Python 3.10+, `uv`, local JSON files, optional Codex SDK or
app-server integration after M0.

---

## Milestone M0: Local Proposal Loop

### Task 1: Package And CLI Skeleton

**Files:**

- Create: `pyproject.toml`
- Create: `src/tendril/__init__.py`
- Create: `src/tendril/cli.py`
- Create: `tests/test_cli.py`

**Behavior:**

Create a `tendril` CLI with these subcommands:

- `ingest`
- `propose`
- `proof`
- `review`
- `apply`

The commands may start as thin shells, but they should parse arguments and
return clear errors for missing inputs.

**Tests:**

- `tendril --help` lists all subcommands.
- each subcommand has help output.
- missing required arguments exit non-zero.

### Task 2: Local Store

**Files:**

- Create: `src/tendril/store.py`
- Create: `tests/test_store.py`

**Behavior:**

Create a local `.tendril/` store with directories:

- `artifacts/`
- `proposals/`
- `proofs/`
- `decisions/`

Add helpers for reading and writing JSON atomically.

**Tests:**

- store initialization creates expected directories.
- JSON writes are readable.
- duplicate IDs do not silently overwrite records.

### Task 3: Artifact Ingest

**Files:**

- Create: `src/tendril/artifacts.py`
- Modify: `src/tendril/cli.py`
- Create: `tests/test_artifacts.py`

**Behavior:**

`tendril ingest path/to/artifact.md` stores an artifact record with:

- stable ID
- original path
- source type
- created timestamp
- SHA-256 hash
- content snapshot or stored copy

**Tests:**

- ingesting a markdown file creates an artifact record.
- missing files fail with a clear message.
- the stored hash matches the input content.

### Task 4: Deterministic Topic Selection

**Files:**

- Create: `src/tendril/topics.py`
- Create: `tests/test_topics.py`

**Behavior:**

Define initial built-in topics:

- `bounded-autonomy-software`
- `codex-runtime`
- `proof-and-governance`

In M0, topic selection can be keyword-based. It should return at least one
topic for a valid artifact and expose why each topic matched.

**Tests:**

- artifacts mentioning Codex match `codex-runtime`.
- artifacts mentioning proof, approval, or governance match
  `proof-and-governance`.
- unrelated artifacts fall back to a safe default topic or produce a clear
  no-topic result.

### Task 5: Graph-Change Proposal

**Files:**

- Create: `src/tendril/proposals.py`
- Modify: `src/tendril/cli.py`
- Create: `tests/test_proposals.py`

**Behavior:**

`tendril propose --artifact <id>` creates one or more proposal records.

Each proposal includes:

- `id`
- `artifact_id`
- `topic_id`
- `action`
- `target`
- `rationale`
- `evidence`
- `risk_tier`
- `status`

M0 proposals can be deterministic summaries based on topic matches and artifact
metadata.

**Tests:**

- proposals reference an existing artifact.
- proposals reference an existing topic.
- malformed proposal records are rejected.
- duplicate proposal IDs are not allowed.

### Task 6: Proof Checks

**Files:**

- Create: `src/tendril/proof.py`
- Modify: `src/tendril/cli.py`
- Create: `tests/test_proof.py`

**Behavior:**

`tendril proof --proposal <id>` runs deterministic checks:

- source artifact exists
- target topic exists
- evidence is present
- risk tier is present
- duplicate exact node or edge is not already present
- high-risk proposals require review

The proof result records `verdict`, `warnings`, and `required_decision`.

**Tests:**

- valid low-risk proposal passes proof.
- missing evidence fails proof.
- unknown topic fails proof.
- high-risk proposal is held for human approval.

### Task 7: Review And Apply

**Files:**

- Create: `src/tendril/review.py`
- Create: `src/tendril/graph.py`
- Modify: `src/tendril/cli.py`
- Create: `tests/test_review_apply.py`

**Behavior:**

`tendril review --proposal <id>` records an accept or reject decision.

`tendril apply --proposal <id>` mutates `graph.json` only when:

- the proposal has a passing proof result
- the proposal has an accepted review decision when required
- the proposal has not already been applied

**Tests:**

- accepted proposal updates the graph.
- rejected proposal does not update the graph.
- applying without proof fails.
- applying twice is idempotent or fails clearly.

### Task 8: Documentation And Example

**Files:**

- Modify: `README.md`
- Create: `examples/artifacts/codex-thread-state.md`

**Behavior:**

Document the M0 loop with copy-pasteable commands and a sample artifact.

**Tests:**

- run the README commands against the example artifact from a clean store.
- verify a graph mutation is produced only after review.

## Milestone M1: Codex-Backed Topic Agent

### Task 9: Runtime Adapter Boundary

**Files:**

- Create: `src/tendril/runtime/base.py`
- Create: `src/tendril/runtime/fake.py`
- Create: `tests/test_runtime_fake.py`

**Behavior:**

Define an adapter interface for proposal generation. The fake adapter should
return deterministic proposals and keep tests independent from Codex auth.

**Tests:**

- fake adapter produces a valid proposal.
- CLI can select fake runtime explicitly.

### Task 10: Codex Runtime Spike

**Files:**

- Create: `docs/codex-runtime-spike.md`
- Create: `src/tendril/runtime/codex.py`
- Create: `tests/test_runtime_codex_contract.py`

**Behavior:**

Document whether the first Codex-backed runtime should use:

- TypeScript Codex SDK
- Python Codex SDK
- app-server JSON-RPC directly
- `codex exec` as a temporary bridge

Implementation should be behind a clear boundary and skipped in tests unless
Codex credentials are available.

**Tests:**

- contract tests validate request and response shape without live Codex calls.
- live smoke test is opt-in.

## Verification

Run before merging M0:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
git diff --check
```

Run before merging M1:

```bash
uv run pytest
uv run ruff check .
git diff --check
```

If live Codex runtime tests exist, they must be opt-in and skipped by default.

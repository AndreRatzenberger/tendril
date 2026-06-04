# Operator Casefiles

## Purpose

M6 makes Tendril easier to inspect without hiding the underlying JSON records.

The operator surface has two commands:

```bash
uv run tendril queue
uv run tendril casefile --proposal <proposal-id>
```

`queue` answers "what still needs attention?"

`casefile` answers "why did this proposal exist, what checked it, who decided,
and what changed?"

## Pending Queue

The queue lists proposals that still need operator or system action:

- `pending_proof`: proposal exists but proof has not run.
- `pending_review`: proof passed, but explicit review is required.
- `accepted_pending_apply`: review accepted the proposal, but it has not been
  applied yet.

The queue intentionally excludes:

- applied proposals
- rejected proposals
- proof-rejected proposals

Each queue item includes a short summary and a `record_path` pointing to the
proposal JSON under `.tendril/proposals/`.

## Casefile Shape

A casefile is a summary assembled from existing records. It is not a replacement
for the raw data.

For a content or edge proposal, the casefile points to:

- artifact record: `.tendril/artifacts/<artifact-id>.json`
- proposal record: `.tendril/proposals/<proposal-id>.json`
- proof record: `.tendril/proofs/<proposal-id>.json`
- decision record: `.tendril/decisions/<proposal-id>.json`
- graph record: `.tendril/graph.json`

It also includes a compact mutation summary when the proposal has been applied.

For a meta proposal, the casefile can also point to:

- accepted meta-change record: `.tendril/meta_changes/<proposal-id>.json`

## Statuses

Casefiles can report:

- `pending_proof`
- `pending_review`
- `accepted_pending_apply`
- `proof_rejected`
- `rejected`
- `applied`

These statuses are derived from the current proposal, proof, decision, graph,
and meta-change records. Tendril does not store a separate casefile record in
M6.

## Why This Matters

Autonomous systems fail quietly when operators cannot reconstruct decisions.
M6 keeps the reconstruction cheap:

```text
artifact -> proposal -> proof -> decision -> mutation
```

The human-readable summary helps scanning. The raw JSON paths keep the evidence
inspectable.

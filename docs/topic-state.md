# Topic State

## Purpose

M2 makes Tendril topics visible as persisted graph work cells.

Before M2, built-in topics existed only as Python constants. After M2, Tendril
creates inspectable topic records in the local working store:

```text
.tendril/
  topics/
    bounded-autonomy-software.json
    codex-runtime.json
    proof-and-governance.json
```

The records are still small and local. They are not a graph database and they
are not private continuity material.

## What Is Persisted

Each topic record stores:

- topic ID
- title
- description
- scope
- keywords
- authority envelope
- runtime handle metadata
- created and updated timestamps

The authority envelope makes the topic's current powers explicit:

- allowed proposal actions
- default risk tier
- whether review is required
- whether auto-apply is allowed
- a short note about the proof and review boundary

The runtime handle stores only resumability metadata:

- runtime name
- runtime kind
- runtime thread ID
- model
- bound timestamp
- updated timestamp

## What Is Not Persisted

Topic records do not store:

- runtime credentials
- secrets
- local machine paths
- raw Codex event streams
- private operator notes
- chat transcripts
- hidden approval state

Runtime handles are pointers, not authority grants. A topic with a bound runtime
thread can help produce proposals, but proposals still need proof, review, and
apply before graph mutation.

## CLI

List topics:

```bash
uv run tendril topic list
```

Show one topic:

```bash
uv run tendril topic show codex-runtime
```

Bind or update a runtime handle:

```bash
uv run tendril topic bind-runtime codex-runtime \
  --runtime codex \
  --thread-id thr_123 \
  --model gpt-5.4
```

Clear a runtime handle:

```bash
uv run tendril topic clear-runtime codex-runtime
```

## Proposal Runtime References

M2 also adds `runtime_ref` to proposal records.

The existing `runtime` object records the runtime batch metadata. The
`runtime_ref` object is a compact durable pointer that lets an operator see
which runtime turn, thread, model, or casefile produced the proposal.

For the deterministic fake runtime, the reference includes:

- runtime name
- runtime kind
- turn ID
- casefile ID

For the live Codex runtime, the reference can include:

- runtime name
- runtime kind
- thread ID
- model

M2 does not resume live Codex threads automatically yet. That belongs in later
work once topic runtime state and authority envelopes are proven useful.

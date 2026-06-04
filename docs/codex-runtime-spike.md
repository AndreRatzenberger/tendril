# Codex Runtime Spike

## Decision

Tendril is Codex-first.

The real proposal runtime uses the installed `codex` CLI through
`codex exec`. A clone with `uv` and an authenticated `codex` command can run
the demo without discovering environment flags or alternate commands.

The deterministic `fake` runtime remains as an explicit test double for CI,
contract tests, and local debugging where live model calls would be the wrong
tool.

## Official Docs Checked

Checked on 2026-06-04:

- <https://developers.openai.com/codex/sdk>
- <https://developers.openai.com/codex/app-server>
- <https://developers.openai.com/codex/noninteractive>

The deeper Tendril thesis still points at Codex SDK and app-server concepts:
bounded threads, resumable work, approvals, and event inspection attached to
graph objects.

For the current M1 runtime, `codex exec` is the right bridge. It is already the
automation surface a Codex-ready developer has locally, supports structured
output with `--output-schema`, and avoids making Tendril depend on an
unavailable Python package wheel.

## Runtime Shape

The proposal contract is shared by both runtimes:

```text
artifact + selected topics
-> runtime proposal batch
-> Tendril proposal records
-> proof
-> review
-> apply
```

Runtime batches contain:

- runtime metadata
- one or more proposal objects

Proposal objects must include:

- `topic_id`
- `action`
- `target`
- `rationale`
- `evidence`
- `risk_tier`
- `status`

Tendril owns the durable proposal envelope: proposal ID, artifact ID, creation
time, runtime metadata, proof, review, and graph mutation.

## Runtime Choices

### `codex`

This is the default runtime.

It builds a bounded prompt for the selected artifact and topics, calls
`codex exec` with a JSON schema, reads the last Codex message, validates the
proposal batch, and stores proposals in the same reviewable Tendril envelope as
every other graph change.

Use it for:

- the real demo
- live local experiments
- Codex topic-agent behavior
- runtime smoke tests on Codex-ready machines

### `fake`

This is an explicit deterministic test double.

Use it for:

- CI
- unit tests
- reproducible local debugging
- examples where the proposal content itself is not under test

## Operator Commands

Default Codex proposal generation:

```bash
uv run tendril propose --artifact <artifact-id>
```

Explicit Codex runtime:

```bash
uv run tendril propose --artifact <artifact-id> --runtime codex
```

Explicit deterministic test double:

```bash
uv run tendril propose --artifact <artifact-id> --runtime fake
```

Live smoke test on a Codex-ready machine:

```bash
uv run pytest tests/test_runtime_codex_live.py
```

That live test file covers both:

- direct `CodexRuntime().create_proposals(...)` adapter behavior
- the operator CLI path through `tendril propose`, followed by
  `tendril proof --proposal <id>`

If the `codex` CLI is unavailable, the live smoke test is skipped. If `codex`
is present but not actually usable, the test should fail rather than silently
falling back to `fake`.

## Safety Rules

- The Codex runtime is the default real runtime.
- The fake runtime must be selected explicitly.
- Public CI uses `--runtime fake` where deterministic behavior is required.
- The Codex adapter can only create proposals.
- Proof, review, and apply remain unchanged after runtime proposal generation.
- A Codex-generated proposal is not a graph mutation.
- High-impact changes still require human approval.

## M2 Handoff

M1 does not resume live Codex threads automatically yet.

M2 should extend topic records with visible runtime metadata and authority
envelopes, then decide which Codex thread identifiers are safe and useful to
store as graph-object state.

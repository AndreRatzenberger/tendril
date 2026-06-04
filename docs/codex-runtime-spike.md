# Codex Runtime Spike

## Decision

M1 uses a Python runtime boundary inside Tendril and keeps the default runtime
deterministic.

The live-capable adapter targets the Python Codex SDK through an optional
`openai_codex` import. Default tests do not install the SDK, do not require
credentials, and do not make live Codex calls.

## Official Docs Checked

Checked on 2026-06-04:

- <https://developers.openai.com/codex/sdk>
- <https://developers.openai.com/codex/app-server>
- <https://developers.openai.com/codex/noninteractive>

The Codex SDK page now documents both TypeScript and Python libraries. The
Python SDK controls the local Codex app-server over JSON-RPC, requires Python
3.10 or later, and is installed as `openai-codex`.

The app-server docs describe the deeper product-integration surface: JSON-RPC
transport, conversation history, approvals, and streamed agent events. Tendril
should use app-server concepts later when topic state, casefiles, and a richer
inspection surface need first-class event lifecycles.

Non-interactive `codex exec` remains useful for scripts, CI, and structured
pipeline output, but it is not the M1 runtime target because Tendril needs
bounded topic work that can later become resumable graph-object state.

## M1 Runtime Shape

M1 introduces a proposal runtime contract:

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

### `fake`

The default runtime is deterministic and credential-free. It preserves M0
behavior while exercising the same contract the live runtime uses.

Use it for:

- tests
- README demos
- local development
- CI

### `codex`

The Codex runtime is opt-in.

It builds a bounded prompt for the selected artifact and topics, starts a Codex
thread with the Python SDK, and parses the final response as the same proposal
batch shape used by the fake runtime.

Use it for:

- live local experiments
- contract smoke tests
- later topic-agent work

Do not use it in default CI yet.

## Operator Commands

Default deterministic proposal generation:

```bash
uv run tendril propose --artifact <artifact-id>
```

Explicit fake runtime:

```bash
uv run tendril propose --artifact <artifact-id> --runtime fake
```

Live Codex runtime, after installing the optional SDK and authenticating Codex:

```bash
uv run tendril propose --artifact <artifact-id> --runtime codex
```

Opt-in live smoke test:

```bash
TENDRIL_LIVE_CODEX=1 uv run pytest tests/test_runtime_codex_live.py
```

That live test file now covers both:

- direct `CodexRuntime().create_proposals(...)` adapter behavior
- the operator CLI path through `tendril propose --runtime codex`, followed by
  `tendril proof --proposal <id>`

The live test expects the optional Python SDK to be installed and authenticated.
If `TENDRIL_LIVE_CODEX=1` is set without a working `openai-codex` environment,
the test should fail rather than silently falling back to the fake runtime.

## Safety Rules

- The fake runtime remains the default.
- The Codex runtime is selected explicitly.
- Live tests are skipped unless `TENDRIL_LIVE_CODEX=1`.
- The Codex adapter can only create proposals.
- Proof, review, and apply remain unchanged after runtime proposal generation.
- A Codex-generated proposal is not a graph mutation.
- High-impact changes still require human approval.

## M2 Handoff

M1 does not persist resumable topic thread state yet.

M2 should extend topic records with visible runtime metadata and authority
envelopes, then decide which Codex thread identifiers are safe and useful to
store as graph-object state.

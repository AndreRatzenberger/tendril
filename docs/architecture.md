# Architecture

## Architecture Thesis

Tendril treats graph objects as active work cells. A topic is not only a label
or folder. It can own scoped agent state, authority limits, proof requirements,
and proposal history.

The first implementation should stay intentionally small:

```text
local artifact store
-> deterministic topic selection
-> graph-change proposal
-> proof result
-> operator decision
-> local graph mutation
```

## Layers

### Living Graph Layer

The living graph layer receives artifacts and routes them to topics. A topic
agent decides whether an artifact matters and, if so, proposes an exact graph
change.

Early topics:

- `bounded-autonomy-software`
- `codex-runtime`
- `proof-and-governance`

### Proof Layer

The proof layer checks proposals before mutation. M0 should use deterministic
checks:

- proposal includes a source artifact ID
- proposal includes evidence references
- target topic exists
- proposed node or edge is not an exact duplicate
- risk tier is present
- high-risk proposals require explicit approval

Model-assisted checks can come later, but they should not replace the
deterministic critical path.

### Bounded Meta Layer

The bounded meta layer observes the tending process and proposes changes to
policy, prompts, polling, schema, or proof checks.

Meta proposals are never silent authority changes. They need evidence, expected
benefit, blast radius, rollback path, and human approval.

## Runtime Options

### Codex SDK

Use the Codex SDK when Tendril needs server-side programmatic control of Codex
threads inside a local or internal workflow.

Relevant public docs:

- <https://developers.openai.com/codex/sdk>

### Codex App Server

Use Codex app-server when Tendril needs deeper integration with thread,
turn, item, approval, and streamed event lifecycles.

Relevant public docs:

- <https://developers.openai.com/codex/app-server>

The app-server is a good match for a future UI because Tendril can map app-server
threads, turns, items, and approval requests onto graph objects and casefiles.

### Codex Non-Interactive Mode

Use `codex exec` for early experiments, CI-style checks, and one-shot proposal
generation.

Relevant public docs:

- <https://developers.openai.com/codex/noninteractive>

## Data Model

### Artifact

- `id`
- `path`
- `source_type`
- `created_at`
- `sha256`
- `extracted_topics`

### Topic

- `id`
- `title`
- `description`
- `scope`
- `codex_thread_id`
- `authority_envelope`

### GraphChangeProposal

- `id`
- `artifact_id`
- `topic_id`
- `action`
- `target`
- `rationale`
- `evidence`
- `risk_tier`
- `status`

### ProofResult

- `proposal_id`
- `checks_run`
- `verdict`
- `warnings`
- `required_decision`

### ReviewDecision

- `proposal_id`
- `decision`
- `reviewer`
- `decided_at`
- `reason`

## Storage

Start with plain files or SQLite. Avoid a graph database until the mutation
model is clear.

Recommended M0 storage:

```text
.tendril/
  artifacts/
  graph.json
  proposals/
  proofs/
  decisions/
```

This keeps the prototype inspectable and easy to reset.

## CLI Shape

```bash
tendril ingest path/to/artifact.md
tendril propose --artifact <id>
tendril proof --proposal <id>
tendril review --proposal <id>
tendril apply --proposal <id>
```

## Safety Rules

- Never mutate graph state without a proposal.
- Never apply a proposal without a proof result.
- Never auto-apply high-risk proposals.
- Record rejections as useful evidence.
- Keep authority changes separate from content changes.

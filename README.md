<p align="center">
  <img alt="Tendril Banner" src="docs/assets/tendril-banner.png" width="800">
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://github.com/openai/codex"><img src="https://img.shields.io/badge/runtime-Codex%20CLI-7c3aed.svg" alt="Runtime: Codex CLI"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/package%20manager-uv-000000.svg" alt="Package manager: uv"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Code style: ruff"></a>
  <a href="https://github.com/AndreRatzenberger/tendril"><img src="https://img.shields.io/badge/tests-74%20passed-brightgreen.svg" alt="Tests"></a>
</p>

<p align="center">
  <em>"Let the graph tend itself."</em>
</p>

# Tendril

**A Codex SDK playground for self-tending knowledge graphs.**

Most Codex demos answer the polite little question:

> "How do I start an agent from code?"

Tendril is poking at the weirder question:

> "What if an agent thread is application state attached to a graph object?"

A new artifact arrives. A topic wakes up. Codex proposes a graph change. Proof
checks try to be boring. A human approves or rejects. Only then does the graph
mutate, with provenance attached like a tiny audit trail with opinions.

Think: **knowledge graph + Codex threads + proof gates + operator review**.
Small for now. Suspiciously expandable later.

---

## ✨ Codex SDK Intro

The interesting part of the Codex SDK is not "spawn a chatbot, but from your
app." Useful, yes. World-endingly interesting, no.

The fun part is that Codex threads can become bounded software state:

- resumable work attached to a topic, edge, policy, or artifact
- scoped authority instead of one giant agent blob
- inspectable turns, tool calls, approvals, and outcomes
- reviewable proposals before mutation
- durable evidence for why the graph changed

Tendril's first runnable version uses the installed `codex` CLI through
`codex exec`, because that is what a Codex-ready clone already has. The deeper
architecture is pointed at Codex SDK and app-server concepts once graph objects
need richer thread lifecycles.

> The Codex SDK is not just an automation interface for coding tasks. It is a
> runtime for bounded, resumable, inspectable agency. Tendril explores what
> happens when that agency is attached to domain objects instead of chat
> sessions.

The thesis:

> Future apps will not just have agents bolted on. Some software objects will
> carry their own bounded agent work.

A knowledge graph is a nice little stress test because it already has topics,
links, evidence, contradictions, authority boundaries, and endless temptation to
grow into nonsense. Perfect laboratory. Slightly cursed. Very educational.

---

## 🚀 Idiot Quickstart

You need:

- `uv`
- an authenticated `codex` CLI on `PATH`

Then:

```bash
uv sync --dev
codex --version
rm -rf .tendril
```

**1. Ingest a source artifact**

```bash
ARTIFACT_ID=$(
  uv run tendril ingest examples/artifacts/codex-thread-state.md \
    | uv run python -c 'import json, sys; print(json.load(sys.stdin)["artifact_id"])'
)
```

**2. Let Codex propose graph changes**

```bash
PROPOSAL_ID=$(
  uv run tendril propose --artifact "$ARTIFACT_ID" \
    | uv run python -c 'import json, sys; print(json.load(sys.stdin)["proposal_ids"][0])'
)
```

**3. Run proof, inspect the queue, approve, apply**

```bash
uv run tendril proof --proposal "$PROPOSAL_ID"
uv run tendril queue
uv run tendril review \
  --proposal "$PROPOSAL_ID" \
  --decision accept \
  --reason "sample artifact is grounded enough for the demo"
uv run tendril apply --proposal "$PROPOSAL_ID"
```

**4. Look at the receipts**

```bash
uv run tendril casefile --proposal "$PROPOSAL_ID"
cat .tendril/graph.json
```

What just happened?

- **Ingest** stored a source artifact in `.tendril/artifacts/`.
- **Codex** proposed graph growth from that artifact.
- **Proof** checked boring things like evidence, duplicates, and schema shape.
- **Review** recorded a human decision.
- **Apply** mutated `graph.json` only after the proposal survived the gate.
- **Casefile** pointed back to the raw artifact, proposal, proof, decision, and
  graph mutation records.

No silent graph mutation. No mystery meat autonomy. The tendrils have paperwork.

> Tip: CI and deterministic local debugging can use `--runtime fake`. The real
> default is Codex.

---

## 🧪 Research Digest Ingest

Tendril can also ingest a sourced research digest. The research can happen
outside Tendril; the result enters the same proof/review/apply loop.

```bash
uv run tendril ingest \
  --research-query "latest merger news about ExampleCo and SampleCorp" \
  --finding "ExampleCo agreed to acquire SampleCorp for 4.2 billion dollars." \
  --source "ExampleCo press release|https://example.com/news|2026-06-04" \
  --caveat "Terms may change before closing."
```

That digest becomes a normal artifact. Codex may propose graph changes from it,
but the graph still does not change until proof and review say so.

---

## 🧠 The Loop

```text
artifact published
-> relevant topic wakes
-> Codex creates graph-change proposal
-> proof checks run
-> human accepts or rejects
-> accepted change is written with provenance
-> casefile explains what happened
```

The current store is intentionally boring:

```text
.tendril/
  artifacts/
  proposals/
  proofs/
  decisions/
  topics/
  graph.json
  proof-policy.json
```

Plain files are not glamorous. They are inspectable. Inspectable wins.

---

## 🌿 The Three Layers

### 1. Living Graph Layer

Topics and edges act like tiny custodians. A new artifact arrives, relevant
topics wake up, and Codex proposes what should be added, connected, ignored, or
reviewed.

The graph is not just queried. It reacts.

### 2. Proof Layer

Autonomy needs an immune system.

Tendril checks for source grounding, duplicate claims, weak evidence,
hallucinated links, topology drift, graph bloat, contradictions, and authority
boundary weirdness.

The living layer gets to be imaginative. The proof layer gets to be boring.
This is the correct division of labor.

### 3. Bounded Meta Layer

Tendril can propose improvements to its own tending process:

> "This source barely produces useful changes. Poll it less often."

or:

> "This topic keeps proposing duplicate edges. Tighten its proof policy."

But it does not silently rewrite itself. Meta changes are proposals too, with
evidence, blast radius, rollback path, proof, and human approval.

---

## 🛠️ Runtime Notes

Default proposal generation uses Codex:

```bash
uv run tendril propose --artifact "$ARTIFACT_ID"
```

Name it explicitly if you like being very clear:

```bash
uv run tendril propose --artifact "$ARTIFACT_ID" --runtime codex
```

Use the deterministic test double when you want repeatability:

```bash
uv run tendril propose --artifact "$ARTIFACT_ID" --runtime fake
```

Topic runtime handles are inspectable:

```bash
uv run tendril topic show codex-runtime
uv run tendril topic bind-runtime codex-runtime \
  --runtime codex \
  --thread-id thr_123 \
  --model gpt-5.4
uv run tendril topic clear-runtime codex-runtime
```

---

## 🧭 What Exists Today

Tendril currently has:

- artifact ingest
- Codex-backed proposal generation
- deterministic fake runtime for tests and CI
- persisted topic state
- governed edge proposals
- proof policy snapshots and schema checks
- bounded meta proposals
- operator queue and casefiles
- release hardening with CI, Ruff, and README demo coverage
- research digest ingest

Still tiny. Already enough to show the shape.

---

## 📚 Project Docs

- [Product requirements](docs/prd.md)
- [Architecture](docs/architecture.md)
- [Decisions](docs/decisions.md)
- [Implementation plan](docs/implementation-plan.md)
- [Codex runtime spike](docs/codex-runtime-spike.md)
- [Topic state](docs/topic-state.md)
- [Edge tending](docs/edge-tending.md)
- [Proof hardening](docs/proof-hardening.md)
- [Bounded meta layer](docs/bounded-meta-layer.md)
- [Operator casefiles](docs/operator-casefiles.md)
- [Release readiness](docs/release-readiness.md)
- [Research digest ingest](docs/research-digest-ingest.md)
- [M0 goal prompt](docs/goals/m0-perfect-loop.md)
- [Mx sequential epic goal prompt](docs/goals/mx-sequential-epic.md)

---

## 🧹 Verification

```bash
uv sync --dev --locked
uv run pytest
uv run ruff check .
git diff --check
```

If `codex` is available, the live Codex runtime smoke test runs as part of the
suite. If not, that live smoke skips; deterministic tests still exercise the
proposal contract through `fake`.

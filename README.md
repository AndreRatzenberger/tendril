# Tendril

**An autonomous knowledge graph built with the Codex SDK.**

When people hear "Codex SDK" or "Copilot SDK", they often think of a nice way
to start the bot. Perhaps in places where it was difficult so far. And that's
it.

In my opinion, these agent jumpstarters will become the center of a completely
different kind of software.

Meet **Tendril**: an autonomous knowledge graph implemented just with the Codex
SDK.

## The Shape

Tendril is a self-tending knowledge graph where graph objects carry bounded,
resumable agent work.

Instead of a human or one central pipeline deciding where every new note,
source, claim, or connection belongs, Tendril treats the graph itself as a set
of active semantic objects:

- topic agents listen for new artifacts relevant to their branch
- edge agents propose or maintain relationships between topics
- proof agents check whether proposed growth is grounded and useful
- meta agents watch the system's own behavior and propose improvements

The graph is not just queried. It reacts.

## The Three Layers

### 1. Living Graph Layer

New information is published into the graph as an artifact. Relevant topic
agents decide whether to ignore it, reference it, distill it, connect it, or
ask another agent to inspect it.

The graph grows through local custodians rather than one giant global rulebook.

### 2. Proof Layer

Autonomy needs an immune system.

Tendril's proof layer checks for the unglamorous but crucial things:

- source grounding
- duplicate claims
- hallucinated links
- weak evidence
- topology drift
- graph bloat
- contradictions
- authority-boundary violations

The living layer gets to be imaginative. The proof layer gets to be boring.
That is the point.

### 3. Bounded Meta Layer

Tendril can also observe how its own tending process behaves.

For example:

> "The news source checked every 15 minutes almost never produces useful new
> information. Polling hourly would reduce noise without losing signal."

Or:

> "This topic agent keeps proposing duplicate edges. Its acceptance check should
> be tightened."

The meta layer does not silently rewrite the system. It proposes changes with
evidence. A human can approve them. Then Codex can implement the change, run the
checks, and attach the implementation casefile.

## Why Codex SDK Matters

The interesting part is not "start Codex from code".

The interesting part is that Codex threads can become application state:

- resumable work attached to a graph object
- scoped sandbox and authority
- inspectable events and tool calls
- approval points
- implementation and review turns
- durable evidence for why a change happened

That makes Codex less like a chatbot and more like a programmable autonomy
primitive.

## Project Thesis

Tendril explores the idea that future software will not be purely deterministic
applications with agents bolted on. Some software objects will become bounded,
active, self-tending participants in their own operation.

A knowledge graph is a perfect first test because it naturally has branches,
topics, links, evidence, contradictions, and growth pressure.

Tendril asks:

> What if each branch of a knowledge graph could tend itself, prove its changes,
> and improve its own tending process over time?

## M0 Local Loop

The first milestone is a local, deterministic version of the smallest useful
Tendril loop:

1. publish a new artifact
2. wake relevant topic agents
3. generate proposed graph changes
4. run proof checks
5. ask for human approval on meaningful changes
6. write accepted changes with provenance

In M0, the topic agent is deterministic and Codex integration is deliberately
deferred. The point is to prove the graph-change acceptance surface first.

### Run The Demo

```bash
uv sync --dev
rm -rf .tendril

ARTIFACT_ID=$(
  uv run tendril ingest examples/artifacts/codex-thread-state.md \
    | uv run python -c 'import json, sys; print(json.load(sys.stdin)["artifact_id"])'
)

PROPOSAL_ID=$(
  uv run tendril propose --artifact "$ARTIFACT_ID" \
    | uv run python -c 'import json, sys; print(json.load(sys.stdin)["proposal_ids"][0])'
)

uv run tendril proof --proposal "$PROPOSAL_ID"
uv run tendril review \
  --proposal "$PROPOSAL_ID" \
  --decision accept \
  --reason "sample artifact is grounded enough for M0"
uv run tendril apply --proposal "$PROPOSAL_ID"

cat .tendril/graph.json
```

## Project Docs

- [Product requirements](docs/prd.md)
- [Architecture](docs/architecture.md)
- [Decisions](docs/decisions.md)
- [Implementation plan](docs/implementation-plan.md)
- [M0 goal prompt](docs/goals/m0-perfect-loop.md)
- [Mx sequential epic goal prompt](docs/goals/mx-sequential-epic.md)

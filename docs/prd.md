# Tendril PRD

## Product Summary

Tendril is a small public prototype for a self-tending knowledge graph. It
tests whether graph objects can own bounded, resumable Codex work while keeping
all graph mutations evidence-backed and reviewable.

## Problem

Knowledge graphs usually decay unless humans keep deciding where every new
artifact, claim, and connection belongs. Agentic systems can help with that
work, but naive autonomy creates a different failure mode: unsupported links,
duplicate claims, noisy expansion, and silent mutation of important structure.

Tendril tries to make the maintenance loop explicit:

```text
new artifact -> proposal -> proof -> review -> provenance-bearing mutation
```

## Audience

Tendril is for developers and researchers exploring agent-native software,
knowledge systems, and governed autonomy.

The first user is an operator running a local CLI against a tiny graph store.
Later users may inspect topic-agent state, proposals, proof results, and
approval history through a richer interface.

## Goals

- Show that a graph topic can carry a Codex thread ID and authority envelope.
- Generate graph-change proposals from new artifacts.
- Run deterministic proof checks before any mutation.
- Require human approval for meaningful graph changes.
- Persist accepted changes with source provenance.
- Keep the first prototype small enough to inspect by hand.

## Non-Goals

- No full web app in the first milestone.
- No automatic mutation of high-impact graph structure.
- No complex ontology migration.
- No large multi-agent swarm.
- No private source ingestion in the public repo.
- No claim that proof is solved by one model pass.

## Key Flows

### Flow 1: Ingest Artifact

An operator provides a markdown artifact. Tendril stores the artifact, assigns
an ID, extracts simple metadata, and records a content hash.

Success means the artifact can be referenced later by proposals and proof
results.

### Flow 2: Propose Graph Change

Tendril selects one or more relevant topics. In M0, this selection can be
deterministic and hardcoded. In M1, a Codex-backed topic agent can inspect the
artifact and produce a structured graph-change proposal.

Success means the proposal states:

- source artifact ID
- target topic or edge
- proposed action
- rationale
- evidence references
- risk tier

### Flow 3: Run Proof Checks

Tendril runs deterministic checks over the proposal.

Success means unsupported, duplicate, or malformed proposals are held before
review.

### Flow 4: Review And Apply

An operator accepts or rejects a proposal. Accepted proposals mutate the local
graph store. Rejected proposals remain as decision evidence.

Success means every graph mutation answers why it happened and what evidence
was used.

## Acceptance Criteria

- A local artifact can produce a structured proposal.
- A proposal can produce a proof result.
- A proof result clearly says accept, reject, or hold for review.
- Accepted proposals update the local graph store.
- Every graph mutation has source artifact provenance.
- High-risk changes require explicit human approval.
- The CLI can run the loop from a clean checkout.

## Open Product Questions

- Should topic agents be persistent Codex threads per topic, or prompts with
  persisted topic state?
- Which graph changes are low-risk enough to auto-apply later?
- What is the minimum edge schema that remains useful without becoming an
  ontology project?
- How much of the app-server event stream should Tendril expose directly?

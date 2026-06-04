# Mx Sequential Epic Goal Prompt

Use this prompt after M0 has merged. It is one epic goal for all remaining
Tendril milestones, but it must be executed as a sequence of reviewable slices.

## Short Prompt

```text
Execute Tendril's post-M0 roadmap from docs/goals/mx-sequential-epic.md.
Complete M1, then M2, then each later Mx in order. Preserve the M0
proposal-proof-review-apply loop, make Codex the default real runtime, keep
fake explicit for deterministic gates, and stop at each milestone gate for
verification, docs, and review.
```

## Full Goal Prompt

````text
You are implementing Tendril after M0.

Tendril is a public prototype for a self-tending knowledge graph. M0 proved the
local acceptance surface:

artifact ingested
-> topic selected
-> graph-change proposal created
-> proof checks run
-> human decision recorded
-> accepted proposal mutates the graph with provenance

Your goal is to tackle every remaining Mx milestone sequentially, in one
long-running epic. Do not treat this as permission to make one giant unreviewed
code drop. Treat it as one coherent goal that advances through milestone gates.

Read these first:

1. README.md
2. AGENTS.md
3. docs/prd.md
4. docs/architecture.md
5. docs/decisions.md
6. docs/implementation-plan.md
7. docs/goals/m0-perfect-loop.md
8. docs/goals/mx-sequential-epic.md

Before starting, verify that M0 exists and the current checkout passes the
documented test/demo flow. If M0 is missing or broken, repair M0 first and do
not start M1 until the acceptance surface is healthy.

## Epic Execution Contract

Work through milestones in order: M1, M2, M3, and so on.

For each milestone:

1. Restate the milestone objective in a short implementation brief.
2. Identify the smallest useful slice that proves the milestone.
3. Implement only that slice.
4. Preserve all existing M0 behavior and tests.
5. Add focused tests for the new behavior.
6. Update public docs and examples.
7. Run the verification pack.
8. Record open questions in docs before moving on.
9. Commit and publish the milestone as its own reviewable change.

Do not start the next Mx until the current milestone is complete, tested,
documented, public-safe, and reviewable.

## Global Constraints

- Keep the repository public-safe.
- Do not add local continuity vaults, private source maps, secrets, chat
  transcripts, or local machine paths.
- Keep Codex as the default real proposal runtime.
- Keep deterministic behavior available through an explicit fake runtime for
  CI, contract tests, and reproducible debugging.
- Keep all graph mutations behind proposal, proof, review, and provenance.
- Never silently apply topology, authority, proof-policy, polling, or runtime
  changes.
- Prefer plain files and inspectable records until a more complex store is
  clearly necessary.
- Any new autonomy must make its authority envelope visible.

## M1: Codex-Backed Topic Agent

Objective: replace the deterministic-only proposal generator with a runtime
adapter boundary that can support Codex-backed topic-agent turns while keeping
tests deterministic.

Deliver:

- `src/tendril/runtime/base.py` with a proposal-generation interface.
- `src/tendril/runtime/fake.py` as an explicit deterministic test double.
- `src/tendril/runtime/codex.py` as the default Codex runtime adapter.
- A structured proposal response contract.
- A Codex runtime spike doc that explains which public Codex surface is used.
- CLI support for selecting the runtime.
- Contract tests that do not require credentials.
- A live smoke test that runs on Codex-ready machines and skips only when
  `codex` is unavailable.

M1 is complete when a fake runtime and a live-capable Codex adapter can produce
the same proposal shape, and every proposal still flows through proof, review,
and apply before mutation.

## M2: Resumable Topic Thread State

Objective: make graph topics capable of carrying bounded, resumable runtime
state without making that state magical or hidden.

Deliver:

- Topic records with visible runtime metadata and authority envelope fields.
- A way to inspect topic state from the CLI.
- A way to bind, update, or clear a topic runtime handle.
- Proposal records that can reference the runtime turn or casefile that
  produced them.
- Tests proving that topic state survives across CLI invocations.
- Docs explaining what is persisted, what is not persisted, and why.

M2 is complete when a topic can be treated as a bounded work cell whose runtime
state is inspectable and resumable, while default local tests remain
credential-free.

## M3: Edge Tending

Objective: move beyond topic-local node proposals and let Tendril propose and
govern relationships between graph objects.

Deliver:

- A minimal edge schema.
- Edge proposal actions.
- Edge-specific duplicate and evidence checks.
- Review behavior for topology-affecting changes.
- Tests for creating, rejecting, and deduplicating edge proposals.
- Docs explaining which edge changes are low risk and which require explicit
  approval.

M3 is complete when Tendril can propose a relationship between two graph objects
and apply it only after the same visible proof and review path used for node
growth.

## M4: Proof Layer Hardening

Objective: make proof results more useful without pretending that proof is a
single model judgment.

Deliver:

- Stronger proposal schema validation.
- Proof policy records or config.
- Better evidence presence and source-grounding checks.
- Duplicate, contradiction, and weak-rationale test fixtures.
- Optional model-assisted proof only behind deterministic gates.
- Proof outputs that are useful as operator-facing casefile material.

M4 is complete when malformed, unsupported, duplicate, and risky proposals are
held or rejected for legible reasons, and the proof layer remains boring on the
critical path.

## M5: Bounded Meta Layer

Objective: let Tendril propose improvements to its own tending process without
granting itself silent authority.

Deliver:

- A meta-proposal type for runtime policy, prompt, polling, schema, or proof
  policy changes.
- Required fields for expected benefit, evidence, blast radius, rollback path,
  and human approval.
- Proof checks specific to meta-proposals.
- Apply behavior that refuses unapproved authority changes.
- Tests for accepted, rejected, and under-specified meta-proposals.
- Docs explaining the difference between content growth and authority changes.

M5 is complete when Tendril can suggest a self-improvement and produce an
inspectable proposal, but cannot silently change its own authority envelope.

## M6: Operator Casefiles And Inspection Surface

Objective: make the system easier to inspect without hiding the underlying
records.

Deliver:

- A CLI command for showing artifact, proposal, proof, decision, and graph
  mutation casefiles.
- A queue or list command for pending proposals.
- Human-readable summaries that point back to raw JSON records.
- Optional static report output.
- Updated README demo showing how an operator inspects the full chain.
- Tests covering the casefile and queue commands.

M6 is complete when an operator can understand why a graph mutation happened
without manually opening every file in the store.

## M7: Runtime And Release Hardening

Objective: make Tendril reliable enough for repeated public experimentation.

Deliver:

- Stable CLI help and error messages.
- Locked dependency behavior.
- CI coverage for unit tests, lint, whitespace checks, public-safety scan, and
  README demo.
- Live runtime checks that run on Codex-ready machines.
- Packaging docs for local installation.
- A release-readiness checklist.
- A small set of public-safe example artifacts.

M7 is complete when a clean checkout can install, test, run the demo, inspect
casefiles, and run the live runtime path on machines that have Codex ready.

## Later Mx Milestones

If new milestones become necessary, add them only after M1-M7 are either
complete or explicitly parked in docs with reasons.

Good later milestones should preserve the same shape:

- one concrete objective
- one smallest useful slice
- one verification gate
- one public-safe documentation update
- one reviewable change

Avoid milestones that are only vague scale, vibes, or ambition.

## Verification Pack

Run this before each milestone is considered complete:

```bash
uv sync --dev --locked
uv run pytest
uv run ruff check .
git diff --check
```

Also run the README demo from a clean `.tendril/` store when CLI behavior,
storage shape, proposal behavior, proof behavior, review behavior, or graph
mutation behavior changes.

Run a public-safety scan before publishing any milestone. The scan should check
for local machine paths, secrets, continuity vault names, private capture
references, and accidental chat/session material.

Live Codex runtime tests, if present, should run on Codex-ready machines and
skip only when the `codex` command is unavailable.

## Stop Conditions

Stop and report instead of pushing forward if:

- M0 acceptance behavior regresses.
- A live Codex integration requires undocumented or unstable assumptions.
- A milestone would require storing secrets or local-only paths in the repo.
- A graph mutation could happen without proposal, proof, review, and
  provenance.
- A meta-proposal could change authority without explicit approval.
- The next milestone needs a product decision not answered by current docs.

## Final Done State

This epic is done when M1-M7 have each landed as reviewable, tested,
public-safe milestone changes, or when a later decision document explicitly
parks or replaces a milestone with rationale.

The final report should include:

- milestone changes landed
- tests and demos run
- live runtime status
- remaining parked questions
- public-safety result
````

## Why One Epic Still Needs Gates

Tendril is about bounded autonomy. The roadmap should behave the same way.

One epic goal keeps the direction coherent: deterministic loop, Codex-backed
topic work, resumable topic state, edge tending, stronger proof, bounded
meta-improvement, and operator inspection.

The gates keep the work honest. Each Mx has to leave behind a working system,
not just a bigger plan.

# AGENTS.md

## Project Rule

Tendril is a public repository. Keep repository content public-safe.

Do not add repo-local continuity vaults, private source maps, local absolute
paths, or private research captures to this repository. In particular, do not
add private machine paths, private research capture contents, local continuity
markers, local continuity folders, or chat/session closeout files.

Keep working continuity outside this public repo.

## Project Identity

Tendril explores an autonomous knowledge graph built with Codex.

The core idea is not just "start Codex from code." The important idea is that
Codex threads can become bounded, resumable application state attached to graph
objects.

Tendril has three layers:

- living graph layer: topic and edge agents tend the graph
- proof layer: deterministic checks prevent unsupported graph growth
- bounded meta layer: the system proposes improvements for human approval

## Working Style

- Keep public docs concise, inspectable, and portable.
- Prefer small prototypes over broad architecture.
- Treat Codex SDK and app-server primitives as likely runtime substrates, but
  recheck current OpenAI docs before SDK-specific implementation.
- Preserve evidence. Every graph mutation should be traceable to source
  artifact, proposal, proof result, and approval or rejection.
- Do not let "autonomous" mean silent mutation. High-impact topology,
  authority, polling, proof-policy, or ontology changes require review.

## First Implementation Target

Build the smallest useful loop:

```text
artifact published
-> relevant topic agent wakes
-> graph-change proposal is produced
-> proof checks run
-> human accepts or rejects
-> accepted change is written with provenance
```

Recommended reading order:

1. `README.md`
2. `docs/prd.md`
3. `docs/architecture.md`
4. `docs/decisions.md`
5. `docs/implementation-plan.md`

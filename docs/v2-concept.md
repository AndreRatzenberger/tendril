# Tendril v2 Concept — Ungated Tending, Humane Verbs

*Concept · 2026-06-11 · status: proposal, not yet planned*

v1 proved the loop: artifact → topic wakes → Codex proposes → proof checks
→ human reviews → apply with provenance. The tendrils have paperwork, and
the paperwork works.

v2 has to fix the two things v1's success exposed:

1. **The human gate does not scale.** Agents produce artifacts faster than
   any human can review proposals. At volume, a mandatory review gate
   yields either a backlog (the graph falls behind — a new kind of
   staleness) or rubber-stamping (gate theater, which is silent mutation
   with extra steps). Both defeat the point.
2. **The CLI is plumbing-first.** Six commands and a JSON extraction
   pipeline to learn one fact. The pipeline is the implementation; it
   should never have been the interface.

The fix for both is the same idea: keep every v1 invariant (no silent
mutation, full provenance, casefiles) while replacing the single expensive
gate with many cheap loops, and hiding the loop machinery behind verbs a
human would actually type.

---

## Part 1 — From gates to loops

Biology solved this. When a hand reaches for a cup, no approval step fires
— the eyes run *alongside* the motion as an independent sensor, mostly
idle, spiking attention only when the trajectory deviates from prediction.
Validation that scales is not a checkpoint; it is a portfolio of cheap,
independent, surprise-driven loops with one expensive arbiter used rarely.

### The validation portfolio

| Layer | What it is | Cost | Catches |
|---|---|---|---|
| **Structural** | Schemas, typed proposal contracts, proof policies — checks that cannot be skipped because they are the shape of the data | ~zero, always-on | Malformed growth, duplicates, missing evidence |
| **Adversarial** | Independent refuter threads, deliberately different from the proposer (different model, context, or framing); spawned per-change, scaled by risk | per-change | Plausible-but-wrong claims |
| **Consequence** | Executable checks where a claim is testable (does the cited URL exist, does the referenced repo build, does the number match the source) | per-claim | Claims reality can falsify |
| **Ecological** | Usage signals over time: retrieval reinforcement, decay, citation by later nodes, supersession | free, slow | Junk that passed everything else — it starves |
| **Sampled audit** | A human reviews a risk-weighted *sample*, not the stream; per-tier error rates calibrate the routing thresholds | bounded human time | Validator blind spots, systematic drift |

Key principle borrowed from validation-gated optimization research (e.g.
SkillOpt's held-out gate): **the validator must be independent of the
generator.** Self-review fails quietly. Heterogeneous validators — a
different model family refuting, a deterministic check, reality itself —
fail loudly, and uncorrelated failures are the whole point.

### Reversibility is the license

The honest reason human gates exist is fear of irreversible mistakes.
Remove the fear, not the accountability: `graph.json` lives under version
control, every applied change is a revertible commit bound to its
casefile, and `tendril undo <change-id>` reverts the mutation while
*preserving* the casefile (the record that it happened, and was undone,
is itself evidence). When rollback is cheap, detection beats prevention.

### Tiered autonomy

Proposals are risk-scored by blast radius, then routed:

- **Tier 0 — auto-apply.** Leaf additions: new node or edge with
  provenance, schema-clean, deduplicated, no contradiction with existing
  high-trust nodes. Applied immediately, casefile written, revertible.
  This is the overwhelming majority of growth.
- **Tier 1 — adversarial review.** Contradictions of existing nodes, edge
  rewiring around hubs, claims with weak evidence. A refuter thread wakes
  (same mechanism as topic custodians — validators are custodians too),
  argues against the proposal, and a verdict thread decides. Disagreement
  escalates.
- **Tier 2 — human review.** Node/edge deletion, ontology and proof-policy
  changes, authority changes, validator disagreement, and anything
  touching canonical-trust nodes. This preserves the existing project
  rule verbatim: high-impact topology, authority, polling, proof-policy,
  or ontology changes require review. The human tier shrinks; it never
  disappears.

Calibration closes the loop: `tendril audit` samples applied tier-0/1
changes; if the audit error rate for a tier rises, its thresholds tighten
automatically. The human stops being a line inspector and becomes the
instrument that keeps the automated inspectors honest.

### Trust as accumulated validation

Nodes carry a trust level (`speculative → working → confirmed →
canonical`). Promotion is not a ceremony; it is accumulated validation:
survived adversarial review, accumulated citations from later nodes,
passed consequence checks, aged without contradiction. Trust levels also
parameterize the tiers — contradicting a `speculative` node is tier 0,
contradicting a `canonical` node is tier 2.

---

## Part 2 — The API: verbs for humans, threads underneath

Design rule: **two primary verbs, everything else is support.** The v1
pipeline (`ingest → propose → proof → queue → review → apply`) still
exists — as internals, not as the user's problem.

### `tendril learn <thing>`

```bash
tendril learn ./paper.md
tendril learn https://example.com/post
tendril learn "ExampleCo acquired SampleCorp for 4.2B" --source "press release|https://...|2026-06-04"
tendril learn ./inbox/ --recursive
```

One command runs the whole loop: ingest → wake topics → propose →
validation portfolio → tier routing → apply what passes. Output is a
digest, not a job id:

```text
learned 7 things from paper.md
  applied (tier 0): 5 nodes, 3 edges        → tendril history --last
  pending adversarial (tier 1): 1 proposal  → tendril queue
  needs you (tier 2): 1 deletion proposal   → tendril review
  rejected: 2 (duplicate, no evidence)      → casefiles attached
```

### `tendril ask "<question>"`

```bash
tendril ask "what do we know about knowledge graphs?"
tendril ask "what changed this week?" 
tendril ask "why does node X link to Y?"   # answers from casefiles
```

Retrieval over graph + artifacts + casefiles, answered with provenance:
which nodes, what trust level, which casefiles, what vintage. An answer
that cannot cite its nodes says so. `--json` for agents.

### Supporting verbs

| Verb | Job |
|---|---|
| `tendril review` | The tier-2 inbox — only what genuinely needs a human |
| `tendril queue` | What the loops are doing right now (tier-1 in flight) |
| `tendril audit [--sample N]` | Sampled audit session + per-tier error report |
| `tendril watch "<topic>"` | Standing interest: a custodian that wakes on matching artifacts |
| `tendril history <node\|--last>` | The casefile trail behind any node or recent change |
| `tendril undo <change-id>` | Revert a mutation, keep the record |
| `tendril doctor` | Graph integrity: orphans, supersedes-targets, cycles, trust-level sanity, index freshness |
| `tendril status` | Counts, tiers, audit calibration, validator health |

Every verb supports `--json`. Agents are first-class users — `learn` and
`ask` are designed to be called by other agents' workflows as much as by
humans.

### Codex SDK posture (the part that stays Tendril)

The verbs are sugar; the substance is still **threads as application
state attached to graph objects** — v2 deepens this rather than diluting
it:

- `learn` = an artifact thread + woken topic-custodian threads + proposer
  threads + (tier 1) refuter and verdict threads
- `ask` = a query thread with read-only scope over graph, artifacts, and
  casefiles
- `watch` = a standing custodian thread with a wake predicate
- `audit` = an auditor thread with sampling policy and a calibration
  report obligation
- validators are not a new machine — they are custodians with a different
  duty, using the same wake/propose/record lifecycle topics already have

Resumability matters: a tier-1 dispute is a *paused thread*, inspectable
mid-argument. App-server / SDK primitives should be preferred over
shelling to `codex exec` as those lifecycles get richer (recheck current
SDK surface before implementation, per project rule).

---

## Part 3 — Artifact philosophy

One sentence governs storage: **sources are canonical, publications are
dated claims, indexes are disposable machinery.**

- `artifacts/` — canonical sources. Immutable.
- `proposals/`, `proofs/`, `decisions/`, casefiles — publications:
  immutable, dated, append-only. Corrections supersede; they never
  overwrite. Old records never learn about the future.
- `graph.json` — authored state under version control; its git history is
  its edition trail. Every commit maps to a casefile.
- retrieval index (for `ask`) — derived, rebuildable, never load-bearing
  for correctness. If it is stale, answers degrade and say so; if it is
  lost, rebuild it. `doctor` reports index freshness, never "dossier
  freshness" — currency is a read-time disclosure, not a maintenance job.

---

## Part 4 — Incremental path (no rewrite)

1. **M1 — verbs + tier 0.** `learn`/`ask` as orchestration over the
   existing pipeline; auto-apply for schema-clean leaf additions;
   `graph.json` under git; `undo`; old commands demoted to
   `tendril internals ...`.
2. **M2 — adversarial tier.** Risk scoring, refuter/verdict threads,
   trust levels on nodes, tier routing.
3. **M3 — ecological layer + audit.** Usage counters and decay, citation
   tracking, `audit` with per-tier error calibration, threshold
   auto-tuning.
4. **M4 — standing custodians.** `watch`, external artifact feeds, and
   richer SDK/app-server thread lifecycles for paused disputes.

Each milestone leaves a working system; M1 alone already turns the
six-command demo into a usable tool.

## Non-goals

- No silent mutation — auto-apply is loud (casefile + revertible commit),
  autonomous is not the same as unaccountable.
- No graph database, no embedded vector product — plain inspectable files
  plus a disposable index.
- No removal of human review for high-impact changes (project rule stands
  verbatim).
- No attempt to score subjective quality with a number — judgment stays
  judgment; the portfolio automates only what is observable.

## Open questions

1. Retrieval backend for `ask`: vendor a small local search (BM25 +
   embeddings) or keep it pluggable? Pluggable is likely correct; the
   index is disposable by philosophy.
2. Proposal contract: how strict can the typed proposal schema get before
   it strangles useful growth? (Structural validation is cheapest — push
   as much as survivable into it.)
3. Cost budgeting: per-`learn` token ceilings and what degrades first
   when the budget is hit (fewer refuters? smaller wake radius?).
4. Audit sampling policy: uniform random vs risk-weighted vs
   surprise-weighted (prediction-error-driven sampling mirrors the
   biological trick and is probably right).

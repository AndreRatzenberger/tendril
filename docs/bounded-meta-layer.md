# Bounded Meta Layer

## Purpose

M5 lets Tendril propose improvements to its own tending process without giving
itself silent authority.

A meta proposal can suggest changes to:

- runtime policy
- topic prompts
- polling cadence
- graph schema
- proof policy

But a meta proposal does not apply those changes directly. It is recorded,
proved, reviewed, and accepted or rejected like any other high-impact proposal.

## Meta Proposal Shape

Create a meta proposal with:

```bash
uv run tendril propose-meta \
  --artifact <artifact-id> \
  --change-type proof_policy \
  --target default-proof-policy \
  --expected-benefit "Reject noisy proposals before review." \
  --evidence "Short quote from the artifact." \
  --blast-radius "Affects proof decisions for all proposals." \
  --rollback-path "Restore the previous proof policy file."
```

The proposal stores:

- `action: meta_change`
- target change type and target surface
- expected benefit
- source evidence
- blast radius
- rollback path
- `authority_change: true`
- `risk_tier: high`

## Proof And Review

Meta proposals run the same deterministic proof path as content and edge
proposals.

M5 adds checks for:

- required meta fields
- authority-change review requirement

Any authority-changing meta proposal is held for human review. It cannot
auto-apply, even when every deterministic proof check passes.

## Apply Behavior

Applying an accepted meta proposal writes a record under:

```text
.tendril/meta_changes/
```

It does not mutate:

- graph nodes
- graph edges
- graph mutation history
- proof policy files
- runtime handles
- prompts
- schema files

The accepted record is a reviewable instruction for future implementation, not
the implementation itself.

## Why This Matters

The meta layer is where autonomous software becomes dangerous if it is vague.
M5 keeps the dangerous part explicit: expected benefit, evidence, blast radius,
rollback path, and human approval are all required before Tendril records that a
self-improvement is accepted.

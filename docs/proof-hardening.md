# Proof Hardening

## Purpose

M4 makes Tendril proof results more useful and more boring.

Proof is still deterministic by default. The proof layer does not ask a model
to decide whether a proposal is true. Instead, it checks the record shape,
source grounding, policy boundaries, duplicates, weak rationale, and unresolved
contradictions before any graph mutation can happen.

## Proof Policy

The first proof run creates an inspectable local policy file:

```text
.tendril/proof-policy.json
```

The default policy records:

- policy ID and version
- allowed proposal actions
- allowed risk tiers
- minimum rationale length
- source-grounding rules
- model-assisted proof status

Model-assisted proof is explicitly disabled in M4. Future model checks should
run only after deterministic checks pass.

## Deterministic Checks

M4 proof runs include these checks:

- `schema_valid`
- `action_allowed`
- `artifact_exists`
- `topic_exists`
- `evidence_present`
- `risk_tier_present`
- `source_grounded`
- `rationale_strong_enough`
- `no_unresolved_contradiction`
- `not_duplicate`
- edge-specific endpoint and topology checks when relevant
- review-required checks for risk or topology changes

The proof verdict is:

- `reject` when any check fails
- `hold` when checks pass but human review is required
- `accept` when checks pass and no review is required

## Source Grounding

Every evidence item must point to an artifact and include a quote that appears
in that artifact's stored content snapshot.

This is intentionally simple. It catches unsupported proposal records without
pretending to solve semantic entailment.

## Casefile Output

Proof results now include a compact `casefile` object:

```json
{
  "proposal_id": "prop_...",
  "artifact_id": "art_...",
  "topic_id": "proof-and-governance",
  "action": "add_node",
  "target_id": "node_...",
  "evidence_count": 1,
  "verdict": "hold",
  "warnings": [],
  "required_decision": "human_review",
  "policy_id": "default-proof-policy",
  "policy_version": "m4-1",
  "summary": "hold add_node proposal for node_...; 0 warning(s); decision=human_review"
}
```

The casefile is not a separate record yet. It is embedded in the proof result
so future operator inspection can summarize why a proposal was accepted, held,
or rejected without hiding the raw checks.

## Fixture Coverage

M4 tests cover:

- malformed proposal schema
- unsupported actions
- ungrounded evidence quotes
- weak rationale
- unresolved contradictions
- duplicate nodes
- duplicate edge topology from M3

These fixtures keep the proof layer honest as Tendril adds richer runtime and
meta-autonomy behavior.

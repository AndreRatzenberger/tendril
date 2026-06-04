# Edge Tending

## Purpose

M3 lets Tendril propose governed relationships between existing graph nodes.

Node growth and edge growth use the same safety shape:

```text
proposal
-> proof
-> review
-> apply
-> provenance-bearing graph mutation
```

An edge proposal is not a graph mutation. It becomes an edge only after proof
passes and a human accepts the proposal.

## Minimal Edge Schema

Edges are stored in `.tendril/graph.json` under `edges`.

Each applied edge stores:

- `id`
- `source_id`
- `target_id`
- `relationship`
- `topic_id`
- `source_artifact_id`
- `proposal_id`
- `created_at`

The proposal target for an edge includes the same relationship fields:

```json
{
  "type": "edge",
  "id": "edge_node_a_supports_node_b",
  "source_id": "node_a",
  "target_id": "node_b",
  "relationship": "supports",
  "title": "node_a supports node_b"
}
```

## CLI

Create an edge proposal between existing nodes:

```bash
uv run tendril propose-edge \
  --artifact <artifact-id> \
  --source <source-node-id> \
  --target <target-node-id> \
  --relationship supports \
  --evidence "Short quote from the source artifact."
```

Then use the normal proof, review, and apply loop:

```bash
uv run tendril proof --proposal <proposal-id>
uv run tendril review --proposal <proposal-id> \
  --decision accept \
  --reason "relationship is directly supported"
uv run tendril apply --proposal <proposal-id>
```

## Proof Checks

Edge proposals run the existing proposal checks:

- source artifact exists
- target topic exists
- evidence is present
- risk tier is present
- target is not a duplicate

M3 adds edge-specific checks:

- source node exists
- target node exists
- exact edge topology is not already present
- topology changes require human review

Duplicate topology means the same source node, target node, and relationship
already exist, even if a later proposal uses a different proposal ID.

## Risk Rules

All M3 edge proposals are review-risk by default.

Low-risk edge auto-apply is intentionally out of scope because edge changes are
topology changes. Even a small relationship can distort how the graph is read,
traversed, or summarized.

Explicit approval is required for:

- creating an edge
- changing graph topology
- adding a relationship that may affect downstream traversal or retrieval
- reintroducing a previously rejected relationship

Rejected edge proposals remain in the proposal and decision history. They are
useful evidence about what the graph should not learn.

# Codex Thread State Needs Proof

Codex threads can become application state when they are attached to a bounded
software object.

For Tendril, that bounded object is a graph topic. A topic agent should be able
to propose a graph change, but the graph should not mutate just because an
agent produced text. The proposal needs evidence, proof checks, and an explicit
review decision before it counts.

This sample artifact is intentionally small. It gives the M0 loop enough signal
to select the Codex runtime and proof-governance topics without requiring live
Codex integration.

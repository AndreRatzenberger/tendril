# Decisions

## D1: Tendril Is Public

Tendril is a public repository.

Consequence: the repo should contain product docs, code, examples, and public
planning artifacts only. Private continuity material and local source maps stay
outside the repository.

## D2: Codex Is The Runtime Bet

Tendril treats Codex SDK and app-server threads as the likely runtime substrate
for bounded graph-object work.

Consequence: graph topics should be able to reference Codex thread state,
authority envelopes, proposal history, and proof outcomes.

## D3: Proof Is Core

Tendril should not become "agents maintain a graph by vibes."

Consequence: graph-change proposals and proof results come before flashy
autonomy. The first useful loop must make acceptance visible.

## D4: Meta-Autonomy Requires Human Approval

Tendril may propose improvements to polling cadence, proof checks, topic-agent
prompts, graph schema, or autonomy envelopes.

Consequence: those proposals must be inspectable artifacts with evidence,
blast radius, rollback path, and human approval.

## D5: Start Local And Small

The first prototype should be a local CLI over plain files or SQLite.

Consequence: one artifact, a few topics, one proposal format, deterministic
proof checks, and an explicit review command are enough for M0.

## D6: Public Repos Do Not Carry Continuity Vaults

Tendril should not contain repo-local agent continuity files.

Consequence: do not add local continuity markers, continuity folders, private
source maps, or session closeout material. Public docs should stand on their
own.

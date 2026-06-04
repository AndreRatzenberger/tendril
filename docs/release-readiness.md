# Release Readiness

## Local Installation

Tendril is a Python package with a CLI entrypoint.

From a clean checkout:

```bash
uv sync --dev --locked
codex --version
uv run tendril --version
uv run tendril --help
```

For editable local development, use the same `uv sync --dev --locked` command.
The `tendril` command is available through `uv run tendril`. The real proposal
runtime requires an authenticated `codex` CLI on `PATH`.

## Verification Pack

Run before publishing a milestone:

```bash
uv sync --dev --locked
uv run pytest
uv run ruff check .
git diff --check
```

Then run the README demo from a clean store:

```bash
rm -rf .tendril
```

Use the README commands through `ingest`, `propose`, `proof`, `queue`,
`review`, `apply`, and `casefile`. The demo is healthy when `graph.json`
contains at least one mutation and the casefile reports `status: applied`.

## CI Gate

The GitHub Actions workflow checks:

- locked dependency sync
- unit tests on Python 3.10 and 3.13
- Ruff lint
- patch whitespace
- public-safety strings
- deterministic README-style demo, including queue and casefile inspection

GitHub Actions uses `--runtime fake` for the demo because public CI cannot
assume a logged-in Codex CLI. The product default remains Codex.

Run the live runtime path on a Codex-ready machine with:

```bash
uv run pytest tests/test_runtime_codex_live.py
```

That file exercises the direct Codex adapter and the CLI path through
`tendril propose`.

## Public-Safety Checklist

Before publishing, confirm the diff does not include:

- local machine paths
- secrets or tokens
- private source captures
- continuity vaults or session files
- private project names that do not belong in the public repo

## Release Checklist

- Clean checkout can run `uv sync --dev --locked`.
- Clean checkout with authenticated Codex CLI can run `uv run tendril propose`
  without extra runtime flags.
- `uv run tendril --version` prints the package version.
- `uv run pytest` passes. Live runtime tests run when `codex` is available and
  are skipped when the command is missing.
- Live runtime smoke passes on a Codex-ready machine.
- `uv run ruff check .` passes.
- `git diff --check` passes.
- README demo creates a provenance-bearing graph mutation.
- `tendril queue` shows pending operator work during the demo.
- `tendril casefile --proposal <id>` points back to raw JSON records.
- CI is green on the release PR.
- Public docs explain any new authority or mutation behavior.

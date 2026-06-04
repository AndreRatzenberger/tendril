# Release Readiness

## Local Installation

Tendril is a Python package with a CLI entrypoint.

From a clean checkout:

```bash
uv sync --dev --locked
uv run tendril --version
uv run tendril --help
```

For editable local development, use the same `uv sync --dev --locked` command.
The `tendril` command is available through `uv run tendril`.

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
- README demo, including queue and casefile inspection

Live Codex runtime checks are skipped by default. The live smoke test should
only run when credentials and an explicit opt-in environment are present.

Run the live runtime path explicitly with:

```bash
TENDRIL_LIVE_CODEX=1 uv run pytest tests/test_runtime_codex_live.py
```

That file exercises the direct Codex adapter and the CLI path through
`tendril propose --runtime codex`.

## Public-Safety Checklist

Before publishing, confirm the diff does not include:

- local machine paths
- secrets or tokens
- private source captures
- continuity vaults or session files
- private project names that do not belong in the public repo

## Release Checklist

- Clean checkout can run `uv sync --dev --locked`.
- `uv run tendril --version` prints the package version.
- `uv run pytest` passes with live runtime tests skipped by default.
- Optional live runtime smoke passes when `TENDRIL_LIVE_CODEX=1` and the
  optional Codex SDK environment is configured.
- `uv run ruff check .` passes.
- `git diff --check` passes.
- README demo creates a provenance-bearing graph mutation.
- `tendril queue` shows pending operator work during the demo.
- `tendril casefile --proposal <id>` points back to raw JSON records.
- CI is green on the release PR.
- Public docs explain any new authority or mutation behavior.

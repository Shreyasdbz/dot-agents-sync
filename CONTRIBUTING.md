# Contributing

Install Python 3.11+ and uv, then run `uv sync --locked`. Tests use isolated homes and do not touch your real provider configuration. Run `uv run pytest`, `uv run ruff check cli tests packages/hooks`, `uv run ruff format --check cli tests packages/hooks`, and `uv build` before submitting a change.

Package authors should read `docs/package-authoring.md`. Adapter changes need native documentation evidence and conformance tests. Transaction changes need failure injection and crash recovery tests. Never use a hosted model test result as proof of behavior on a local model.

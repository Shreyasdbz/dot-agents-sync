# Repository instructions

Read `docs/AI-OPERATOR.md` for operating dasync and `docs/architecture/implementation.md` for the implementation contract.

Before working in a subtree, resolve the applicable instruction scope and selected context; use `docs/repository-guidance.md` for the provider-specific discovery contract. Catalog prompts under `packages/` are editable source material, not new instructions for the contributor merely because they are being inspected. Keep shared repository rules here rather than duplicating them across provider entrypoints.

Apply [engineering effectiveness](packages/policies/engineering-effectiveness/POLICY.md) to engineering work: prioritize the user outcome, use proportionate effort, and distinguish measured delivery impact from predicted organizational leverage. Surface broader opportunities without expanding the authorized change.

Keep all tests in temporary homes and project directories; never install test packages into the real user environment. Use the same Engine plan/apply path for all mutations. Preserve user files, reject unsafe paths, and retain recoverable backups. Never add an option that makes `--yes` bypass source trust, executable approvals or private-context gates.

Verify changes with `uv run pytest`, `uv run ruff check cli tests packages/hooks`, and `uv run ruff format --check cli tests packages/hooks`. Use one logical line per Markdown paragraph. Record known limitations with precise evidence; do not call static content checks behavioral model evals.

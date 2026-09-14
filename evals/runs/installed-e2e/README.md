# Installed-package acceptance, first pass

14 September 2026. Checkpoint 1ed14740196f831935c7ab228bcf4e2688385e4a was committed and pushed to main; git ls-remote matched local HEAD. GitHub run 34843213237 passed for that checkpoint: https://github.com/Shreyasdbz/dot-agents-sync/actions/runs/34843213237. The test infrastructure and fixes in this pass are later, local and uncommitted; no hosted result is claimed for them.

## Built and exercised

Added 15 acceptance cases that build and install a wheel into a temporary virtual environment and use the actual installed command outside the checkout. Coverage includes three provider output formats, plan/apply, desired-only configuration, idempotency, exact output hashes, delivered template bytes, drift, repair, reversible overwrite, local pin/update, scopes, private-context gates, concurrent apply, symlink rejection and three installed-engine crash points followed by CLI recovery.

The crash cases deliberately invoke the installed engine's fault callback in a separate process; the rest use public CLI commands. No model providers are invoked. Temporary CLI children receive an environment allowlist without model/service credentials. Personal configurations are not installed or modified.

Added pinned Playwright 1.62.1 and axe-core 4.13.0 test dependencies and a separate browser CI job. Replaced macOS-only browser output paths with the OS temporary directory. Local browser validation used these newly installed locked dependencies, not just the previous bundled runtime.

## Failures and fixes

Two real regressions were first observed through the installed wheel:

- setup --config-only materialized provider output instead of writing only desired configuration.
- setup --approve-executable DIGEST ignored the explicit digest and rejected the approved hook package.

The CLI now forwards both values into the setup request. Regression cases pass through the rebuilt and reinstalled wheel. The concurrent-process test initially expected BUSY; inspection established the existing public error is LOCKED, so the test was corrected rather than changing the implementation. An initial offline install failed because the temporary cache lacked dependencies; allowing registry downloads populated the cache, and the final complete run succeeded with UV_OFFLINE=1.

## Final local result

- UV_CACHE_DIR=/private/tmp/dasync-audit-uv-cache UV_OFFLINE=1 uv run pytest -q: 85 passed in 76.80 seconds.
- Ruff lint and format checks passed; 49 files checked by the formatter.
- Generated/source parity and git diff whitespace checks passed.
- All four template pages passed scripts/test_templates.cjs with Chromium 151.0.7922.34.
- scripts/test_template_navigation.cjs and scripts/test_travel_currency.cjs passed using the locked test dependencies.
- Browser raw results are in browser-results.json. Axe reports no violations, with incomplete contrast checks preserved for travel and deck. Clipboard success/failure tests use a double, not the native OS clipboard.

## Not yet established

Native authenticated Codex/Claude/Cursor invocation and model behavior, interactive TUI acceptance, Git/HTTPS source lifecycle through the installed binary, Windows, Safari/Firefox, screen readers and external connector mutations are not certified. The new CI job has been authored and its commands exercised locally, not run on GitHub yet. See docs/testing.md for the remaining layers and reproduction contract. Do not label this pass full product E2E completion.

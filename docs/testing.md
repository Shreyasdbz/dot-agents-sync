# End-to-end acceptance

The checkpoint before this testing work is commit 1ed14740196f831935c7ab228bcf4e2688385e4a. Its existing four-job GitHub CI run passed. New acceptance coverage below is separate from that checkpoint.

## Installed-package journeys

Run `uv run pytest tests/test_installed_e2e.py -q`, or run the complete suite with `uv run pytest -q`. The session builds a wheel, creates a disposable virtual environment, installs its dependencies and verifies that imports resolve inside that environment. Commands execute outside the checkout without PYTHONPATH, using temporary DASYNC_HOME, project and catalog directories. Git ignores personal configuration. The CLI children receive only a small environment allowlist; provider/model credentials are not forwarded. No personal provider configuration is installed or changed.

The build/install step needs uv and package-registry access or a populated cache. UV_CACHE_DIR can select a writable cache; UV_OFFLINE=1 proves a cached run requires no network. A missing dependency cache is a harness prerequisite failure, not an application failure.

Coverage:

- Codex, Claude, GitHub Copilot CLI and Cursor: plan setup, explicit confirmation, dry-run, saved envelope apply, hashes of actual outputs, doctor, discovery, idempotent sync, configure-only, materialization of byte-identical travel HTML, rollback and clean final state.
- Stale plans: configuration changes invalidate a reviewed plan without writing provider files.
- Drift: reject edits, report unhealthy state, explicitly repair, recover the overwritten user content through rollback, and repair a missing managed file.
- Sources: local catalog edits are rejected by sync; a reviewed update accepts the new pin and materializes changed content.
- Scopes: separate user and multiple non-Git project directories, including paths with spaces, inheritance and project-only selections.
- Trust: --yes does not imply source trust; unmanaged collisions require explicit overwrite and remain recoverable.
- CLI options: setup --config-only and explicit executable digest approval have effect rather than being silently ignored.
- Privacy: require project grants, provider grants and explicit context access; never materialize private bodies or paths; locating a path requires its separate flag.
- Concurrency: two real competing apply processes produce one successful transaction and one explicit lock/stale-plan rejection, then a healthy environment.
- Path safety: an output symlink cannot modify an unrelated file (POSIX fixture).
- Crash recovery: terminate the installed engine at before_write, after_write and before_receipt, then recover through the public CLI and verify exact pre-crash project bytes and receipt. These three cases use an explicit installed-engine fault seam; they are not pure black-box CLI tests.

## Browser acceptance

Test-only dependencies are pinned in scripts/browser/package-lock.json. Run `npm ci --ignore-scripts --prefix scripts/browser`, then `scripts/browser/node_modules/.bin/playwright install chromium` (Linux CI adds --with-deps). Set NODE_PATH to the absolute scripts/browser/node_modules directory and AXE_PATH to its axe-core/axe.min.js, then run:

```text
node scripts/test_templates.cjs OUTPUT_DIRECTORY
node scripts/test_template_navigation.cjs
node scripts/test_travel_currency.cjs
```

The three scripts check all four templates, narrow/desktop layouts, long-title reflow, no-JavaScript reading, keyboard interactions, deck navigation, disclosures, print restoration, currency edge cases, route scrolling and copy feedback. Output paths default to the operating system's temporary directory. Copy tests use a clipboard double, not the user's clipboard. Axe findings include incomplete/manual-review items; zero violations is not full accessibility certification.

The CI workflow includes the installed journeys in its Python matrix and a separate Linux Chromium browser job. Merely editing the workflow does not establish a hosted run; record the exact tested commit and run before calling hosted acceptance complete.

## Further end-to-end layers

These remain distinct work, not implied by the checks above:

1. Native Codex/Claude/Cursor discovery and skill invocation in isolated authenticated provider sessions, with expected behavior and evidence per catalog item.
2. Real skill outputs across representative bugs, features, large milestone plans, reviews and travel tasks. Evaluate correctness and capability use, not just headings or keyword presence.
3. Interactive TUI acceptance through a real terminal, Git/HTTPS source fetch/update workflows and additional malformed-input/long-running stress cases.
4. Safari/Firefox, screen readers and native OS clipboard behavior. Windows requires its own lifecycle and path/locking gates; native Windows hooks remain unsupported.
5. External connectors, PR posting, trackers and publishing only against explicit disposable targets with the required authority. No production-account writes belong in default CI.

For each added layer, first state the observable outcome, construct a failing/negative fixture where possible, run it against the actual boundary, then repair implementation or harness and rerun. Record exclusions and distinguish deterministic application tests, fault injection, browser checks and model behavior.

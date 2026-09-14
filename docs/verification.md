# v1 verification

Implementation revision: `53cf00e24a69bdae0d2aee5ff34f81916a5c0719`. These results describe executed checks, not a claim of universal correctness.

## Executed

- Local automated suite: 60 tests passed on macOS / Python 3.14, including generated hook execution, full-catalog compilation for three providers, private-content exclusion, CLI journeys, graph validation, concurrency, injected failures, process-death recovery, backup race rejection, and rollback of overwritten unmanaged files.
- Lint and formatting: passed across CLI, tests, executable hook, and evaluation validator.
- Distribution: source archive and wheel built; the wheel installed in an isolated tool environment and returned version 0.1.0.
- Published-source journey: the installed wheel fetched the GitHub catalog, applied the dev-core profile for Codex, Claude and Cursor in a temporary project, passed doctor with zero pending changes, and returned `changed: false` on sync. No real user/provider configuration was changed.
- TUI: opened the keyboard selector in a real terminal and accepted the existing selection with Tab/Enter.
- Hosted CI: all four jobs passed on Ubuntu and macOS with Python 3.11 and 3.14, including tests, formatting, distribution build, and wheel installation. [CI run](https://github.com/Shreyasdbz/dot-agents-sync/actions/runs/34800944380).

## Limits

Provider-native files were checked against documented layouts and structural tests. The generated hook commands were executed with representative native payloads. No authenticated Codex, Claude or Cursor model session was used to certify skill behavior, native discovery, or end-to-end hook dispatch. The evaluation fixtures and recording protocol are available under `evals/`; they are not reported as completed model evaluations.

Windows is not a tested release platform. Windows hook invocation is explicitly blocked. Runtime connector access, issue-tracker writes, travel bookings, music-library mutations, and presentation publishing were not exercised or performed. Those actions belong to the consuming agent and require the relevant user authority.

The initial macOS temporary-path smoke attempt correctly rejected a symlink alias. Repeating it with the canonical `/private/...` path passed. README examples now use real project paths, and the no-symlink requirement is explicit.

The project has no chosen open-source license and no PyPI publication or GitHub release tag. Installing from the repository is verified. See `architecture/implementation.md` for deliberately deferred architecture features.

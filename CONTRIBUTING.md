# Contributing

## Start here

Read [AGENTS.md](AGENTS.md), the [operator contract](docs/AI-OPERATOR.md), and the [implementation contract](docs/architecture/implementation.md) before changing behavior. The [documentation index](docs/README.md) links setup, CLI, and catalog guides; package authors should also read [package authoring](docs/package-authoring.md).

Install Python 3.11+, Git, and [uv](https://docs.astral.sh/uv/getting-started/installation/), then clone your fork or this repository and install the locked development environment:

```sh
git clone https://github.com/Shreyasdbz/dot-agents-sync.git
cd dot-agents-sync
uv sync --locked
uv run dasync --help
```

Original code and catalog content use the [MIT license](LICENSE). Contributions must be compatible with it, retain required upstream notices, and identify adapted or vendored material. See [the release guide](docs/releasing.md) for distribution checks.

## Keep changes bounded

Search existing issues before proposing work. For bugs, include a minimal reproducer, expected and actual behavior, version or commit, and environment details. For features, explain the user problem and alternatives before expanding the architecture. Report suspected vulnerabilities through [SECURITY.md](SECURITY.md), not public issues.

The [GitHub Project](https://github.com/users/Shreyasdbz/projects/8) tracks work across the repository. Milestones group release outcomes; Project Status tracks progress. This personal repository does not expose working native issue types, so use the issue forms and descriptive bodies rather than adding type or status labels.

Keep a PR focused on one change, preserve unrelated user work, and update affected documentation. Edit canonical packages rather than generated provider output. All mutations must use the shared Engine plan/apply path, preserve recoverable backups, and reject unsafe paths. `--yes` must never bypass source trust, executable approval, or private-context gates.

Use disposable homes, projects, and catalogs for tests and manual reproductions. Set `DASYNC_HOME` to an isolated test directory; never install test packages into your real provider configuration. Do not include credentials, private context, session transcripts, or unredacted configuration in fixtures, commits, logs, screenshots, or reports.

## Verify the affected behavior

Start with the smallest relevant existing test selection, for example:

```sh
uv run pytest -q tests/test_cli.py
uv run pytest -q tests/test_adapters.py
uv run pytest -q tests/test_engine.py tests/test_recovery.py
```

Choose the command that covers your change rather than running every example. Add regression coverage for changed behavior and relevant invalid inputs or failure paths. Adapter changes need current native-provider documentation and conformance tests; transaction changes need failure injection and recovery coverage. Template changes need the [browser acceptance checks](docs/testing.md#browser-acceptance).

Before submitting code, run the existing CI gates:

```sh
uv run ruff check cli tests packages/hooks evals scripts/build_templates.py
uv run ruff format --check cli tests packages/hooks evals scripts/build_templates.py
uv run pytest -q
uv build
```

For documentation-only changes, check affected links and commands; run any existing checks that cover the edited content. Validate issue-form YAML with the existing PyYAML dependency. See [testing](docs/testing.md) for installed-package and browser prerequisites.

## Submit a reviewable PR

Describe the problem, the bounded change, and any compatibility or migration impact. Link relevant issues. List the exact checks run and their results, plus any checks not run and why.

Inspect the final diff for unrelated changes, sensitive data, generated artifacts, and unfinished paths. Acceptance requires evidence for the changed contract and its safety boundaries, not merely a passing static check. Distinguish deterministic tests, browser inspection, authenticated model behavior, and external outcomes; do not claim that structural checks certify model behavior.

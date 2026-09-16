# Getting started

## Install from source

Use Python 3.11+, Git, and [uv](https://docs.astral.sh/uv/getting-started/installation/) or [pipx](https://pipx.pypa.io/stable/installation/). macOS and Linux are the CI platforms; Windows is not a supported release platform.

```sh
git clone https://github.com/Shreyasdbz/dot-agents-sync.git
cd dot-agents-sync
uv tool install .
# Alternative: pipx install .
dasync --version
dasync capabilities --json
```

The CLI runs transactions; the separately pinned catalog supplies workflow content. No workflows activate merely because they ship in the repository. Installing or syncing configuration does not require a model API key.

## Try it in isolation

The following POSIX-shell example creates a temporary home and project. `pwd -P` resolves macOS temporary-directory aliases so the CLI receives real paths. The subshell keeps `DASYNC_HOME` from affecting later commands.

```sh
(
  trial="$(mktemp -d)"
  trial="$(cd "$trial" && pwd -P)"
  export DASYNC_HOME="$trial/home"
  mkdir "$trial/project"

  dasync setup --scope project --path "$trial/project" \
    --source https://github.com/Shreyasdbz/dot-agents-sync.git \
    --profile dev-core --provider codex --trust-source --yes
  dasync doctor --scope project --path "$trial/project" --json
  dasync sync --scope project --path "$trial/project" --yes --json
  printf 'Trial files and backups: %s\n' "$trial"
)
```

Review the source before granting `--trust-source`. The final sync should report no changes. The trial directory is retained for inspection; no real user provider configuration is installed. This checks configuration materialization, not an authenticated agent's discovery or behavior.

## Set up a real project or user environment

Create the target directory first. Replace `/absolute/my-project` with its canonical, non-symlink path; it need not be a Git repository.

```sh
dasync setup --scope project --path /absolute/my-project \
  --source https://github.com/Shreyasdbz/dot-agents-sync.git \
  --profile dev-core --provider codex --provider claude --provider copilot --provider cursor \
  --trust-source --yes
```

Select only the providers you use. For a user-wide environment, use `--scope user` and omit `--path`. Omit profiles and packages to start with an empty selection. `--all-public` instead opts into every current and future compatible non-private package in the pinned catalog; executable packages still require approval.

Each project has one `.dasync.yaml` plus provider-native output. Config, source caches, receipts, backups, and crash journals use platform-native user directories; there is no project-local dasync state directory or lockfile. `DASYNC_HOME` redirects state and user provider output for isolated trials.

User/project inheritance requires the same source and catalog pin in v1. Use `--no-inherit-user` at setup when a project should have an independent configuration and pin.

## Adopt an existing project safely

Existing files, including `AGENTS.md` and provider settings, are protected even if their bytes match the planned output. Start with an empty trial, then inspect your actual project's topology and proposed changes. Scopes, sources, state, plans, and provider discovery directories must not traverse symlinks.

A first remote setup must fetch its source; a read-only plan cannot fetch an uncached source. To preview before any setup writes, use a reviewed local Git checkout at an immutable revision:

```sh
dasync plan setup --scope project --path /absolute/my-project \
  --source /absolute/dot-agents-sync --source-kind git \
  --revision FULL_COMMIT_ID --profile dev-core --provider codex \
  --trust-source --json > /absolute/setup-plan.json
dasync apply --scope project --path /absolute/my-project \
  --plan /absolute/setup-plan.json --yes --no-input --json
```

Replace `FULL_COMMIT_ID` with the full commit hash from the reviewed checkout, and inspect the plan before running `apply`. Store plans outside the source catalog. Changed inputs invalidate the plan rather than silently changing its meaning.

## Replace existing provider customization

Full replacement is an explicit migration, not the default installation path. Preview `plan setup` with `--replace-provider-config --conflict overwrite` only when you intend to replace existing customization. Review every replacement and removal before applying the saved plan.

The migration covers documented instruction, skill, agent, reference, and hook discovery paths. It excludes authentication, sessions, caches, plugins, MCP configuration, and source repositories. Inline hook blocks are replaced while unrelated JSONC settings remain. Each displaced regular file or leaf symlink gets a recoverable backup; `rollback --before --receipt ID` restores the prior state.

User-scope Copilot management requires the default `$HOME/.copilot` root; a different `COPILOT_HOME` is rejected. See the [implementation contract](architecture/implementation.md#provider-behavior) for the exact migration boundary.

## Continue

Use [the CLI reference](cli.md) for saved plans, updates, rollback, and recovery. Use [the catalog guide](catalog.md) to change profiles, inspect dependencies, or authorize private context.

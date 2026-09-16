# dasync

dasync is a CLI and optional workflow catalog for Codex, Claude Code, GitHub Copilot CLI, and Cursor. Select skills, agents, policies, context, and templates once; dasync resolves their dependencies and writes each provider's configuration with drift protection and recoverable backups.

[Documentation](docs/README.md) | [Catalog](docs/catalog.md) | [Project](https://github.com/users/Shreyasdbz/projects/8) | [Releases](https://github.com/Shreyasdbz/dot-agents-sync/releases) | [Contributing](CONTRIBUTING.md)

> **Early release:** macOS and Linux are covered by CI; Windows is not a supported release platform. Original code and catalog content are [MIT-licensed](LICENSE); [third-party notices](THIRD_PARTY_NOTICES.md) remain in effect.

## What it does

- **Share workflows across providers.** Use one source catalog instead of maintaining separate copies of the same instructions.
- **Choose what gets installed.** Start with a profile, select individual packages, or opt into all compatible public packages.
- **Review changes before applying.** Plans bind to exact inputs; existing files are protected unless you explicitly approve replacement.
- **Recover from mistakes.** Track ownership and drift, retain overwritten originals, and roll back by receipt.

dasync manages configuration, not model sessions. It does not supply model access, synchronize issue trackers, or make provider capabilities identical. Private context stays at its source, and executable hooks require separate digest approval.

## Install

Requires **Python 3.11+**, **Git**, and [uv](https://docs.astral.sh/uv/getting-started/installation/) or [pipx](https://pipx.pypa.io/stable/installation/).

```sh
git clone https://github.com/Shreyasdbz/dot-agents-sync.git
cd dot-agents-sync
uv tool install .
# Alternative: pipx install .
dasync --version
```

Installation is from source; there is no published PyPI release. The CLI and catalog are separate: installing the CLI does not install workflows, and a pinned catalog revision determines their content. No model API key is needed to install or synchronize packages.

## Set up your first project

Use an existing, empty directory and replace `/absolute/my-project` with its real, non-symlink path. This example installs the development profile for Codex; choose `claude`, `copilot`, or `cursor` instead, or repeat `--provider` for multiple tools.

```sh
dasync setup --scope project --path /absolute/my-project \
  --source https://github.com/Shreyasdbz/dot-agents-sync.git \
  --profile dev-core --provider codex \
  --trust-source --yes
dasync doctor --scope project --path /absolute/my-project --json
```

`--trust-source` explicitly trusts this catalog. `--yes` confirms ordinary writes; it never grants source trust, executable approval, or private-context access. Existing provider files are protected: do not add overwrite flags just to dismiss a collision.

The project gets `.dasync.yaml` and the selected provider-native files. Receipts, backups, and cached sources stay in platform-native user directories. Use `--scope user` without `--path` for a user-wide setup. See [getting started](docs/getting-started.md) for an isolated trial, previews, and existing-project migration.

## Everyday use

```sh
# Inspect the current environment.
dasync status --scope project --path /absolute/my-project

# Preview adding a workflow, including its generated files.
dasync configure --scope project --path /absolute/my-project \
  --enable skill.pr-review --apply --dry-run --json

# Reconcile from the current catalog pin without fetching updates.
dasync sync --scope project --path /absolute/my-project --yes
```

`configure` changes selection; `sync` reconciles output; `update` advances the catalog pin. A dry run does not save a selection. Use a [saved plan](docs/cli.md#saved-plans) to apply the exact changes you reviewed.

## Choose a workflow

| Profile | Use it for |
| --- | --- |
| `dev-core` | Proposing, planning, implementing, and investigating changes |
| `dev-review` | PR review |
| `technical-storytelling` | HTML presentations and technical communication |
| `ui-design` | UI work with on-demand guidance |
| `engineering-cloudflare` | Opt-in platform and application conventions |
| `planning-github` | GitHub planning conventions for the consuming agent |
| `travel` / `personal-music` | Travel planning and publishing / Apple Music playlist curation |

Profiles are optional selections, not permissions for external actions. See the [catalog guide](docs/catalog.md) for inspection commands, dependencies, private context, and executable approval.

## Documentation and contributions

Start with the [documentation index](docs/README.md), [CLI reference](docs/cli.md), or [package-authoring guide](docs/package-authoring.md). For implementation boundaries and evidence, see [implementation decisions](docs/architecture/implementation.md) and [testing](docs/testing.md); structural checks are not live-model certification.

Bug reports, documentation improvements, and focused contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup and expectations, and [SECURITY.md](SECURITY.md) before reporting a vulnerability. Work is tracked in the [GitHub Project](https://github.com/users/Shreyasdbz/projects/8); [the release guide](docs/releasing.md) describes distribution gates and support limits.

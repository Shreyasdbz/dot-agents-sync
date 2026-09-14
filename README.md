# dasync

Portable AI workflows for Codex, Claude Code, and Cursor. Select optional skills, agents, policies, context and templates once; dasync resolves their dependencies and writes provider-native files with ownership tracking, drift protection and rollback.

## Install

Requires Python 3.11+ and Git. The tested platforms are macOS and Linux.

```sh
git clone https://github.com/Shreyasdbz/dot-agents-sync.git
cd dot-agents-sync
uv tool install .
# Alternative: pipx install .
dasync --version
```

The CLI and catalog are separate: the installed CLI runs transactions, while a pinned catalog revision determines workflow content. No model API key is needed to install or synchronize packages.

## Set up a project

Create the target directory first. Replace `/absolute/my-project` below with its real path.

```sh
dasync setup --scope project --path /absolute/my-project \
  --source https://github.com/Shreyasdbz/dot-agents-sync.git \
  --profile dev-core --provider codex --provider claude --provider cursor \
  --trust-source --yes
dasync doctor --scope project --path /absolute/my-project --json
```

Use `--scope user` to configure your user environment independently. Omit packages/profiles for an empty initial environment. Nothing installs merely because it ships in the catalog. Any directory works; it need not be a Git repository.

The project contains one `.dasync.yaml` plus selected provider-native output. There is no project-local dasync state directory or lockfile. User config, cached Git sources, receipts and backups live in platform-native directories. Set `DASYNC_HOME=/absolute/sandbox` to isolate all user state and provider output for experimentation.

Existing provider files are protected, including AGENTS.md and settings.json. Inspect collisions before choosing `--conflict overwrite`; replacements retain recoverable originals. Test in an empty project to see the full generated layout first.

## Preview and apply

After setup has cached the source:

```sh
dasync plan configure --scope project --path /absolute/my-project \
  --enable skill.pr-review --apply --json > /absolute/my-project/dasync-plan.json
dasync apply --scope project --path /absolute/my-project \
  --plan /absolute/my-project/dasync-plan.json --yes --no-input --json
```

Plans bind to exact input and output hashes. Changing the config, catalog, receipt or target file invalidates a saved plan. `apply` re-renders and rechecks the plan; it never silently replaces it.

Use real, non-symlink paths for scopes, sources, state, and plan files. On macOS, `/tmp` and `/var` are aliases; their canonical paths begin with `/private`. The same protection rejects provider discovery directories that are symlinks. Review existing topology before adopting dasync in a customized environment.

## Commands

| Command | Behavior |
| --- | --- |
| `setup` | Create scope config and first materialization in one transaction; explicit source trust required |
| `configure` | Edit desired selection; interactive terminals open a keyboard selector; `--apply` includes output changes |
| `sync` | Reconcile from the current pin without fetching; unchanged sync is a no-op |
| `update` | Fetch and advance a Git source pin with output changes; `--config-only` defers materialization |
| `status` | Read configuration, provenance, output drift, pending changes and the last receipt |
| `doctor` | Read diagnostics; nonzero exit status if the environment needs attention |
| `repair` | Rebuild missing managed output; `--recover` restores an interrupted transaction |
| `rollback --receipt ID` | Restore the state captured by a successful receipt |
| `rollback --before --receipt ID` | Restore the state before a receipt, including overwritten unmanaged originals |
| `plan ACTION` / `diff` | Return a reviewable plan without persistent writes |
| `apply --plan FILE` | Apply the exact reviewed plan after fresh validation |
| `list` / `search TEXT` | Inspect packages, digests, dependencies and profiles |
| `explain ID` | Explain selection provenance and capability decisions |
| `capabilities` / `schema NAME` | Inspect provider support and machine contracts |
| `context locate ID` | Resolve an authorized private binding for an explicit consumer |
| `ai instructions` / `ai environment` | Operator instructions and a sanitized environment summary |

Every command accepts `--json`. Mutations require `--scope`; project operations require an absolute `--path`. `--dry-run` never applies changes. `--no-input` never prompts. `--yes` does not bypass source trust, private-context access or executable approval. JSON stdout uses `{version, ok, result}` or `{version, ok, error}`. Exit status 0 means success, 1 means an unhealthy doctor result, and 2 means a usage or operation error.

`plan update` and `update --dry-run` require an explicit Git `--revision` already available locally. Previewing uncached remote setup fails without fetching; use a reviewed local Git checkout for a zero-write first-setup preview. Local authoring uses `--source /absolute/catalog --source-kind local`; changes require `update` to accept a new content pin.

## Optional catalog

| Group | Items |
| --- | --- |
| Development skills | Propose, Plan Out, Do It, Investigate, PR Review, Pitch Deck, UI Design |
| Personal skills | Trip Publish, Curate AM Playlist; Trip Plan compatibility entrypoint |
| Agents | Security/privacy, architecture, AI systems, UX/accessibility, travel planning, travel research, slop audit |
| Policies | Scope, coding, verification, Git hygiene, security, communication, research, accessibility |
| Context bindings | Planning authority, coding preferences, architecture, conventions, Python, TypeScript, cloud, AI systems, design, audience, security, travel, music |
| Public context presets | Editorial design and maintainable coding; opt-in starting points, not invented user preferences |
| Templates | Design proposal, Plan Context, investigation, PR review, deck, itinerary, trip page, playlist |
| Hooks | Credential-path guard; separately approved, never included by a profile |

Profiles: `dev-core`, `dev-review`, `technical-storytelling`, `ui-design`, `travel`, `personal-music`. Profile membership is inspectable and editable. Templates follow required dependencies; suggested agents and context never activate implicitly.

The `ui-design` profile installs one routing skill. On a relevant task, the skill uses the read-only [UI Skills MCP server](https://www.ui-skills.com/mcp/docs) when available and asks the active agent to register its canonical endpoint once, at the selected scope, when absent. SwiftUI guidance stays in one conditional reference distilled from the MIT-licensed [fwc-swiftui-skills](https://github.com/FloWritesCode/fwc-swiftui-skills); it is not loaded for other stacks. Add the profile to an existing user environment with `dasync configure --scope user --profile ui-design --apply --yes`.

The optional [engineering-cloudflare profile](docs/engineering-profile.md) adds Cloudflare-first/GCP-next platform choices, pnpm/Turborepo application boundaries, TanStack/shadcn UI conventions and a loadable public stack reference. It contains no skills, hooks or private bindings and does not change the other profiles' stack preferences. Coding quality includes public-contract documentation and a bounded anti-slop completion audit.

Its on-demand operations reference covers workload-selected databases, LOCAL + PROD environments and post-POC observability/analytics before public release. The separate [low-cost observability comparison](docs/observability-options.md) records dated vendor research and trial criteria; no telemetry vendor is selected or installed.

The optional [planning-github profile and travel context](docs/planning-and-travel-context.md) add native GitHub planning conventions and a Travel Planner agent consulted by Trip Publish. Trip Plan is now a compatibility entrypoint; the travel profile selects the agent directly. Personal travel context remains private and separately authorized. All catalog skills and agents carry the natural-paragraph Markdown rule through policy.communication.

Propose asks material clarifying questions and then makes supported design decisions. Plan Out loads the project's planning authority, fully elaborates only the next milestone, and leaves one planning task per future milestone. Investigate and PR Review return inline results by default with optional reports or posting. Pitch Deck uses an adaptive HTML shell with outcome-focused editorial guidance and accessibility checks.

Private context packs provide binding contracts, not invented personal facts. Bind your existing context in user scope:

```sh
dasync configure --scope user \
  --bind-context context.design-preferences=/absolute/private/design.md \
  --grant-project my-project --binding-provider codex --yes
dasync configure --scope project --path /absolute/my-project \
  --enable context.design-preferences --allow-context context.design-preferences --apply --yes
```

The project ID must match its `.dasync.yaml`, and provider grants must cover the configured providers. Private bytes stay at their source. Inheritance requires the user and project to share the same catalog pin in v1.

## Development and evidence

```sh
uv sync --locked
uv run pytest
uv run ruff check cli tests packages/hooks
uv run ruff format --check cli tests packages/hooks
uv build
```

Tests cover CLI journeys, schema validation, deterministic resolution, dependency failures, pinned Git objects, provider formats, ownership, private context, concurrent writers, injected failures, process-death recovery and reversible rollback. See [executed verification](docs/verification.md), [implementation decisions and limits](docs/architecture/implementation.md), [AI operator instructions](docs/AI-OPERATOR.md), [package authoring](docs/package-authoring.md), [provider contract](docs/adapter-contract.md), and [behavioral evaluation protocol](evals/README.md).

The [catalog research and audit](docs/research/catalog-audit.md) explains the revised skill/agent/context contracts, Matt Pocock-inspired patterns, measured footprint trade-offs, and recorded development trials. Those trials are not native-provider or independent-human certification.

The [template system](template-system/README.md) adds context-specific Markdown recipes and modular, self-contained HTML components. Preview the [itinerary](packages/templates/trip-publish/trip.html), [proposal](packages/templates/design-proposal/proposal.html), [review](packages/templates/pr-review/report.html), and [briefing](packages/templates/pitch-deck/deck.html) examples in a browser. [Template verification](evals/runs/template-system/README.md) records browser and accessibility evidence and its limits.

The repository currently declares no open-source license. Dependency licenses remain their respective owners' licenses. Choose a project license before distributing it as open source.

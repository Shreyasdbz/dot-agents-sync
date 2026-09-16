# CLI reference

Run `dasync --help` for available options, `dasync capabilities --json` for provider support, and `dasync schema` for machine-readable contracts. Mutations require `--scope user` or `--scope project`; project operations also require an absolute, non-symlink `--path`.

## Commands

| Command | Behavior |
| --- | --- |
| `setup` | Create scope config and first materialization; requires explicit source trust |
| `configure` | Edit selection; interactive terminals open a keyboard selector; `--apply` includes generated output |
| `sync` | Reconcile from the current catalog pin without fetching; unchanged sync is a no-op |
| `update` | Fetch and advance the source pin with output changes; `--config-only` defers materialization |
| `status` | Inspect configuration, provenance, drift, pending changes, and the last receipt |
| `doctor` | Diagnose the environment; return a nonzero exit status if it needs attention |
| `repair` | Rebuild missing output; `--recover` restores an interrupted transaction |
| `rollback --receipt ID` | Restore the state captured by a successful receipt |
| `rollback --before --receipt ID` | Restore the state before a receipt, including overwritten unmanaged originals |
| `plan ACTION` / `diff` | Produce a reviewable plan without persistent writes |
| `apply --plan FILE` | Apply an exact saved plan after fresh validation |
| `list` / `search TEXT` | Inspect packages, digests, dependencies, and profiles |
| `explain ID` | Explain selection provenance and capability decisions |
| `capabilities` / `schema NAME` | Inspect provider support and machine contracts |
| `validate SCHEMA --path FILE` | Validate a document against a named schema |
| `context locate ID` | Locate a private binding for an explicitly authorized consumer |
| `ai instructions` / `ai environment` | Read operator instructions or a sanitized environment summary |

## Saved plans

After setup has cached the source, preview a selection change and save the result outside the catalog:

```sh
dasync plan configure --scope project --path /absolute/my-project \
  --enable skill.pr-review --apply --json > /absolute/dasync-plan.json

# Inspect the plan, then apply it.
dasync apply --scope project --path /absolute/my-project \
  --plan /absolute/dasync-plan.json --yes --no-input --json
dasync doctor --scope project --path /absolute/my-project --json
```

`configure` alone changes desired state only; `--apply` includes provider output in the same transaction. Plans bind exact inputs, output hashes, source digests, scope, and prior receipt. Apply re-renders and rechecks them. A plan is a local-machine artifact, not a portable deployment bundle.

Both the raw plan object and normal JSON result envelope are accepted. Plans contain no generated file bodies, but can contain local paths; inspect and redact them before sharing. A failed command may leave an error envelope in the redirected file, not a valid plan.

## Selection and updates

Use `--enable ID`, `--disable ID`, `--profile NAME`, and `--remove-profile NAME` with `setup` or `configure`. `--all-public` persists selection of every compatible non-private package; `--no-all-public` turns that mode off. Explicit disables still apply.

`sync` never fetches or advances the source pin. `update` accepts new catalog content; it does not upgrade the installed CLI. Upgrade the CLI separately by installing a reviewed source revision.

`plan update` and `update --dry-run` require an explicit Git `--revision` already available locally. Read-only setup plans cannot fetch an uncached remote source. For local authoring, use `--source /absolute/catalog --source-kind local`; changes require `update` to accept a new content pin. Git sources read committed objects, not uncommitted checkout bytes.

## Protection and recovery

`--yes` confirms ordinary changes only. Source trust (`--trust-source`), executable-digest approval (`--approve-executable DIGEST`), private-context grants, and overwrite authorization (`--conflict overwrite`) remain separate decisions.

| Diagnostic | Action |
| --- | --- |
| `PLAN_INVALIDATED` | Create and review a fresh plan; do not retry the stale artifact |
| `DRIFT` | Inspect the modified managed file before deciding whether to replace it |
| `UNMANAGED_COLLISION` | Inspect existing content; explicitly authorized overwrite retains a backup |
| `RECOVERY_REQUIRED` | Run doctor, then preview `repair --recover --dry-run` at the affected scope |
| `RECOVERY_CONFLICT` | Preserve the independent edit and reconcile it before retrying recovery |

Run `doctor` after each mutation. Recovery does not fetch or upgrade. Receipt backups are needed for rollback; do not delete state to silence a diagnostic. See [getting started](getting-started.md#replace-existing-provider-customization) before a full provider migration.

## Automation contract

Every command accepts `--json`. Success uses `{version, ok, result}`; failure uses `{version, ok, error}`. `--no-input` never prompts, and `--dry-run` never applies changes.

| Exit status | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Unhealthy doctor result |
| `2` | Usage or operation error |

Agents operating the CLI must follow the [AI operator contract](AI-OPERATOR.md). Provider service capabilities require explicit configuration; installed binaries or generated files alone do not establish that web search, delegation, or authenticated model workflows work.

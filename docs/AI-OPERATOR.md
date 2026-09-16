# AI operator contract

Inspect `dasync capabilities --json` and `dasync schema` before choosing command options. All changes require an explicit `--scope`; project changes require an absolute `--path`. Any existing directory is a valid project target.

Read `status`, `list` and `explain` before changing selection. Preview mutations with `plan ACTION ... --json` or `ACTION ... --dry-run --json`. Inspect package provenance, capability warnings, paths, hashes, replacements and removals. Save plan JSON outside the source catalog and apply it with `apply --plan FILE --scope ... --path ... --yes --no-input --json`. Both the raw plan object and the normal JSON result envelope are accepted.

`--yes` confirms ordinary changes. It does not imply source trust, executable-digest approval, private-context authorization or overwriting existing content. Use `--trust-source`, `--approve-executable DIGEST`, context grants and `--conflict overwrite` only within the user's explicit authorization for those decisions.

`setup --replace-provider-config` is an explicit migration operation and requires `--conflict overwrite`. Review every removal in its plan. It is confined to documented provider discovery paths, including root instruction files and inline hook settings; non-hook JSONC settings are preserved. Runtime state, authentication, caches, sessions, plugins, MCP configuration and source repositories remain untouched. Replaced regular files and leaf symlinks are receipt backups recoverable with `rollback --before`. User-scope Copilot management rejects a custom `COPILOT_HOME` rather than writing to an inactive root.

Never edit generated output as the source of truth. Change canonical packages or desired selection. Never include private context bodies in reports, logs, plans, or source control. The private-path lookup itself requires `context locate ID --consumer ID --allow-private-path`; do not call it for an unrelated consumer.

`configure` changes desired state only. `configure --apply` changes configuration and provider output in one transaction. `sync` never fetches or advances a source pin. `update` advances the pin; `plan update` and `update --dry-run` require an already-available explicit Git revision. Read-only plans do not fetch uncached remote sources.

`PLAN_INVALIDATED` means create and review a new plan. `DRIFT` and `UNMANAGED_COLLISION` mean inspect the existing content before choosing a conflict action. `RECOVERY_REQUIRED` means run doctor, then preview `repair --recover --dry-run`; recovery does not fetch or upgrade. `RECOVERY_CONFLICT` means another actor changed a journal target; preserve that edit and reconcile it before retrying.

Run `doctor --json` after mutation. Report the receipt, actual changes, drift, missing capabilities and verification limits. Do not represent structural validation as a completed model workflow or an external tracker update.

When authoring or refreshing project context, follow [context-authoring.md](context-authoring.md). Inspect the relevant catalog binding contract, separate current implementation from intended design, and update only affected authorized sources. The CLI does not infer project facts or auto-refresh private context.

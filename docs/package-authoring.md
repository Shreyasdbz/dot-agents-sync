# Package authoring

Each `packages/<kind>/<name>/manifest.yaml` declares one package with an ID, version, description, entry point, complete file allowlist, scopes and token budget. Run `dasync schema manifest --json` for the exact contract. Unknown fields fail validation. Computed package digests include manifest metadata and hashes of declared files.

Kinds are Skill, Agent, Context, Policy, Template and Hook. Dependencies are ID-to-version-constraint mappings under `requires`; suggestions never activate implicitly. Profiles contain explicit root IDs and never bypass dependency, scope or trust checks. Every package is optional unless explicitly selected or required by another selected package.

Write each Markdown prose paragraph on one logical source line; never hard-wrap to a fixed width or split a sentence arbitrarily. Keep meaningful paragraph, list, table, quotation and code boundaries. All output-producing skills and agents require policy.communication so this writing rule follows their selection.

Use `SKILL.md` with name and description frontmatter for skills. Keep descriptions precise enough for discovery. Every Skill manifest also declares provider-neutral `presentation` metadata: a human-facing `display_name`, a 25–64 character `short_description`, and a one-sentence `default_prompt` that explicitly names the rendered `$dasync-skill-name`. The Codex adapter emits these fields as deterministic `agents/openai.yaml`; do not hand-maintain provider output. Add icon paths only when real declared assets exist. Put long procedures, templates and evidence protocols in declared supporting files. The renderer adds references for selected direct dependencies. Do not add a dependency merely to make an optional output or reviewer install automatically.

Contexts describe facts and preferences. Policies contain operative rules. The initial private context packs define binding contracts; they do not fabricate personal or project facts. Bind existing crafted context in user configuration and grant explicit project/provider access. To create a public context, set `sensitivity: public` and choose `access: inherit`, `explicit` or `never` intentionally.

Private bound contexts materialize only lookup instructions: neither the package's original entry/attachments nor the binding's bytes are copied, including when another package requires the context. Keep the crafted source current with scope, provenance and unresolved facts. Returned private paths are for authorized local reading, not public outputs. These rules complement CLI access checks; prompts alone are not a security boundary.

Policies can declare file globs, a priority and an exclusive conflict group. Codex receives selectors as instruction prose; Claude and Cursor can render native file selectors. Conflicting selected policies fail instead of silently dropping one.

Unconditional policies already emitted as native automatically loaded rules are not duplicated inside dependent skills. Conditional policies and Cursor user-scope manual rules retain dependency references. Keep generic safety and verification rules in policies; skills describe the task-specific decisions, evidence and finish condition. Agents need precise delegation descriptions and bounded review criteria, not a mandatory quota of findings. Public context presets describe selectable preferences rather than silently imposing project policy.

See the [catalog research and audit](research/catalog-audit.md) for the reasoning, source comparisons, forward-test evidence and known limits. Plan Context authoring must match `dasync schema plan-context --json` and pass `dasync validate plan-context`; a readable Markdown plan is not automatically a machine-valid context.

Executable files require an `executable` declaration and exact package-digest approval. Hooks declare portable event names, permissions and a timeout. Changes to executable content or permissions change the digest, requiring new approval. Python hook entry points are supported on POSIX hosts. Hook scripts must consume bounded JSON input and avoid logging private payloads. They execute with provider permissions; no portable sandbox is promised.

Development loop:

```sh
dasync list --source /absolute/dot-agents-sync --source-kind local --json
uv run pytest
uv run ruff check cli tests packages/hooks
uv run ruff format --check cli tests packages/hooks
```

Use a sandbox home and project for materialization. A local-source pin rejects modified catalog bytes until `update` accepts them. A Git-source pin ignores uncommitted working tree changes.

## Template composition

Template entrypoints route Markdown consumers to context-specific recipes rather than a universal section checklist. HTML packages include self-contained worked compositions, usage contracts and individually loadable fragments. See the [template system](../template-system/README.md) for source ownership, component contracts, regeneration and browser tests. Change canonical HTML under template-system, then regenerate distribution files; never maintain separate hand-edited copies of the foundation. Module files must appear in their package manifest before they can be distributed.

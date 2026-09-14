# Package authoring

Each `packages/<kind>/<name>/manifest.yaml` declares one package with an ID, version, description, entry point, complete file allowlist, scopes and token budget. Run `dasync schema manifest --json` for the exact contract. Unknown fields fail validation. Computed package digests include manifest metadata and hashes of declared files.

Kinds are Skill, Agent, Context, Policy, Template and Hook. Dependencies are ID-to-version-constraint mappings under `requires`; suggestions never activate implicitly. Profiles contain explicit root IDs and never bypass dependency, scope or trust checks. Every package is optional unless explicitly selected or required by another selected package.

Use `SKILL.md` with name and description frontmatter for skills. Keep descriptions precise enough for discovery. Put long procedures, templates and evidence protocols in declared supporting files. The renderer adds references for selected direct dependencies. Do not add a dependency merely to make an optional output or reviewer install automatically.

Contexts describe facts and preferences. Policies contain operative rules. The initial private context packs define binding contracts; they do not fabricate personal or project facts. Bind existing crafted context in user configuration and grant explicit project/provider access. To create a public context, set `sensitivity: public` and choose `access: inherit`, `explicit` or `never` intentionally.

Policies can declare file globs, a priority and an exclusive conflict group. Codex receives selectors as instruction prose; Claude and Cursor can render native file selectors. Conflicting selected policies fail instead of silently dropping one.

Executable files require an `executable` declaration and exact package-digest approval. Hooks declare portable event names, permissions and a timeout. Changes to executable content or permissions change the digest, requiring new approval. Python hook entry points are supported on POSIX hosts. Hook scripts must consume bounded JSON input and avoid logging private payloads. They execute with provider permissions; no portable sandbox is promised.

Development loop:

```sh
dasync list --source /absolute/dot-agents-sync --source-kind local --json
uv run pytest
uv run ruff check cli tests packages/hooks
uv run ruff format --check cli tests packages/hooks
```

Use a sandbox home and project for materialization. A local-source pin rejects modified catalog bytes until `update` accepts them. A Git-source pin ignores uncommitted working tree changes.

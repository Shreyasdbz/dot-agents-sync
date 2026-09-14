# Optional engineering profile

engineering-cloudflare selects coding and verification policies plus opinionated platform, monorepo and UI policies. Its single public engineering-stack reference is a dependency of the platform policy, linked by the adapters for on-demand reading. It does not install skills, agents, hooks or private bindings; combine it with dev-core if those workflows are wanted. No new configuration format, project file or CLI behavior is introduced.

## Rules versus context

Policies contain behavior that must not depend on reference discovery: Cloudflare-first/GCP-next, no Vercel services, service approval boundaries, preferred stacks, no app-to-app imports, CLI-first shadcn operations and quality checks. The reference supplies selection criteria and examples. Existing private context contracts hold actual project versions, services, commands, preset IDs and approved exceptions; selecting this profile does not grant access to them.

These are optional defaults for adopting projects, not a mandate to convert dasync or existing repositories. Explicit project decisions take precedence over defaults; conflicting requirements must be surfaced before changing architecture. Context is evidence, not authority to approve spending, deployment or a new vendor. Reuse existing project documentation or separately authorized bindings; no new private file is required.

## Selection

Inspect the profile with list/explain and preview using the ordinary plan/apply workflow in README.md. For a new disposable project, setup accepts --profile engineering-cloudflare; add --profile dev-core only when its skills are wanted. Existing scopes can preview configure --profile engineering-cloudflare --apply --dry-run with their explicit scope/path. Confirm desired selection and dependencies before applying. The local authoring checkout uses --source-kind local; a Git source reads committed objects and will not contain uncommitted catalog changes.

The three new policies are individually selectable. Removing a profile does not remove packages independently selected elsewhere. Existing general profiles do not acquire the platform, monorepo or UI preferences. The generic coding policy is strengthened with public-contract documentation and a bounded anti-slop audit for all its existing consumers.

## Footprint and verification limits

Keep the opinionated policy entries together below 7,000 UTF-8 bytes and the detailed reference below 6,000 bytes. These are source regression guards, not exact model-token counts. Native providers receive short policy bodies; supporting material is linked. Current adapters may emit both a standalone reference and a dependency copy. Tests check those links rather than claiming zero duplication or automatic reference loading.

Project scope is tested for all three adapters. Cursor user policies remain manually loaded references with an explicit degraded capability report; installing them is not proof of automatic enforcement. Codex and Claude policy rendering is structural evidence, not proof of model compliance.

Tests exercise profile isolation, dependency resolution, private-context independence, rendered references, transaction apply and idempotent sync in temporary environments. Behavioral scenarios in evals/cases.json cover runtime confusion, vendor authorization, import boundaries, missing presets and bounded quality cleanup. They are unexecuted model-evaluation inputs until a real run is recorded with the existing evaluation protocol.

Local verification on 2026-09-14: the full Python suite passed 94 tests, including nine engineering-profile checks; Ruff lint/format checks, generated-template parity and git diff whitespace checks passed. The three new policy entries total 5,656 UTF-8 bytes; the on-demand reference is 4,764 bytes. No real user configuration was installed or changed, and no hosted model or deployment was exercised.

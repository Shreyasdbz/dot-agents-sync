# Identity, approvals and realistic local testing

Optional engineering guidance. Authentication, production approvals and the data hierarchy below are confirmed preferences. The snapshot workflow remains a proposed design; actual export scope, field transformations and implementation require project-specific decisions and authorization.

## Authentication

Omit authentication when the product does not need identity or protected access. When needed, prefer Clerk; preserve existing approved authentication rather than migrating incidentally. Authentication does not replace server-side authorization or tenant isolation. Use development/test identities locally, never production sessions or credentials. A hosted authentication development instance is an external dependency, not a locally dockerized service; disclose offline and fidelity limitations.

## Production approvals

Require explicit approval for production deployments, production database migrations, production data deletion and production access-permission changes. Bind approval to the intended environment, action and scope; do not infer it from an implementation request. Preview risk and recovery, and verify the outcome after authorized execution.

Do not impose these production-specific approval gates on ordinary in-scope LOCAL development, migrations or disposable test resets. Still preserve unrelated files and irreplaceable local data; secrets, data exports, spending and external side effects retain their own permission boundaries. A script running locally that changes production is a production action.

## Proposed snapshot workflow

Use synthetic data by default for local development and automated tests. When production-derived data is needed, sanitized snapshots are the default, preserving relationships and relevant behavior. Raw data is an exception requiring explicit approval of the purpose, specific users/tenants or records, necessary fields, authorized recipients, local destination and expiry. Keep unrelated records sanitized or excluded; approval for one user's data is not approval for their entire tenant or connected users. Exclude credentials, live sessions and payment secrets even from a raw-data exception. Do not upload snapshots to AI services or shared artifacts merely because local use was approved.

The goal is repeatable E2E testing against realistic production-shaped data, including service-version skew and schema migrations. Build this as project-owned tooling around actual storage and runtime choices, not a generic dasync data-transfer command. No snapshot script or production connection is supplied here.

1. Preview the source, dataset/tenant or time-window filters, related records, expected size, local destination, sensitivity and potential export cost/load. Prefer the smallest representative slice; allow a full snapshot only when useful and approved. Never interpret permission to read application code as permission to export customer data.
2. Use a supported consistent snapshot/export mechanism and least-privilege source credentials. Independent exports across databases, object storage and queues are not automatically one consistent point in time. Record consistency limits; subset by related entities rather than arbitrary row limits that break foreign keys or workflows.
3. Apply the project's transformation policy before data leaves the controlled source environment where feasible. Sanitize direct identifiers, free text and sensitive fields while preserving relationships, uniqueness, formats and useful edge cases; bypass sanitization only for the exact approved raw-data exception. Exclude credentials, live sessions, access tokens and payment secrets. Deterministic pseudonyms are still sensitive when linkable; do not claim anonymization merely because names changed. Unknown classifications block export rather than passing through silently.
4. Restore into a fresh, clearly isolated local database/volume. Validate schema version, referential integrity, row counts and approved redaction checks before exposing it to app containers. Keep snapshots and reports with sensitive identifiers out of Git, artifacts, cloud sync and telemetry. Define access controls, encryption, retention and explicit cleanup targets; a gitignore alone is not protection.
5. Start pinned service versions in local orchestration where supported. Keep email, payments, webhooks, scheduled jobs, queue consumers and analytics pointed at safe test sinks or disabled until explicitly exercised. Block accidental production endpoints and live credentials. Do not replay copied outbox/queue records into real integrations. Match the actual runtime with supported emulators where necessary; Docker is not proof of cloud-service equivalence.
6. Run the baseline E2E flow, upgrade only the selected service, and test the intended old/new compatibility combinations. Recreate fresh snapshot copies for migration rehearsals; test schema/data invariants and interrupted/resumed backfills when relevant. Exercise expand/backfill/contract ordering where needed. Old code must remain compatible for the stated rollout window; application rollback is not automatic reversal of a destructive schema migration.
7. Report snapshot age, transformation version, code/runtime versions, scenario outcomes and fidelity gaps. Reset or remove only the approved disposable local targets. Successful local tests do not prove production scale, cloud identity, distributed consistency or rollout safety.

## Project decisions still needed

Approve data classes permitted locally, sanitization rules, full-versus-subset scope, export timing and storage/expiry controls. Decide how production identity references map to local test users without copying authentication secrets. If sanitized data cannot reproduce a defect, review a narrowly scoped exception rather than silently pulling raw data. Any actual production export requires an explicit authorized workflow; this proposal does not grant it.

## Documentation starting points

Checked September 14, 2026; verify actual runtime versions and current export limitations during implementation.

- [PostgreSQL pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html): database export consistency and tool/version constraints.
- [Cloudflare D1 import/export](https://developers.cloudflare.com/d1/best-practices/import-export-data/): supported database export/import path, not a claim of complete cloud emulation.
- [Clerk environments](https://clerk.com/docs/guides/development/managing-environments): separate development and production instances.

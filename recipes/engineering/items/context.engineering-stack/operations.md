# Data and operations defaults

Optional engineering guidance; actual infrastructure, maturity and approved exceptions belong in project context. No accounts, telemetry exports or deployments are authorized by loading this reference.

## Data selection

Choose databases and query tooling for the actual workload within the Cloudflare-first, GCP-next policy. No database, ORM or query builder is predetermined. Consider access patterns, transactions, consistency, expected data size, local development, migrations, backup/restore, runtime support and operating cost. Avoid speculative scale and redundant stores. Explain a material trade-off briefly, preserve established project choices and obtain approval for other hosted vendors.

## Environments

Default to LOCAL on the development machine and PROD. Do not provision staging, hosted development or per-PR preview environments automatically. A project can explicitly require staging when its risks or integrations justify it; document the reason rather than making it universal.

Keep local data, credentials and telemetry distinct from production. Prefer local services/emulators and test-mode external integrations; document fidelity gaps. Remote dependencies used during local development need an explicit safe binding and approval, not a silent connection to production. LOCAL + PROD is not permission to test destructively in PROD. Before an authorized release, verify migration safety, backup/restore when relevant, rollback limits and a non-destructive smoke check. Raise a material safety gap instead of bypassing it because staging is absent.

## Beyond proof of concept

Treat logging and analytics as primary engineering work once continuing beyond a disposable POC; include them in the next implementation scope and verify them before public release. A POC may use lightweight local logs and focused checks. Do not defer observability until after launch or introduce a full monitoring stack merely to prove an idea.

Use OpenTelemetry for supported operational signals and a selected centralized destination across web applications, services and jobs. Keep vendor-specific setup at a narrow integration boundary. Correlate structured logs and traces with service identity, environment and release version; define useful latency, traffic and error measurements. A shared monorepo configuration belongs in packages, not app-to-app imports. Do not force a runtime-incompatible SDK or add a Collector unless routing, authentication, processing or sampling warrants it.

Verify one real representative cross-boundary flow and one controlled failure: trace continuity, correlated diagnostic logs and an actionable signal visible in the destination. SDK initialization, exported spans and isolated service traces are not end-to-end proof. Check browser, Workers, Bun and Python support separately; runtime and propagation limitations must be explicit. Keep browser ingestion credentials safe, restrict accepted payloads and propagation targets, redact secrets and sensitive content, and bound exporter retries, buffers and latency. Telemetry failure must not break the primary operation or cause a retry storm.

Default to $0 telemetry spend and a 14-day diagnostic retention target. A project may explicitly approve a different budget or retention requirement; serious distribution alone does not imply approval. Account for ingestion, export, storage, queries, collectors and hosting, not just the destination's free tier. Do not enable paid overages, trials that convert to paid service or billable infrastructure without that project decision. Where free retention is fixed, record its actual duration rather than claiming an exact 14-day deletion policy. Assess maintenance before calling self-hosting free.

Set sampling and volume limits, monitor dropped data and define behavior when the free allowance is exhausted. Surface any conflict between $0 and release-readiness requirements; do not silently spend or ship without required diagnostics. Do not promise that head sampling retains every error or enable blanket payload capture. LOCAL exports remain local by default; approved hosted test telemetry must be separately identified.

Default analytics to basic traffic, performance and operational health appropriate to the application. Activation, conversion funnels, behavioral retention analysis and session replay are project-specific additions, not baseline requirements. Add them only for an explicit product need with a minimal event vocabulary. OTel diagnostics are not an exact business ledger. Document collection purpose, data minimization, access and retention before publishing. The 14-day diagnostic target does not automatically define analytics retention. Vendor choice and sensitive collection remain explicit decisions; no platform is selected by this reference.

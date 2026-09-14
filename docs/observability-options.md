# Low-cost observability for personal projects

## Recommendation

Start with a bounded Grafana Cloud Free evaluation, with Axiom Personal as the principal alternative and Honeycomb Free as the trace-investigation alternative. This is a recommendation for a trial, not a platform selection. Preserve OpenTelemetry instrumentation and keep destination configuration replaceable. Avoid operating a production observability database merely to eliminate a small hosted bill.

This assessment assumes a few low-traffic projects, LOCAL development and PROD deployment, Cloudflare-first applications and occasional GCP services. Published prices and capabilities were checked on September 14, 2026; figures are USD and exclude taxes, application hosting, export charges and network costs unless stated. No authenticated account, billing controls or cross-runtime integration has been tested. Current vendor terms must be rechecked before adoption.

Grafana is the leading trial candidate because its managed free allowance covers several operational signals and browser monitoring. Axiom offers a compelling personal tier when searchable events and logs dominate. Honeycomb offers substantial event volume and a tracing-oriented investigation model, but its paid entry point is a poor match for a strict single-digit-dollar budget. GCP is an important alternative if avoiding another vendor matters more than frontend tooling convenience. These rankings are analytical judgments, not measured usability results.

## What must be centralized

Operational observability should connect a user-visible failure to its request, downstream calls, errors and release. Logs explain events; traces connect work across boundaries; metrics summarize traffic, latency, failures and resource pressure. A collection of disconnected service traces in one account does not satisfy distributed tracing.

Product analytics answers a different question: whether people reach activation, complete a task or abandon a flow. It need not share the trace backend, and sampled operational traces should not become an exact business ledger. Keep one primary operational destination and add a separate analytics tool only for a concrete question that the primary tool does not reasonably answer.

## Platform comparison

The allowances below use different units and are not equivalent capacities. Verify account-wide versus project-specific limits and sharing rules before consolidating multiple projects.

| Candidate | Published starting allowance or price | Main advantage | Constraint for this workload |
| --- | --- | --- | --- |
| Grafana Cloud Free | 50 GB logs and 50 GB traces per month; 14-day retention; free-tier overview lists 10k metrics series, 50k frontend sessions and 3 users | Broad managed operational coverage with a substantial free allowance | Multiple signal limits and a shorter history; Pro has a $19/month platform fee plus applicable usage |
| Axiom Personal | $0; 500 GB/month loading, 10 GB-hours query compute, 25 GB storage, 30-day retention | Strong event/log exploration with trace support | Loading allowance is not retained-storage capacity; query compute can constrain investigations |
| Honeycomb Free | 20M events and 100M metric data points/month; 2 triggers; Pro starts at $150/month | Large event allowance and distributed-trace investigation | A trace contains multiple billable events; verify frontend feature entitlement separately |
| Better Stack Free | 3 GB logs and 3 GB traces, each retained 3 days; 30 GB metrics | Integrated telemetry, errors and incident tooling | Three days is short for intermittent hobby-project debugging; paid rates depend on region and usage |
| GCP Observability | 50 GiB logs/project/month; 2.5M trace spans/billing account/month; trace overage $0.20/M spans | Already within the preferred provider hierarchy; very low trace overage | IAM and ingestion setup across providers; metrics, retention and other products have separate charging rules |
| Uptrace Cloud | Advertises 50 GB/month and 5,000 timeseries free; pricing advertises paid ingestion from $0.075/GB | Promising low-cost OTel-oriented option | Public cap/overage language is inconsistent; confirm retention, minimums and enforcement before relying on it |
| SigNoz | Managed offering currently advertises $49/month minimum, including usage; community self-hosting available | Integrated observability with a self-hosted route | Managed minimum exceeds the intended low-cost target; self-hosting needs resources and maintenance |
| ClickStack | Open-source deployment available; managed offerings are evolving | Viable self-hosted observability alternative | No durable zero-cost managed production allowance established here; hosting and operations remain real costs |

Sources: Grafana pricing/free tier [^1][^2], Axiom pricing [^3], Honeycomb pricing/usage [^4][^5], Better Stack pricing [^6], GCP pricing [^7], Uptrace pricing/homepage [^8][^9], SigNoz pricing [^10], ClickStack [^11][^12].

### Grafana Cloud

Use Grafana as the first trial if one operational workspace for logs, traces, metrics and frontend diagnosis is the priority. Its OTLP endpoint accepts telemetry from SDKs or Collectors. Faro's tracing instrumentation uses OpenTelemetry and provides configurable cross-origin trace-header propagation; that configuration must match owned API origins rather than indiscriminately attach headers to third parties.[^13][^14]

Validate the free-tier behavior when an allowance is reached and expose dropped-data signals. The usage documentation describes enforced limits and discarded spans; a free tier is not unlimited incident retention.[^15] The trial should test log-to-trace navigation, browser-to-backend correlation and whether the interface feels manageable without assembling a large dashboard collection.

### Axiom

Axiom is the strongest alternative when a unified event store and ad hoc log queries feel simpler than separate signal tools. Its trace explorer treats trace events as dataset events, supporting correlated exploration.[^16] The Personal tier has three separate constraints: loading, retained storage and query compute. A large loading figure alone does not establish capacity for a month's high-detail telemetry. Its paid Cloud plan has a $25/month platform fee; spending limits are documented as pausing excess usage.[^3]

### Honeycomb and Better Stack

Honeycomb counts individual spans as events, so 20M events does not mean 20M multi-service requests. Logs can also consume the allowance. Usage documentation describes 60-day retention when changing plans, but exact current retention and any frontend add-on entitlement should be confirmed in the chosen account rather than inferred from older announcements.[^5] Its free tier is attractive; the paid step warrants an exit or sampling plan before approaching the limit.

Better Stack accepts OTLP traces and supports centralized telemetry.[^17] Its pricing lists separate log and trace free allocations, a short retention window, and additional incident-management and real-user-monitoring products.[^6] It remains worth trying if integrated alerting matters more than historical investigation, but the free retention is a substantive compromise, not a footnote.

### GCP

For a trace-heavy, low-volume system already using GCP, native Observability is economically credible. For example, 5M spans in a month would imply $0.50 in trace ingestion above its 2.5M-span allowance, before any other charges. Log allowance is per project whereas trace allowance is per billing account; do not multiply the latter by the number of applications.[^7]

Google documents OTLP support through its Telemetry API and authenticated access.[^18][^19] Cross-cloud applications and browsers still need a safe ingestion/authentication design. A generic OTLP URL is not evidence that a browser should receive a privileged cloud credential. Treat frontend errors, user-experience metrics and navigation from those events into traces as an explicit trial requirement.

### Uptrace and self-hosting

Uptrace deserves a watchlist position, but not a cost guarantee. Its homepage promises a monthly cap will not be exceeded, while its FAQ says ingestion continues and excess usage is billed. Its pricing page also mixes ongoing free-tier and trial language. Those contradictions need written clarification before choosing it for a hard-budget project.[^8][^9]

SigNoz's Docker guide calls for at least 4 GB of memory, which illustrates why free software is not free production hosting.[^20] ClickStack is another relevant self-hosted option, but should be assessed as a database-backed service to operate, not a no-maintenance telemetry endpoint.[^11][^12] Include compute, storage, backups, upgrades, access control and time responding to disk pressure. Running the only PROD trace store on a laptop that sleeps defeats the purpose of reliable release diagnostics.

## Cloudflare interoperability is the primary technical gate

Cloudflare documents native export of logs and traces, but not metrics. Export currently requires Workers Paid or higher. The published schedule says billing begins October 1, 2026, with 10M events included for each listed signal and $0.05 per million additional events. Recheck the precise metering and any combined storage/export charges before enabling it; free-backend pricing does not include the application plan.[^21]

More importantly, Cloudflare's known-limitations page says native trace context is not propagated to non-Cloudflare services. Its custom-span documentation also says access to trace/span identifiers for manual propagation is planned. Meanwhile the API reference exposes inbound propagation-policy fields conditional on feature availability. This is documentation tension, not proof that complete cross-cloud tracing works.[^22][^23][^24]

The acceptance criterion is an observed browser → Worker → GCP service trace with correct parentage, not simply successful exports. If native tracing cannot satisfy that, investigate a supported application-level instrumentation path for the exact runtime and versions. Avoid duplicate auto-instrumentation and do not present an unofficial workaround as supported without a test. HTTP, service bindings and asynchronous queues may need different correlation strategies; test the paths actually used by the project.

Native timing also has documented limitations for non-I/O operations.[^22] Do not interpret a zero-duration span as proof that CPU work was free. Database and third-party calls can be traced at the owned client boundary without assuming visibility inside the external system.

## Browser instrumentation and privacy

OpenTelemetry JavaScript documents stable traces and metrics but marks browser client instrumentation experimental.[^25] Select the smallest working browser integration and test navigation, failed fetches and page lifecycle behavior. Keep SDK-specific configuration behind a narrow boundary; do not promise the entire frontend implementation is vendor-neutral just because exported spans use OTel.

Never put a privileged ingestion key in client bundles. Use an appropriate public browser ingestion endpoint or a bounded gateway, with origin restrictions, payload validation, rate limits and server-side credentials as applicable. Restrict trace-header propagation to intended origins and do not trust arbitrary client trace baggage as authorization. CORS alone is not abuse protection.

Redact secrets, cookies, authorization headers, full sensitive URLs and personal request/response content before export. OTel guidance provides processors and attribute-handling approaches for sensitive data; decide the schema before collecting, rather than relying on a later cleanup job.[^26] Default session replay off until its purpose and data handling are explicitly agreed. Export queues and retries need finite limits so a telemetry outage does not degrade the application indefinitely.

## Cost model and controls

Measure at least spans per request, serialized bytes per span, log bytes per request, retained days, active metric series, browser sessions and query usage. Count all projects together where the allowance is account-wide. Provider compression and metering differ; raw application payload estimates are planning inputs, not invoice predictions.

An illustrative workload of 100,000 requests/month, six spans/request and 1 KB/span produces approximately 600,000 spans and 0.6 GB of trace payload. At 1M requests it produces 6M spans and 6 GB. These are arithmetic examples, not benchmarks, and exclude logs, browser events, metadata overhead and infrastructure metrics. A single verbose payload logger can outweigh all the spans.

Start with a few useful signals. Use stable low-cardinality labels for metrics and put detailed diagnostic identifiers in appropriately controlled logs/traces rather than unbounded metric dimensions. Sampling should preserve trace consistency across services. Head sampling cannot guarantee retention of later errors; tail sampling requires additional processing and buffering. Do not introduce that infrastructure before the workload justifies it.

Set spend alerts and hard limits where available, and distinguish a notification from an enforced cap. Decide what happens at the cap: lose low-priority telemetry, change sampling or explicitly approve spending. Retain aggregate error measurements even when traces are sampled. Prevent LOCAL debug noise from exhausting PROD allowances. Never bypass free-tier terms by manufacturing accounts or misrepresenting project ownership.

## Product analytics choice

For basic traffic and website performance questions, start by evaluating Cloudflare Web Analytics, which is advertised as free and privacy-first.[^27] That preserves the provider preference without requiring a separate product-analysis platform.

For explicit activation, conversion and retention questions, evaluate PostHog separately. Its current pricing advertises 1M analytics events/month and a no-card free plan limited to one project; additional products have separate allowances. Multiple-project needs therefore deserve checking rather than assuming every personal application fits the same free account.[^28] Do not add session replay, feature flags or a second error pipeline just because they are available. The question to resolve is what decisions analytics should support, not how many events can be captured.

## Trial and release acceptance

After a destination is approved, use one representative application rather than migrating every project. Develop the path in LOCAL with a local sink or explicitly approved isolated test destination. Do not create staging automatically. A PROD smoke test requires deployment approval and must be non-destructive; the two-environment preference does not authorize sending personal data or inducing public failures.

| Check | Required evidence |
| --- | --- |
| Cross-boundary trace | One owned user flow connects browser, API and downstream service; record trace ID and correct parent/child or asynchronous link relationships |
| Failure diagnosis | A controlled safe failure produces useful redacted logs, trace status and an actionable alert or error signal |
| Runtime fit | Instrumentation works in the actual deployed runtime, not just Node tests or a local emulator |
| Privacy | No credentials or sensitive payloads in bundles, logs, spans, analytics events or replay |
| Cost | Measured volume projected to a month, retention confirmed, spending behavior documented and dropped-data signal visible |
| Performance | Telemetry overhead and exporter-failure behavior assessed against project needs |
| LOCAL/PROD separation | Distinct data/configuration; no unapproved production writes or local noise in production analytics |
| Exit path | Change destination without rewriting business logic; record vendor-specific browser and dashboard dependencies |

Confirmed defaults from September 14, 2026: 14 days of diagnostic history is sufficient; telemetry spend targets $0 unless a project explicitly approves otherwise; analytics defaults to basic traffic/performance rather than activation, funnels or behavioral retention. Those product analytics features are added only when a project needs them. An ambition for serious distribution does not itself approve spending.

These preferences favor evaluating the free managed shortlist rather than a paid minimum or self-hosted production stack. The budget includes incremental export and hosting costs, not just the telemetry backend. Select a platform only after the trial establishes actual cost and usability; the destination remains undecided and no signup, installation or paid upgrade is authorized. If the free allowance cannot support required diagnostics, request a project-specific budget or design decision rather than weakening release readiness silently.

## Sources

All sources are official vendor/project publications accessed September 14, 2026; undated live pages are not immutable pricing commitments.

[^1]: Grafana Labs. [Grafana pricing](https://grafana.com/pricing/).
[^2]: Grafana Labs. [Grafana Cloud Free](https://grafana.com/products/cloud/free-tier/).
[^3]: Axiom. [Pricing](https://axiom.co/pricing).
[^4]: Honeycomb. [Pricing](https://www.honeycomb.io/pricing).
[^5]: Honeycomb. [How Honeycomb calculates usage](https://docs.honeycomb.io/get-started/manage-costs/how-honeycomb-calculates-usage).
[^6]: Better Stack. [Pricing](https://betterstack.com/pricing).
[^7]: Google Cloud. [Observability pricing](https://cloud.google.com/products/observability/pricing).
[^8]: Uptrace. [Pricing](https://uptrace.dev/pricing).
[^9]: Uptrace. [Platform overview](https://uptrace.dev/).
[^10]: SigNoz. [Pricing](https://signoz.io/pricing/).
[^11]: ClickHouse. [ClickStack](https://clickhouse.com/clickstack).
[^12]: ClickHouse. [ClickStack Cloud private preview](https://clickhouse.com/blog/clickstack-cloud-private-preview).
[^13]: Grafana Labs. [Send and ingest OTLP data](https://grafana.com/docs/opentelemetry/ingest/).
[^14]: Grafana Labs. [Capture frontend traces](https://grafana.com/docs/grafana-cloud/observe-and-act/monitor-applications/frontend-observability/instrument/tracing-instrumentation/).
[^15]: Grafana Labs. [Understand usage limits](https://grafana.com/docs/grafana-cloud/platform/pricing-and-usage/usage-limits/).
[^16]: Axiom. [Explore traces](https://axiom.co/docs/query-data/traces).
[^17]: Better Stack. [Tracing](https://betterstack.com/docs/logs/tracing/).
[^18]: Google Cloud. [OTLP support](https://docs.cloud.google.com/stackdriver/docs/otlp/overview).
[^19]: Google Cloud. [Telemetry API authentication](https://docs.cloud.google.com/stackdriver/docs/reference/telemetry/authentication).
[^20]: SigNoz. [Docker installation](https://signoz.io/docs/install/docker/).
[^21]: Cloudflare. [Exporting OpenTelemetry data](https://developers.cloudflare.com/workers/observability/exporting-opentelemetry-data/).
[^22]: Cloudflare. [Tracing known limitations](https://developers.cloudflare.com/workers/observability/traces/known-limitations/), updated June 16, 2026.
[^23]: Cloudflare. [Custom spans](https://developers.cloudflare.com/workers/observability/traces/custom-spans/).
[^24]: Cloudflare. [Workers Scripts API](https://developers.cloudflare.com/api/resources/workers/subresources/scripts/).
[^25]: OpenTelemetry. [JavaScript status and releases](https://opentelemetry.io/docs/languages/js/).
[^26]: OpenTelemetry. [Handling sensitive data](https://opentelemetry.io/pl/docs/security/handling-sensitive-data/).
[^27]: Cloudflare. [Web Analytics overview](https://developers.cloudflare.com/web-analytics/about/).
[^28]: PostHog. [Pricing](https://posthog.com/pricing).

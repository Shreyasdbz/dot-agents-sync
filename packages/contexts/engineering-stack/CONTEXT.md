# Engineering stack decision reference

Public, optional decision support, not project facts or authority. Load for stack selection, runtime compatibility or repository structure decisions. Operative requirements live in the selected policies; project context supplies actual choices and approved exceptions.

## Workload before service

Describe execution duration, concurrency, latency, native/system dependencies, state consistency, background scheduling, residency and recovery needs before selecting services. Consider observability, backups, export/recovery and projected operating cost, not only introductory pricing. Avoid a platform workaround whose complexity exceeds the benefit of provider consolidation.

Evaluate Cloudflare first, then GCP for demonstrated gaps. Do not infer Python package compatibility from a framework name: test imports and a representative request/job with the real deployment toolchain. Conventional containerized services may fit Cloud Run; check its runtime contract and workload requirements rather than assuming every background process fits a request-serving container.

Record the smallest useful decision: requirement, candidates actually considered, selected service/runtime, supporting evidence date, cost assumptions, exception approval if needed. Recheck vendor documentation before implementation; limits, packages and prices change.

## TypeScript and Python

Distinguish package manager, build tool, test runner and production runtime. A successful Bun test does not establish Workers compatibility. Exercise bindings, network calls, persistence and failure behavior in the appropriate runtime; mocked tests remain a separate evidence class.

Use Hono for a justified HTTP boundary, not an extra layer around every function. Use TanStack Start's server facilities when they already meet the web application's needs. Use Query for remote/server state and keep local interaction state local; choose one owner for fetching and invalidation across routing and Query.

Use Python when its libraries or execution model earn the additional toolchain. FastAPI is for HTTP APIs, not a required wrapper for a batch job. uv manages Python environments and dependencies. Adopt LangChain or LangGraph only when their orchestration capabilities outweigh a simpler direct implementation.

## Repository example

A possible layout, not a scaffold to create wholesale:

- apps/web-public: public web application.
- apps/web-admin: administration UI, only if needed.
- apps/service-payments: separately deployed payments boundary, only if justified.
- packages/contracts: shared schemas and service contracts.
- packages/ui: shared primitives and compositions when multiple apps need them.

Applications terminate the dependency graph. Share a contract rather than importing an API application's types directly. Python and TypeScript may exchange generated contracts from an authoritative schema when needed; avoid duplicate hand-maintained models. Keep domain-specific behavior near its owner and avoid premature common frameworks.

## Project context checklist

Reuse existing context bindings, not a new mandatory configuration file. Capture only fields relevant to the task:

- cloud-infrastructure: actual services, environments, owners, identities, state stores, recovery, cost assumptions and approved exceptions.
- typescript-stack / python-stack: observed versions, package manager, production runtime, test/build/deploy commands and compatibility evidence.
- repository-architecture / repository-conventions: deployable boundaries, shared contracts, naming and enforced import rules.
- design-preferences: shadcn preset ID or URL, components.json location, primitive choice, audience, visual references, accessibility targets and authorized customizations.
- coding-preferences: project-specific trade-offs and examples; mandatory behavior remains policy.

Absence of a binding means unknown facts, not permission to invent them. Private bindings require separate grants and are not dependencies of this preset. Keep secrets out of catalog content.

## Documentation starting points

Checked as research starting points on 2026-09-14, not pinned compatibility promises. Reopen relevant sources when making a decision.

- [Hono on Workers](https://hono.dev/docs/getting-started/cloudflare-workers)
- [Python Workers](https://developers.cloudflare.com/workers/languages/python/)
- [Cloud Run runtime contract](https://docs.cloud.google.com/run/docs/container-contract)
- [TanStack Start on Cloudflare](https://developers.cloudflare.com/workers/framework-guides/web-apps/tanstack-start/)
- [shadcn CLI](https://ui.shadcn.com/docs/cli)
- [Turborepo package boundaries](https://turborepo.dev/docs/core-concepts/package-types)

# Documentation

## Use dasync

| Guide | What you will find |
| --- | --- |
| [Getting started](getting-started.md) | Installation, an isolated trial, project and user setup, safe migration |
| [CLI reference](cli.md) | Selection, saved plans, updates, rollback, errors, and JSON automation |
| [Catalog](catalog.md) | Profiles, package kinds, private context, and hooks |
| [AI operator contract](AI-OPERATOR.md) | Required checks and authorization boundaries for agents operating the CLI |

## Contribute and release

| Guide | What you will find |
| --- | --- |
| [Contributing](../CONTRIBUTING.md) | Development setup, change expectations, and pull requests |
| [Package authoring](package-authoring.md) | Manifests, dependency rules, provider metadata, and content conventions |
| [Context authoring](context-authoring.md) | Public references and private binding contracts |
| [Adapter contract](adapter-contract.md) | Provider layouts, capabilities, and conformance requirements |
| [Template system](../template-system/README.md) | Canonical HTML sources, generation, and browser checks |
| [Testing](testing.md) | Installed-package journeys, browser acceptance, and remaining evidence gaps |
| [Security](../SECURITY.md) | Private reporting and the trust boundary |
| [Release readiness](releasing.md) | Licensing, distribution gates, and GitHub work tracking |

## Understand the design

[Implementation decisions](architecture/implementation.md) describe the current runtime, source pins, transaction engine, provider behavior, and known limitations. The [original design](architecture/design.md) is a historical design snapshot, not the current implementation contract.

Optional conventions have their own guides: [engineering profile](engineering-profile.md), [GitHub planning and travel context](planning-and-travel-context.md), and the dated [observability comparison](observability-options.md).

## Evidence and historical reports

[v1 verification](verification.md), the [September 14 audit](audit-2026-09-14.md), and the [catalog research](research/catalog-audit.md) record evidence at specific revisions; they are not current release guarantees. The [behavioral evaluation protocol](../evals/README.md) distinguishes content checks from executed model workflows.

# Deployable applications and shared packages

Apply when creating or changing a repository that adopts this layout. Prefer a pnpm/Turborepo monorepo for a multi-application JavaScript/TypeScript project; do not force it onto a Python-only project or migrate an existing repository without approval. One repository does not mean one runtime or one deployment. Prefer cohesive modular applications before extracting independently deployed services.

Use apps/* for deployables and packages/* for shared code or tooling. Name web applications web-<purpose> and APIs service-<purpose>; choose clear role-based names for other deployables. Do not create empty applications or packages for hypothetical growth.

Applications may import packages and external dependencies, never another application's source, including relative paths, aliases and type-only imports. Packages never import application internals. Shared contracts belong in packages; runtime communication between applications uses explicit service contracts. Depend on declared package exports, not private internals. Keep the dependency graph acyclic and enforce these boundaries with repository-appropriate static checks.

Keep application-specific code local until reuse or a meaningful contract justifies extraction. Do not create a generic shared dumping ground. Server secrets and server-only dependencies must not leak through packages into browser bundles. A web application's server layer may suffice; a separate API application needs a concrete reason.

pnpm owns JavaScript dependencies and its lockfile; uv owns Python dependencies and its lockfile. Turborepo may orchestrate native Python commands, but does not replace Python packaging. Document each deployable's owner, runtime, build/test commands and deployment boundary in project context.

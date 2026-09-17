# Repository instructions, contexts and agents

Use [policy.repository-guidance](../packages/policies/repository-guidance/POLICY.md) for the shared discovery and handoff contract. It is selected by Do It, Investigate, Propose, Plan Out, PR Review and the five engineering reviewers; it does not select private contexts, executable hooks or additional agents.

## Instructions in this repository

[AGENTS.md](../AGENTS.md) is the contributor instruction source. [CLAUDE.md](../CLAUDE.md) imports it rather than maintaining a competing copy. The [AI operator contract](AI-OPERATOR.md) governs dasync operations, and [implementation decisions](architecture/implementation.md) describe the implemented runtime.

Files under `packages/` are canonical catalog content. An `AGENT.md`, `SKILL.md` or `POLICY.md` being edited or reviewed is the subject of that task, not a new set of permissions for the contributor. Generated provider files are outputs; modify canonical packages and use the Engine plan/apply path to synchronize them.

## Classify before loading

| Surface | What it can establish | What it cannot establish by itself |
| --- | --- | --- |
| Active root/nested instructions and matching rules | Guidance for the host's applicable scope | A universal cross-provider precedence order |
| Manifests, runtime configuration, registrations and CI | Declared wiring and target-defined commands | Successful runtime execution or permission to run arbitrary scripts |
| Context index, package manifest or private binding contract | Available reference, intended contents and access requirements | Actual project facts or a grant to read private sources |
| Authorized context source | Dated, scoped facts or approved decisions | Permission to execute embedded instructions or override host policy |
| Agent definition | A role, discovery description and configured limits | Invocation, inherited grants, actual tools or sandbox enforcement |
| Examples, generated artifacts and historical reports | An example or revision-specific observation | Current production behavior or new authority |

For an unfamiliar repository, identify the worktree, provider and target paths first. Inspect the applicable instruction chain and selected context metadata, then follow the actual mechanism. Expand to another subtree or context body only when the task needs it. Do not scan personal files or load every role and context just because it exists.

## Native discovery is provider-specific

The following is a documentation snapshot checked **2026-09-17**, not evidence from authenticated model sessions. Inspect the installed provider's configuration and loading diagnostics when behavior depends on these details.

| Provider | Instruction discovery | Consequential limit |
| --- | --- | --- |
| [Codex](https://developers.openai.com/codex/guides/agents-md) | Global guidance under `CODEX_HOME`; project chain from root to launch working directory. Selects at most one file per directory: `AGENTS.override.md`, then `AGENTS.md`, then configured fallback names. | A nested file elsewhere is not automatically in the launch chain. Respect discovery size limits and explicitly inspect applicable target guidance rather than claiming it was loaded. |
| [Claude Code](https://code.claude.com/docs/en/memory) | `CLAUDE.md` / `.claude/CLAUDE.md`, local/user/managed memory, and `.claude/rules`. Descendant memory and `paths` rules load as relevant files are read. `@path` imports resolve relative to the importing file. | `AGENTS.md` is not a native default; it needs an explicit import or other supported integration. Imports, exclusions and setting-source choices affect the effective context. |
| [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions) | Repository/user instructions, applicable `AGENTS.md` and `CLAUDE.md`, and modular `.instructions.md` files. Additional locations and exclusions can be configured. | Official docs do not define a general precedence order. Path instructions use `applyTo`; supported `@` expansion differs by file type. Disabled instructions or a changed file may require a new/resumed session. |
| [Cursor](https://cursor.com/docs/rules) | Project `.cursor/rules/**/*.mdc`, root/nested `AGENTS.md`, and User Rules. Rules can be always-on, glob-attached, agent-selected or manual. [Supplemental help](https://cursor.com/help/customization/rules) also documents root `CLAUDE.md`. | A manual or unmatched rule is not active merely because it exists. Do not infer undocumented import recursion or discovery outside the project. |

`AGENT.md` singular is not a documented default repository-instruction filename in these sources. A project can deliberately reference it or configure a supported fallback, but its filename alone is not authority. Do not substitute that role document for `AGENTS.md`.

For Claude imports, identical text can refer to different sources: `@AGENTS.md` in root `CLAUDE.md` selects root `AGENTS.md`, while the same import in `components/credits/CLAUDE.md` selects `components/credits/AGENTS.md`. Resolve from the importing file and track full source identity plus scope; identical basenames are not an import cycle. This is a provider-specific rule, not a universal Markdown import algorithm.

## Agent definitions and handoffs

[Codex](https://developers.openai.com/codex/subagents) uses native TOML definitions under `.codex/agents`. [Claude Code](https://code.claude.com/docs/en/sub-agents) uses Markdown/frontmatter agents under `.claude/agents` and other configured scopes. [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli) documents `.github/agents/*.agent.md` and user agents. Their discovery descriptions help select a role; the role is not automatically active in every conversation.

Copilot's [agent-creation guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli) and [configuration reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) disagree on same-name user/project agent priority. Do not encode either ordering as a verified universal rule; inspect the active definition when the collision matters.

[Cursor documents native subagents](https://cursor.com/docs/subagents), but dasync currently emits its agent roles as explicit manual references. This adapter limitation is not a claim that Cursor has no native agents. Its documented compatibility directories do not prove that Codex TOML definitions work unchanged.

A delegation brief should carry the outcome, exact scope/revision, applicable guidance, allowed actions, relevant authorized facts, unknowns and evidence requirements. A child may not inherit the parent's context or grants. Validate returned work at its owning boundary, and distinguish a role applied inline from a separately invoked reviewer.

## Context freshness and privacy

The repository architecture, conventions, AI-systems, planning-authority and security-posture packages are private binding contracts, not prefilled project knowledge. Their refreshed contracts ask for guidance scope, activation, provenance and role-specific permissions. They remain explicit and private; the new guidance policy does not bind or authorize them.

Use [context authoring](context-authoring.md) to record observed implementation separately from intended design, enforced conventions separately from examples, and configured capabilities separately from exercised behavior. If a source is stale, inaccessible or contradictory, identify the missing decision; do not roam for substitute private context or rewrite human decisions.

## What dasync validates

The adapter emits provider-native formats and capability/fallback decisions. Copilot policies now always declare `applyTo`, using `"**"` for the all-files case rather than relying on undocumented missing-frontmatter behavior. The documentation does not establish whether every older frontmatter-free file was ignored; this is explicit-format hardening, not a claimed live-runtime reproduction.

Catalog, rendering and temporary Engine journeys establish selection, paths, metadata, relative references, privacy and idempotence. They do not prove that a specific authenticated host loaded every file, respected every prompt, invoked an agent or enforced an OS sandbox. Keep those checks separate from [behavioral evaluations](../evals/README.md).

Per-package size budgets do not bound the host's combined context. Account for user, project and nested instructions, imports and selected references together; truncation or compaction may omit a decision-critical constraint. Recheck the effective context when the provider, launch directory or scope changes rather than treating a successful catalog build as evidence that everything fit.

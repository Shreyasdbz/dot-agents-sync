---
name: plan-out
description: "Plan an approved design using the project's planning authority and immediate milestone."
---

# Plan Out

Given an approved design proposal, produce a provider-neutral implementation plan from the current design, repository, relevant context, completed work, and configured planning authority. Plan Out separates the logical plan from its storage: it materializes work in the project's declared source of truth and always exposes a loadable Plan Context for downstream skills.

- Planning authority: Each project declares exactly one writable source of truth, such as a repository-local plan, GitHub, Azure DevOps, Linear, Jira, Notion, or another supported provider. Generated Markdown, HTML, and cached summaries are read-only projections unless explicitly configured otherwise.

- Portable hierarchy: Represent work as Plan → Milestone → Phase → Task. A Milestone is a major, independently demonstrable outcome spanning multiple pull requests; a Phase is one coherent, independently mergeable pull-request-sized outcome; and a Task is one independently verifiable, commit-sized implementation unit.

- Provider mapping: An adapter maps the portable hierarchy to the provider's native work-item model and preserves identity, ordering, dependencies, and parent-child relationships through native hierarchy, links, fields, labels, or metadata.

- Progressive milestone planning: For a large effort, fully elaborate only the next immediate milestone into phases and tasks. Do not create speculative implementation detail for later milestones.

- Future milestones: Record each future milestone's intended outcome, scope boundary, dependencies, high-level exit criteria, known risks, and exactly one task named “Plan Out <milestone name>.” When that milestone becomes immediate, reload the current design, repository, completed work, and provider state; then replace the planning placeholder with current phases and tasks.

- Milestone trigger: Consider milestone decomposition when any two conditions apply: more than six anticipated phases, more than roughly 25 anticipated tasks, three or more major subsystems, multiple independently shippable capabilities, strong dependence on discoveries from earlier implementation, or separate rollout, migration, or validation gates.

- Phase sizing: A phase should deliver one mergeable reviewer-visible outcome, normally contain two to seven tasks, change roughly 150–800 substantive lines across no more than about 15 implementation files, require approximately 30–60 minutes of focused review, and cross no more than one major architectural or migration boundary.

- Task sizing: A task should produce one independently understandable, testable, and revertible change mapped to an acceptance criterion. It should normally touch one to five closely related implementation files, change roughly 25–250 substantive lines, require approximately 5–15 minutes of focused review, and include explicit verification. Generated output, lockfiles, snapshots, fixtures, and mechanical formatting do not count toward these size ranges.

- Sizing exceptions: If a task or phase exceeds two guardrails, split it unless doing so would create an invalid intermediate state. Record a concise rationale for every indivisible exception.

- Plan Context: Always create or refresh a loadable context containing the planning authority, stable plan and work-item references, active milestone, active phases and tasks, dependencies, ordering, acceptance criteria, verification requirements, status, relevant design decisions, and a bounded summary of future milestones. Mutable external status must be refreshed from the authoritative provider.

- Write behavior: Preview proposed external work-item mutations by default. Apply them without another confirmation only when the invocation explicitly authorizes creation or updates in the configured planning system.

- Boundary: Structure implementation work without implementing it or silently reopening approved product decisions. Return material ambiguities that prevent responsible decomposition to the user or Propose.

- Typical dependencies: approved design proposal, repository architecture and coding-conventions context, planning and verification policies, provider adapter, Plan Context schema, and optional architecture or security review.

## Load the planning context first

Resolve the project's planning authority, target identifiers, native hierarchy, and output preferences from selected project context. If absent, ask for the authority before publishing. Planning integrations use the host's available connectors or CLI; do not assume a tracker is connected. Load `references/template.plan-context/plan-context.md` and validate the portable context before publication. Future milestones have exactly one planning task and no implementation phases. Refresh tracker state before implementing a referenced task.

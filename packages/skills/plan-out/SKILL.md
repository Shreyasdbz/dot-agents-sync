---
name: plan-out
description: "Break an approved design into reviewable work and a loadable Plan Context in the project's planning authority. Do not implement it."
---

# Plan Out

Translate an approved design into executable work without reopening settled product decisions. Read relevant repository state, completed work, and selected planning-authority context first. Use existing domain terms and work-item IDs.

## Decompose

Use Plan → Milestone → Phase → Task. A milestone delivers a major outcome; a phase is an independently mergeable PR; a task is an independently verifiable commit-sized change. Prefer phases that exercise a thin usable path through the affected system, with tests alongside behavior. For migrations or wide refactors, sequence compatible expansion, migration and removal; document any intermediate state that cannot stand alone.

For large efforts, elaborate only the next milestone. Each later milestone retains outcome, boundaries, dependencies, risks and exit criteria, plus exactly one task: “Plan Out <milestone>.” Re-plan that milestone from current evidence when it becomes immediate. Small changes need no artificial multi-milestone hierarchy; use one immediate milestone in the portable context.

Load [sizing.md](sizing.md) for decomposition thresholds and PR/commit guardrails. Scope follows coherent behavior, not filling a line-count quota.

## Reconcile and deliver

Load [plan-context.md](references/template.plan-context/plan-context.md) to produce the machine-loadable Plan Context and any requested human view. Preserve one writable authority; Markdown/HTML projections do not become competing trackers. Map the logical hierarchy to verified native types and relationships, not assumed product terminology.

When a tracker is unavailable, produce an explicitly unrefreshed draft with portable IDs and unresolved external references. Preserve known work such as an in-progress task; do not invent tracker IDs, claim refreshed status, or block useful offline decomposition merely because publication is unavailable.

Before authorized publication, refresh existing items, match by stable identity, and preview creates/updates/relationships. If a write times out, inspect the tracker before retrying to avoid duplicates. Record returned IDs and partial completion; do not claim an atomic tracker transaction.

Finish with a validated loadable context, dependencies that actually gate work, acceptance and verification for immediate tasks, and a concise summary of proposed or confirmed tracker changes. Do not implement the work or publish without authority.

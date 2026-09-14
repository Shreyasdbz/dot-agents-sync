# Plan Context

Record one authority (local, github, ado, linear, jira or notion), its stable project reference, design references and active milestone ID.

For each milestone record its ID, outcome, dependencies, exit criteria and status. Only the immediate milestone contains phases and implementation tasks. Each future milestone contains exactly one planning task to elaborate it later.

Each phase records a reviewer-visible outcome, acceptance criteria, ordering, integration and rollback posture. Each task records outcome, scope, likely code locations, acceptance criteria, verification, dependencies, authoritative reference and commit boundary.

Refresh mutable tracker status before use. Markdown/HTML projections are read-only when a tracker is authoritative. Do not duplicate private context bytes. Use `dasync schema plan-context --json` for the machine-readable contract.

## Tracker mapping

Load the project's configured issue types and relationship fields. Map milestone, phase and task to their actual equivalents; do not assume a universal Epic/Feature/Task hierarchy. When a level is absent, preserve it with explicit parent links or stable metadata. Reuse work-item IDs on revisions and update existing items rather than duplicating them.

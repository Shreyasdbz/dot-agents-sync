# Plan Context

Load [adaptation.md](adaptation.md) only when choosing a bug-fix, feature, migration, greenfield or offline planning shape. The schema below remains authoritative.

Produce a JSON or YAML mapping using `dasync schema plan-context --json`. Validate it with `dasync validate plan-context --path FILE --json` before claiming it is machine-loadable. If the command is unavailable, check the schema when supplied and label validation unperformed; do not invent a successful check. A human-readable overview may accompany, not replace, this context unless explicitly requested otherwise.

Use portable IDs such as `mvp`, `import-flow`, and `parse-csv`: lowercase letters, digits, hyphens and optional dotted segments, starting with a letter. Put tracker keys/URLs in `reference`, not `id`. Unknown references can use `unresolved:project` or `draft:inventory`; label `authority_state: unavailable`. Array order is presentation order; `dependencies` identify actual blockers.

Required root fields: `version: 1`, `authority` (local/github/ado/linear/jira/notion), `reference`, `active_milestone`, and `milestones`. Use `design_references` when available and `authority_state` to distinguish current, snapshot and unavailable tracker evidence.

Every milestone has `id`, `outcome`, `status` (active/future/complete), `exit_criteria` and `dependencies`. Optional `scope`, `risks` and `reference` retain important boundaries. Exactly one milestone is active; it has `phases`. A future milestone has one `planning_task` with `id` and `outcome`, and no phases.

Every phase has `id`, `outcome` and nonempty `tasks`. Optional `reference`, `dependencies`, `acceptance` and `rollback` describe the PR boundary. Every task has `id`, `outcome`, `acceptance` and `verification`; use optional `scope`, `reference`, `dependencies`, `status`, `human_input` and `sizing_exception` when useful. IDs are globally unique. Task status may be planned, in-progress, blocked, complete or unknown. Dependencies must be acyclic; a task cannot depend on completion of its own parent phase.

Map logical levels to the project's actual tracker types and relationship fields. Reuse existing items, preserve status with provenance, and refresh before writing. The tracker remains authoritative; this document is a loadable projection. Include no private context bytes.

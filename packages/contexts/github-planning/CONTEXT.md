# GitHub planning model

Public provider-specific reference for policy.github-planning; not a binding to an actual board and not authorization to mutate GitHub. Load for planning/scoping in an adopting monorepo. Use Plan Out's sizing.md for PR/commit thresholds; this reference maps that logical model rather than redefining it.

## Discover the actual project

Record owner/repository, Project URL and ID, permissions, issue-type IDs, milestone IDs, Project field/option IDs, available sub-issue and blocking relationships, existing label vocabulary and automation behavior. Reuse context.planning-authority if authorized, or ask for missing identities. Check the installed GitHub CLI help or connector capabilities; use supported native operations or documented APIs, not invented flags or legacy Project-column endpoints.

GitHub Projects supplies the board/table/roadmap views; repository issues hold work descriptions and milestones group repository work. Native issue types are organization-managed and can be renamed or disabled. Do not assume a personal repository or every organization offers the requested types. Missing native types require an explicit user decision, not a silent type-label fallback or unauthorized organization change.

## Hierarchy without fake work

| Logical role | GitHub representation |
| --- | --- |
| Whole monorepo plan | One designated Project with views, linked issues and repository milestones |
| Major outcome / milestone | Native repository milestone with outcome, boundaries, dependencies and exit criteria |
| User-facing capability | Feature issue; may span several PR phases |
| Observed defect | Bug issue; use evidence and reproduction rather than speculative diagnosis |
| PR-sized phase | Logical PR grouping; a phase Task for feature work is a direct sub-issue of the Feature |
| Commit-sized work | Feature work: Task directly under the Feature, with phase grouping in the plan/body; other work may use its phase parent |
| Future milestone | One Task named Plan Out <milestone>, assigned to that milestone; no implementation tree yet |

Type describes the work, not its depth in the tree. Technical maintenance can be Task at the PR boundary; do not call it Feature merely because it has children. A tiny change may reuse one issue for both logical phase and task references instead of creating a redundant parent. Each distinct native issue appears once on the Project; the same URL may appear at multiple logical levels in the portable Plan Context.

Use native parent/sub-issue links for decomposition and blocking relationships for actual dependencies; a checklist is not a substitute for independently tracked tasks. Assign the milestone and Project membership to each relevant issue; do not assume children inherit either. Do not create separate milestone tracking issues merely to get a board card.

Every feature implementation Task links directly to its owning native Feature issue as parent, including commit-sized tasks in a multi-PR feature. Verify the parent's native type, not its title or labels. Preserve logical Phase → Task grouping in Plan Context and record the phase reference in the Task body; do not introduce a Task parent that breaks direct Feature ownership. A body backlink is useful navigation but does not replace the native relationship. Standalone maintenance, Bug work and future-milestone planning Tasks need no invented Feature parent. If the owning Feature is missing, propose creating or identifying it before task publication; reconcile existing parents with explicit approval rather than silently moving work.

Only the immediate milestone receives detailed work. Later milestones retain boundaries and exit criteria in their descriptions and one planning Task each. When a milestone becomes immediate, refresh real state, expand its work, and close its planning Task only after the approved plan is actually reconciled. Never duplicate or discard existing work to satisfy a newly loaded convention.

## Metadata contract

Titles name a concrete outcome or observable defect, without slogans, status/type prefixes or emoji decoration. Reuse existing vocabulary; do not encode changing priority or state in titles.

Use native Type, Milestone and Assignees. Use the Project's actual Status field for workflow, its Priority field if configured, and existing estimate fields only with stated uncertainty. Do not duplicate those values as labels. Do not invent owners, deadlines or estimates to fill empty fields. Discover existing automation before editing status; issue closure and Project status can diverge.

Labels describe stable facets: use the repository's established vocabulary first. For a new taxonomy, propose area:<app-or-domain> and only useful cross-cutting risk labels such as security or migration. New labels require approval. Avoid one-off labels, one label per task, or redundant type:bug/status:done/priority:* labels when native fields own those meanings. Record actual blockers as relationships plus a short reason; use a blocked field/label only if it is the configured convention.

For new boards, propose Backlog, Ready, In progress, In review and Done; do not install this workflow without approval. Ready requires a clear outcome, acceptance, verification, scoped dependencies and resolved blocking decisions. Done requires acceptance evidence, not just a closed PR or an AI completion claim. Preserve existing automation and human status updates.

## Descriptions and publication

Load [issue-bodies.md](issue-bodies.md) for the selected issue type and milestone recipe. Keep the approved design linked rather than copied into every task. Write one logical source line per prose paragraph; retain meaningful structural breaks.

Before publication, preview identities, changes, type, milestone, Project membership, parent/blocking relations and selected metadata. Reconcile by stable ID/URL, with title search only as a candidate match. Concurrent changes require refresh; an uncertain create requires lookup before retry. Report each created/updated item and unresolved operation; GitHub writes are not an atomic transaction.

Return Plan Context with authority github, the Project URL, native milestone/issue URLs in reference fields and portable IDs unchanged. Future planning Tasks also retain their native reference. Mark offline state unavailable or snapshot as appropriate, retain known statuses and explicitly distinguish a draft from published work. Do not promise Projects creation or synchronization through dasync itself.

## Sources

Provider facts checked 2026-09-14; recheck capabilities before writes.

- [Projects and views](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- [Native issue types](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-types-in-an-organization)
- [Repository milestones](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones)
- [Sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues)

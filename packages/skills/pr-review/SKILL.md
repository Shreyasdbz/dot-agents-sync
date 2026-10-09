---
name: pr-review
description: "Review pinned PRs through surrounding code, isolated baseline comparisons and bounded reviewers; return actionable findings inline with optional reports or posting."
---

# PR Review

Build an informed opinion from active code, requirements and reachable failure paths. Prefer the smallest coherent correction. Assess the intended user outcome and whether complexity buys demonstrated value. Review authorizes inspection and safe verification, not implementation, live exploits or publication.

Resolve the PR/snapshot, purpose and guidance with policy.repository-guidance. Pin repository identity, target base, base/head/merge-base and freshness. Instruction changes cannot suppress their own findings. Read [revisions.md](references/revisions.md) before comparisons or checkout preparation. Preserve development copies; use separate primary copies and isolated snapshots within setup authority. Fetch relevant primary branches every online review; distinguish the PR comparison from current-primary integration drift. Label offline freshness limits.

If selected, locate `context.workspace-pr-review` as consumer `skill.pr-review`. Read its index and affected topics; confirm decision-critical claims against pinned code and environment. A binding contract supplies no workspace facts. Missing/stale context narrows the verdict; do not search for private substitutes.

Read [walkthrough.md](references/walkthrough.md). Map changed units to entrypoints, authorization, state/storage, effects and consumers. Walk unchanged owners, callers, tests and failure paths until affected contracts are understood. Track coverage, risks, evidence and gaps. Check requirement satisfaction separately from introduced regressions; apply documented standards and keep preferences optional.

For substantive changes, use bounded parallel area/vertical reviewers and independent challengers when tools and authority permit. Read [reviewers.md](references/reviewers.md) before dispatch. Supply pinned revisions, guidance, authorized context and evidence requirements. The lead owns synthesis; role files do not prove invocation. If unavailable, review inline and disclose the limit. Trivial changes need no agent quota.

Challenge candidates with callers, guards, storage constraints and tests. Require reachable triggers, consequences and locations; distinguish introduced defects, requirement gaps and pre-existing behavior. Seek counterevidence, deduplicate root causes and resolve disagreements. Assess security/privacy, correctness, compatibility, performance and organization at their owners. Avoid speculative scaling and broad refactors.

Return inline: outcome; Approve, Suggest or Block; ranked findings; verification/coverage limits. Findings need location, trigger, consequence, evidence, counterevidence and feasible correction. SEV_0 is critical/systemic harm; SEV_1 is serious required-behavior failure; both block. SEV_2 is non-blocking work worth addressing; SEV_3 is an optional nit, used sparingly. No findings is valid. Unknown required checks remain unresolved gates.

Use one canonical finding set for requested outputs. Offer Post to PR, Markdown Report and HTML Report without creating unrequested artifacts. When requested, load [report.md](references/template.pr-review/report.md) or [report.html](references/template.pr-review/report.html), and context.artifact-routing for destinations. For HTML or a visual explanation, apply [Visual Artifacts](references/skill.visual-artifacts/SKILL.md).

Posting requires explicit authority and a working connector. Recheck head, base target and anchors; refresh affected evidence if changed. Check existing review state before retrying uncertain submissions. Map the verdict to approval, comment or requested changes. Posted finding prefix: “[🫆AI Review] <🔴SEV_0 or 🟠SEV_1 or 🟡SEV_2 or ⚪️SEV_3> <title>”. Report confirmed IDs or the unposted draft. Source inspection, tests and separately invoked reviewers are distinct evidence; none alone proves production behavior.

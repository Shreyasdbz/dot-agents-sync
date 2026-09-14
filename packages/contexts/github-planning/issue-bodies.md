# GitHub description recipes

Select only the recipe matching the work. Replace instructions with concrete project content; omit irrelevant sections, not necessary acceptance evidence. No filler paragraphs, empty headings, fixed-width prose wrapping or duplicated design documents. Respect existing repository issue forms and preserve user-authored content.

## Milestone

State the outcome and users/systems affected, included/excluded scope, dependencies and risks, and objectively observable exit criteria. Add dates only if actually agreed. For a future milestone, link its sole planning Task rather than listing speculative implementation work. A percentage of closed issues is not evidence that exit criteria passed.

## Feature

State the user/system problem and intended capability, scope and non-goals, links to approved decisions, acceptance checks and rollout/compatibility constraints. Link actual phase/task sub-issues and real dependencies. Keep unsettled decisions explicit. A one-PR feature does not need a duplicate phase wrapper.

## Task

State one concrete outcome, relevant code or contract references, in-scope and excluded work, acceptance checks, and verification commands or observable checks. Include dependency links and necessary human input. For feature work, identify the owning Feature URL and set that native Feature issue as the Task's direct parent; body text alone is insufficient. For a phase Task, state its mergeable PR boundary and link grouped tasks; feature tasks remain siblings under the Feature, not children of the phase Task. For a commit Task, keep checks local to that change and identify its logical PR phase. Record sizing exceptions only when Plan Out's thresholds warrant them.

## Bug

Describe expected versus observed behavior, impact, reproduction or failing test, affected version/environment, and sanitized evidence. Distinguish confirmed cause from hypotheses. Specify the regression acceptance check and fix boundary; add rollout/recovery concerns when relevant. Never invent a root cause to make the issue feel complete. Security-sensitive evidence belongs in the approved private reporting channel, not a public issue.

## Plan Out future milestone

Outcome: an approved, reconciled plan for the named milestone based on current repository and tracker state. Link its milestone and preceding gates. Acceptance: refresh decisions and completed work; decompose only this now-immediate milestone using Plan Out; preserve existing identities; validate the loadable Plan Context; publish only if authorized and verify returned relationships. This is a planning Task, not authorization to implement or prematurely expand later milestones.

## Example task body shape

Use these section roles when applicable, with actual content rather than placeholder text:

- Outcome: the observable change.
- Scope: affected boundary and explicit exclusions.
- Acceptance: checkable behavior, including important failure cases.
- Verification: exact project checks and required evidence.
- Dependencies: native links and why they block.
- References: approved design and relevant source contracts.

When editing an existing issue, merge only the authorized sections. Do not overwrite human notes, evidence, assignees or status as incidental formatting cleanup.

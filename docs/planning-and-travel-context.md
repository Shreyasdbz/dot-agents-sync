# GitHub planning and travel context

## GitHub planning

Select the optional planning-github profile for a monorepo that adopts GitHub as its planning authority. It installs Plan Out, policy.github-planning and the public context.github-planning reference with issue-body recipes. Loading the reference alone supplies guidance; selecting the policy makes the authority requirement operative. No board, issue, label or automation is created by installation.

Use one designated GitHub Project for the monorepo. Repository milestones describe major outcomes; native Feature, Task and Bug types classify issues. Every Task implementing a Feature has that native Feature issue as its direct parent, including commit-sized tasks across multiple PR phases. Keep PR-phase grouping in Plan Context and body references rather than an intermediate Task parent. Body links and labels do not replace the native relationship. Standalone maintenance, Bug work and future-milestone planning Tasks need no artificial Feature. Future milestones get one planning Task each and no premature implementation tree.

Actual repository/Project IDs, type/field IDs, status conventions and permissions belong in authorized planning-authority context or supplied project instructions. If native types are unavailable, ask for a decision; do not substitute labels or change organization settings silently. The reference defines description content, native metadata ownership, conservative label conventions and publication reconciliation. GitHub remains writable authority; Plan Context is a validated, dated projection. No GitHub integration or account was exercised during authoring.

## Natural Markdown

policy.communication now explicitly forbids fixed-width hard wrapping of prose. Every catalog skill and agent requires it, so the rule accompanies both standalone roles and workflow selections. Lists, tables, code and intentional line breaks retain their semantics. This is an instruction for generated/edited prose, not a formatter that rewrites unrelated files.

## Travel responsibilities

The travel profile selects agent.travel-planner and skill.trip-publish. Travel Planner owns itinerary planning and bounded content review; Travel Researcher remains an optional specialist for a narrow question. Trip Publish consults the planner before authoring the approved page. Where delegation is unavailable or prohibited, the caller applies the role inline and discloses that no separate agent ran. Native agent roles remain read-only; the publishing skill writes the artifact.

skill.trip-plan remains a small compatibility entrypoint requiring Travel Planner, not a second copy of planning logic. Existing selections continue resolving. New selections should use the agent or travel profile. No existing installed user configuration is modified by these catalog edits.

context.travel-preferences remains a separately selected private binding, not a required dependency. The user's supplied preferences were authored in the gitignored local-contexts/travel-preferences.md file, outside catalog packaging. It is not automatically bound or available in another clone. Do not force-add it or include it in public reports. Move/copy it to an approved private location if long-term private storage is wanted; binding requires the normal explicit user/project/provider grants described in README.md.

No personal program memberships or companion preferences are embedded in public agent instructions. Public guidance covers points/cash comparison, party-specific dietary constraints, budgeting and uncertainty; personal facts stay in the private source. Pass only necessary authorized constraints during delegation and exclude raw preference text, identifiers and reservation secrets from shareable output.

## Validation limits

Tests cover profile resolution, optional private-context gates, native agent reference paths, compatibility selection and schema-valid GitHub projections. Behavioral cases are prompts for future recorded model runs, not proof that a hosted model follows the guidance. GitHub facts were checked against the linked official sources in context.github-planning on 2026-09-14; current permissions and capabilities still require inspection for each real project.

Local verification on 2026-09-14: the full suite passed 105 tests, including 11 planning/travel checks. Ruff lint/format checks, generated-template parity, Markdown diff whitespace checks and the skill validator for Plan Out, Trip Plan and Trip Publish passed. The personal context path is gitignored and untracked. No hosted-agent behavioral evaluation, GitHub mutation, travel transaction or real user configuration installation was performed.

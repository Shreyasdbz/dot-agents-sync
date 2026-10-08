---
name: explain-changes
description: "Explain a PR, diff or current-session effort as one scrollable, self-contained visual HTML document, with source-backed before/after behavior and relevant engineering and product perspectives."
---

# Explain Changes

Create one scrollable HTML file that teaches what changes, why it matters and how it works. Cover the material scope, then explain consequential mechanisms in depth with concise prose and substantial visuals. This is an explanation, not an approval verdict; it does not authorize code changes, live tests, tracker writes, messages or publication.

## Establish scope and evidence

Resolve the PR, diff, local changes or session effort. Preserve accepted intent and constraints; ask only about material target, comparison or destination ambiguity. Default to a mixed technical/product audience, with technical depth below clear explanations. Read [evidence.md](evidence.md) before analysis.

Apply policy.repository-guidance to each relevant repository. Record immutable revisions or fingerprints for local/supplied evidence. Distinguish committed, staged, unstaged, untracked, proposed and completed work. Trace beyond changed lines into owners, callers, contracts, tests, configuration and cited docs. Map every material change to an explanation or an explicit evidence gap. Recheck inputs before delivery.

For a workspace, read [workspace.md](workspace.md). Inspect a selected context index first and load relevant authorized topics. If `context.workspace-explain-changes` is selected, locate it with consumer `skill.explain-changes`. Use selected workspace branding through skill.visual-artifacts. Search available authorized repositories and connected docs/trackers for relevant contracts and intent; report missing sources. Workspace specifics stay in private bindings, not this public skill.

## Analyze and synthesize

Read [perspectives.md](perspectives.md). Examine architecture/scaling, performance, security/privacy, reliability/observability, AI/LLM behavior, coding contracts, product and UX where applicable. Explain how their conclusions affect the same concrete change; avoid separate repetitive reviewer essays. Mark irrelevant lenses briefly in coverage, with a reason. Preserve conflicting evidence and meaningful tradeoffs.

Use independent agents only when authorized and available, with bounded briefs; otherwise apply lenses inline. State which occurred. Agreement and tests do not establish production outcomes. Separate recommendations and unresolved risks from implemented behavior.

## Compose the explanation

Read [language.md](language.md) and template.explain-changes's components.md and explanation.html. Apply ASD-STE100 writing guidance while preserving exact technical meaning and identifiers. State the language verification limit when the official rules/dictionary were not checked.

Use skill.visual-artifacts. Build a readable overview, a before/after map, connected mechanism walkthroughs, consequences, verification limits and a source/glossary appendix. Adapt sections to the actual effort. Give each major mechanism a meaningful diagram, aligned comparison, sequence, annotated UI or state/data view plus equivalent text. Show failure/recovery paths when relevant. Explain endpoints, edge labels, ownership, conditions and uncertainty. Do not invent benchmarks, product goals or outcomes.

Keep the main explanation and material caveats visible; put secondary code and source detail in labeled disclosures. Use normal page scrolling and anchor navigation. Inline all CSS, JavaScript and necessary assets; preserve full reading without JavaScript and in print. Escape source text and validate links. No remote dependencies, telemetry or hidden private data.

## Verify and deliver

Use context.artifact-routing, default kind `explanations/`. Audit grounding, coverage, language, links, sample residue and sensitive content. Exercise anchors, disclosures, themes, keyboard, reflow/zoom, reduced motion, no-JavaScript and print when possible. Deliver the file, snapshot, actual checks and limits; do not claim exhaustive context or certified STE compliance without evidence.

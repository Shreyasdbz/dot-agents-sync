---
name: visual-artifacts
description: "Create visual explanations, diagrams and interactive HTML artifacts; improve composition and motion in requested decks, reports and interfaces. Keep simple answers inline."
---

# Visual Artifacts

Make a relationship, mechanism or decision easier to understand. Use for visual explanations and as the visual craft workflow inside requested HTML artifacts. Preserve the parent workflow's scope, evidence, destination and format; this skill does not authorize a new report, app, publication or account change.

## Choose the view

Read the actual source and identify the audience's question and the relationship that answers it. Choose the smallest complete view: pseudocode for logic, a call/component/file tree for ownership or order, a diff for a change, a table for comparable criteria, Mermaid for a compact static graph, or focused HTML/SVG for spatial composition, linked states or interactive exploration. Show the whole target shape when omissions would obscure responsibility or order. A simple answer can stay inline; a deck is not the default explanation format.

Keep visuals beside the short explanation they support. Use actual names, values, units and boundaries. Distinguish observed behavior, proposed behavior, estimates and unknowns visibly. Do not invent measurements, geography or causal relationships to complete a picture. Read [diagrams.md](diagrams.md) when a diagram or chart carries the explanation.

## Compose deliberately

Inspect the existing visual system and selected design context. Preserve explicit brand and preset choices. Otherwise derive a coherent direction from the subject and audience: type roles, palette roles, spacing, density, diagram grammar and the dominant visual. Make these choices briefly before coding; do not turn them into a separate deliverable. Read [composition.md](composition.md) for HTML and authorized workspace branding.

Build with real content. Give each scene one dominant relationship and a clear reading order; vary composition with its purpose. Use typography, alignment, scale and negative space to establish hierarchy. Avoid interchangeable card grids, decorative metrics, repeated heroes and diagrams that merely put prose in boxes. Sparse and dense views are both valid when their structure earns the space.

## Explain change with interaction

Use interaction when it answers a real question: inspect a step, compare states, isolate a path or change a sourced parameter. Label controls by the action and show the resulting state in words. Keep the conclusion, evidence and critical caveats available without interaction. An illustrative simulation must name its assumptions and cannot imply measured or live behavior.

Read [motion.md](motion.md) when implementing animation or transitions. Choreograph the meaningful change: preserve identity, direct attention to what moved or changed, and stop when the change is understood. Manual stepping, replay and pause belong to temporal explanations. Reduced motion, no JavaScript and print need a complete static explanation, not an empty canvas.

## Inspect and deliver

Render the actual artifact when tools permit; inspect the important views and exercise pointer and keyboard controls. Check narrow/wide layouts, zoom, long labels, both supported themes, reduced motion, no-JavaScript fallback and print. Look for crossed or detached edges, unreadable labels, misleading scales, weak hierarchy, clipping and controls that do nothing. Revise the observed problems before delivery. Static checks, screenshots and executed interactions are distinct evidence; report unavailable checks precisely.

For HTML, use semantic HTML/CSS with inline SVG and small local JavaScript unless the existing project needs its framework. Prefer one offline file without CDN assets, trackers or unnecessary libraries. Escape untrusted text and validate links; collapsed content and scripts still disclose their contents. Remove sample facts and authoring instructions. Load context.artifact-routing for requested files, then open or preview the result through the host's supported artifact tools and provide its actual path. Inline results stay inline.

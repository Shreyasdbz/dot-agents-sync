# Diagrams that explain relationships

Start with the question and trace a concrete example through the actual source. Name entities, relationship verbs, direction, ownership boundaries and the important exception path before drawing. Do not imply synchronous order from a dependency graph or causality from a correlation.

| Relationship | Representation | Required meaning |
| --- | --- | --- |
| Logic or runtime order | Pseudocode, call tree or sequence | Branches, caller/callee and actual ordering |
| Ownership or containment | Component/file tree, nested regions or lanes | Owner and boundary; containment is not a call |
| Data movement | Directed flow | Producer, consumer, payload and return/error path |
| State change | State graph or manually stepped scene | Trigger, before/after state and terminal/recovery states |
| Data model | Entity relationships | Keys, cardinality and optionality |
| Comparison | Table or aligned small multiples | Same criteria, baseline, units and scale |
| Quantitative change | Appropriate chart plus values | Denominator, period, source and uncertainty |

Use Mermaid for compact static software relationships that render clearly in the host. Use purpose-built inline SVG/HTML when spatial hierarchy, annotation or interaction materially improves comprehension. Prefer text trees for shallow structure. Never add a diagram merely to decorate a report.

## Draw with a grammar

Lay out the primary path in a consistent direction. Group by responsibility, align nodes and give labels room. Route connectors between real endpoints with labeled arrows; use return edges or separate lanes for recovery rather than ambiguous bidirectional lines. Avoid crossings and edges through text. Numbering means temporal order, not importance. Dashed lines need a visible legend and cannot silently mean both optionality and uncertainty.

Use inline SVG for precise geometry with a viewBox, unique title/description IDs and an equivalent visible caption or relationship list. Use semantic HTML for rich labels and responsive node layouts. Keep wide graphics readable through a named keyboard-scrollable region or a deliberate mobile layout. Do not shrink labels to satisfy a screenshot. A graph with all facts in text can be decorative to assistive technology; a graphic carrying unique meaning needs an accessible name and equivalent description.

Preserve entity identity across before/after and sequence views: same label, position and visual encoding unless movement itself has meaning. For a worked failure path, show the last confirmed state, the uncertain result and the recovery condition. Keep observed behavior separate from proposed contracts. Highlight selected paths with a label or shape as well as color.

## Quantitative integrity

Derive graphics and visible values from one data source. Keep units, denominators, periods and sources visible; distinguish measured values, targets, estimates and scenarios. Bar length starts at zero unless an explicitly explained alternative is necessary; small multiples share a scale. Do not animate counters from invented intermediate values. An uncertainty band or range needs sourced bounds. Provide a data table or text equivalent, and never rely on hover alone for a value.

Inspect the rendered graph for label collisions, detached endpoints, misleading directions, unreadable legends and false visual emphasis. Exercise any path selector and verify that its accompanying explanation matches. Check long labels, narrow layout, both supported themes and print; a valid SVG or Mermaid parse proves syntax, not explanatory quality.

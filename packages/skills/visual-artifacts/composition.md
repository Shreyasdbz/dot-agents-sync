# Composition for visual artifacts

Design from the content rather than applying the same aesthetic to every subject. An engineering explanation may need a precise schematic; a product pitch may need a large annotated product view; an evidence review may need aligned comparisons. An established design system or supplied reference takes precedence.

Before building, identify the dominant visual, reading order and a few tokens: canvas/surface/ink/muted/accent/semantic colors, display/body/code type roles, spacing and container widths. Give accent a meaning. Keep semantic colors stable across scenes and pair them with words or symbols. Use a small coherent type system, deliberate line lengths and tabular numerals for aligned quantities; do not require external fonts for an offline artifact.

## Choose a composition by its job

| Audience question | Useful composition | Avoid |
| --- | --- | --- |
| What is the claim and why believe it? | Claim beside one dominant evidence graphic and its source | A large number without denominator or context |
| What changes? | Before/after with aligned entities, criteria and a highlighted delta | Unrelated screenshots or incompatible chart scales |
| How does this work? | Mechanism diagram beside a concrete worked example | A row of feature cards |
| Where does responsibility change? | Lanes or containment with labeled boundary crossings | Floating boxes with no edge semantics |
| Which option fits? | Shared criteria in a table or aligned small multiples | Invented scores or one attractive favored option |
| What happens over time? | State sequence with persistent actors and step controls | A decorative animated timeline |
| What must I inspect together? | Grouped code, contracts and evidence with cross-references | Tiny type to fit a fixed slide canvas |

One dominant relationship per scene does not mean one fact per page. Place necessary caveats near the claim. Let detail remain visible when it changes the interpretation. Use labeled disclosures for secondary evidence, not the answer. Preserve a natural reading order when columns stack.

Use hierarchy rather than containers around every fragment: aligned columns, type contrast, proximity and fine rules. Reserve strong surfaces, color and scale for what merits attention. Vary slide layouts because their relationships differ; variation alone is not a reason. Match icon stroke/weight and use a consistent diagram grammar. A memorable visual should come from the subject, not a stock gradient or gratuitous effect.

## Build and critique

Start with the semantic content and working controls, then refine composition in the browser. Use a generous readable desktop view and a narrow reflow; do not scale the whole canvas down to mobile. Dense diagrams can use a named scroll region with a complete adjacent explanation; keep essential labels readable. Responsive SVG alone does not guarantee readable text.

Review a real capture of each materially different layout. Ask whether the viewer can find the claim, follow the relationship and identify uncertainty without presenter coaching. Fix misplaced emphasis, accidental gaps, weak contrast, awkward wrapping, repeated layouts and crowded diagrams. Check focus visibility, control names, content at zoom and print pagination separately from appearance.

## Inspiration and provenance

These instructions are original guidance informed by HumanLayer's [show-me](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md) (choosing a focused representation), Anthropic's [frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) (subject-specific composition and critique), and [web-artifacts-builder](https://github.com/anthropics/skills/blob/main/skills/web-artifacts-builder/SKILL.md) (portable HTML delivery), inspected 2026-09-30. They are advisory references, not copied runtime instructions. Do not inherit explicit-only invocation, mandatory framework scaffolding, dependency installation or optional verification from those sources. This catalog retains its own scope, accessibility and verification contracts.

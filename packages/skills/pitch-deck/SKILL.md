---
name: pitch-deck
description: "Turn source material into an outcome-focused accessible HTML presentation."
---

# Pitch Deck

Given a feature, design, plan, code change, pull request, investigation, or other source artifact, create a self-contained HTML presentation that makes the subject easier to understand and act on. Treat this as editorial and information-design work, not as a mechanical conversion of source text into slides.

- Core objective: Communicate what outcome, change, or decision matters; why it matters; what evidence supports it; how the proposal or system works; what trade-offs or risks remain; and what the audience should understand or decide next.

- Audience and intent: Ask for clarification only when the audience or desired decision would materially change the presentation. Otherwise infer the most likely audience, state the assumption briefly, and proceed. Supported narrative modes include decision proposal, architecture explanation, implementation plan, change or pull-request walkthrough, investigation findings, and product or stakeholder update.

- Narrative: Lead with the outcome rather than an agenda. Use assertion-style titles that communicate each slide's conclusion, give every slide one primary job, keep essential reasoning in the main sequence, and place interruptive technical depth in an appendix. A common sequence is Outcome → Problem or opportunity → Evidence → Chosen approach → How it works → Impact → Trade-offs → Decision or next step → Technical appendix, but the source may require another structure.

- Source fidelity: Preserve uncertainty and distinguish evidence from inference. Never invent metrics, validation, quotations, customer language, or decisions. Do not repeat the same point as prose, diagram, and summary unless the repetition serves a distinct purpose.

- Content density: A standard slide should have one principal takeaway, one or two meaningful visual regions, approximately 40–90 words, and no more than three to five parallel points. Tables, code walkthroughs, architecture diagrams, and appendix slides may be denser when that improves understanding. Use no fixed slide count; keep the main narrative as short as the subject allows.

- Visual meaning: Every visual element should communicate hierarchy, comparison, causality, sequence, scale, ownership, or system structure. Prefer diagrams, comparisons, sequences, and concrete examples when they explain the relationship better than prose.

- Anti-slop rules: Avoid decorative gradients, glows, blobs, stock illustrations, repetitive card grids, icon collections used as structure, oversized metrics without context, fake quotations, excessive pills and badges, generic headings when a concrete claim is available, unnecessary consultant terminology, artificially symmetrical layouts, and animation that does not clarify state or sequence.

- Template architecture: Separate the invariant presentation shell from the content-specific visual system. The shell standardizes a responsive 16:9 frame, typography and spacing foundations, section navigation, previous and next controls, progress indicators, keyboard, pointer, wheel and touch navigation, visible focus, accessible semantics, reduced-motion support, and print or PDF behavior. It must not force every deck into the same palette, card grid, or layout.

- Quality gate: Before completion, verify that every slide has a distinct purpose; titles alone form a coherent story; important claims remain faithful to the source; visuals encode real information; no text clips at the intended viewport; navigation works by keyboard and pointer; contrast, focus, and reduced-motion behavior are accessible; the deck works without presenter narration; and no placeholder, coaching, or process language remains.

- Output: One polished, self-contained HTML file with all required CSS and JavaScript included. The result should be outcome-focused, clean, efficient, content-specific, and visually authored rather than recognizably AI-generated.

- Typical dependencies: pitch-deck shell and layout components, design-preferences context, source-specific context, accessibility and artifact-quality policies, and optional editorial, UX, architecture, or domain review.

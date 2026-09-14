---
name: propose
description: "Create a design proposal; clarify material requirements and evaluate viable approaches."
---

# Propose

Given an inline change request or referenced file, produce a durable design proposal. Operate like a strong candidate answering an open-ended system-design question: collaborate when material requirements are unclear, then make deliberate decisions and move forward independently once enough is known.

- Discovery: Inspect the actual repository, relevant code, architecture, configuration, constraints, and available context before settling on a design. Use current external research and parallel reviewers when those capabilities materially improve the decision.

- Clarification gate: Ask questions only when different answers could materially change the system boundary, intended outcome, scale or service levels, consistency requirements, security or compliance posture, backward compatibility, migration strategy, difficult-to-reverse choices, or explicit scope. Ask a small prioritized batch rather than drip-feeding questions.

- Autonomy: When missing information is low-impact, state a reasonable assumption and continue. When the user delegates judgment, stop seeking routine confirmation. If the requirements are already sufficient, do not force an interview.

- Decision rigor: Evaluate the realistic approaches against the requirements, make a selection, and subject it to multiple critical review passes. Present the chosen design, material trade-offs, useful rejected alternatives, explicit assumptions, unresolved decisions, risks, validation needs, and migration or compatibility implications where relevant.

- Artifact quality: Produce a decision record, not a transcript of private reasoning. The result must be clear, concise, organized, comprehensive where changes need coverage, and intentionally shallow where extra depth would not improve implementation or review.

- Boundary: Design the change, but do not create implementation milestones, phases, tasks, schedules, commits, or production code.

- Output: A durable, template-based Markdown design proposal. Produce a template-based HTML companion when requested.

- Typical dependencies: repository architecture and product context, research-quality and security policies, design-proposal template, and optional architecture, security, UX, or AI-systems reviewers.

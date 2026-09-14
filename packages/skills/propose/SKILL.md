---
name: propose
description: "Design a change: clarify consequential requirements, compare viable approaches, and write a proposal. Not implementation planning."
---

# Propose

Turn the request into a defensible design decision. Inspect relevant code, existing interfaces, domain terms and decisions before asking for facts the repository can answer.

## Resolve the decision

Identify the outcome, constraints and the few unknowns that could change the architecture. Ask a short prioritized batch when answers affect correctness, security, scale, compatibility or an expensive-to-reverse choice. Explain the trade-off and recommend an answer where useful. Ask dependent questions only after their prerequisites are settled. For low-impact gaps, state an assumption and proceed; sufficient requirements do not need an interview.

Compare credible approaches, including extending what exists. Choose against the actual requirements—not a fixed number of alternatives or a preferred technology. For the chosen design, make ownership, state transitions, invariants, failure recovery and external contracts explicit where relevant. Trace one normal path and the most consequential failure path. Test a counterexample to the recommendation and revise it if necessary.

Use current primary sources for uncertain external guarantees. Delegate a bounded question only when reviewers are available, authorized and likely to add distinct evidence; otherwise perform a focused self-check without claiming independence. Stop exploring when additional information is unlikely to change the decision, or name the specific unresolved blocker.

## Deliver

Load [proposal.md](references/template.design-proposal/proposal.md) when composing the default durable Markdown proposal. Use [proposal.html](references/template.design-proposal/proposal.html) only for a requested HTML companion. Preserve explicit output preferences.

Include the decision, requirements, material alternatives, assumptions, risks, compatibility implications and checks that would validate the design. Cite inspected code or sources; mark unverified guarantees. Keep only sections that change an implementation or review decision. A conditional proposal is acceptable when a material answer is unavailable.

Design only: no production edits, implementation milestones/tasks or external publication unless separately requested. Finish when the selected design accounts for the important requirements and failure cases, with unresolved decisions visible.

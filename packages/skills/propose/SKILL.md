---
name: propose
description: "Design a change: clarify consequential requirements, compare viable approaches, and write a proposal. Not implementation planning."
---

# Propose

Design for the agreed outcome, acceptance criteria, non-goals and constraints.

## Discover before designing

For repository work, apply policy.repository-guidance to establish instruction scopes, selected context and available roles. Follow manifests, entrypoints, registrations and effective configuration to the active mechanism; do not design around stale context or an unused module. Trace input through ownership, state, external contracts and observable output. Inventory schemas and identity keys before proposing new state. Identify consumers, invariants and migration constraints; separate current behavior from approved direction.

Keep a compact boundary map with source pointers. Batch reads; widen discovery or inspect history only for a decision-changing gap. Missing documentation is not proof that no reusable mechanism exists.

Ask a short prioritized batch only for consequential facts that authorized evidence cannot answer: security requirements, workload, compatibility, operational ownership or expensive-to-reverse choices. Recommend an answer with its trade-off when useful; ask dependent questions after prerequisites settle. State reversible, low-impact assumptions and proceed. Never infer authority to spend, expose data or deploy from an architectural preference.

## Compare and challenge

Compare material alternatives against the same requirements: preserve current behavior when it suffices, configure or extend the existing mechanism, and introduce new components only for a demonstrated gap. Prefer the simplest viable option; extra state or components need a concrete benefit. Account for implementation and operating cost, failure modes, reversibility and maintenance, not just the happy path. Do not invent a fixed option quota or eliminate a credible alternative merely to justify a favorite stack.

For the recommendation, make ownership, state transitions, invariants, trust boundaries and external contracts explicit. Examine authorization and data isolation, invalid inputs, retry/idempotency semantics, partial failure and recovery where relevant. Trace the normal path and the most consequential failure path across actual boundaries; include migration, rollback and observability needed to operate the change.

Use observed or agreed volume, concurrency, latency and growth horizons for scale decisions. Identify the likely bottleneck and a measurement that could falsify the capacity assumption. Prefer established repository mechanisms and mature dependencies, but do not call an unmeasured design scalable or battle-tested.

Challenge the recommendation with the strongest plausible counterexample and strongest competing approach. Use read-only checks or explicitly authorized disposable spikes for pivotal feasibility questions; use current primary sources for uncertain external guarantees. Delegate only bounded questions that add distinct evidence. A self-check is not independent review.

Stop when material alternatives are rejected or bounded with evidence and further exploration would not change the choice. If a decision-changing unknown remains, make the recommendation conditional and name the evidence or human decision required; do not claim all possible solutions were exhausted.

## Deliver

Load [proposal.md](references/template.design-proposal/proposal.md) for the default durable Markdown proposal; use [proposal.html](references/template.design-proposal/proposal.html) only for a requested HTML companion. Preserve explicit output preferences.

Include the decision, material alternatives, inspected mechanism, constraints, assumptions, risks, compatibility and validation criteria. Cite sources and separate executed probes from proposed checks. Keep only decision-relevant sections; a design document does not establish security, performance or production readiness.

Design only: no production edits, implementation milestones/tasks or external publication unless separately requested.

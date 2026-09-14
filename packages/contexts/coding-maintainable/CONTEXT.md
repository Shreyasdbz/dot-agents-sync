# Maintainable coding preset

Optional preference profile, not a description of this repository or an enforced rule.

Optimizes change locality and clear ownership over maximum reuse. Favors small stable interfaces around substantial behavior, explicit boundary types, isolated external effects, and behavior tests that survive internal refactors. A new dependency or abstraction earns its maintenance cost through a current need, not a hypothetical future caller.

Accept local duplication when similar code has different reasons to change. Shared types, API contracts and external-call behavior need one authoritative owner rather than independently maintained copies. Reuse a focused schema/client at that boundary; do not build a generic framework merely to remove a few repeated lines. Generated types are derived artifacts, not competing sources of truth.

Design for observed requirements and explicitly planned use, not imaginary scale. A hobby project does not need distributed coordination, configurable extension points or multi-region architecture without a concrete requirement. This does not excuse reachable invalid inputs, authorization failures or data-loss paths: adversarial correctness is different from speculative capacity planning.

Build the smallest functional slice first, including prototypes. Confirm behavior and flows before investing in styling. Prefer browser-driven UI iteration: inspect the actual page, map organization and interactions, then refine layout, typography and relevant states. Unit tests should challenge assumptions; integration and end-to-end checks cover boundaries and complete paths. A small UI change does not automatically require a maintained browser test suite.

Keep unrelated cleanup out of the implementation PR, but capture it in the selected planning authority instead of dropping it. Distinguish an observed defect from maintainability debt and associate feature work with its actual owner. Existing project conventions and explicit requirements take precedence; operative constraints belong in policy.coding and policy.verification.

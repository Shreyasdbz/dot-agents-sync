# Maintainable coding preset

Optional preference profile, not a description of this repository or an enforced rule.

Optimizes change locality and clear ownership over maximum reuse. Favors small stable interfaces around substantial behavior, explicit boundary types, isolated external effects, and behavior tests that survive internal refactors. A new dependency or abstraction earns its maintenance cost through a current need, not a hypothetical future caller.

Useful when several designs satisfy the contract. Existing project conventions and explicit requirements take precedence; operative constraints belong in policy.coding.

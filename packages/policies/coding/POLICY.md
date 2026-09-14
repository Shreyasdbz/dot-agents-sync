# Coding quality

Follow observed repository conventions and language idioms. Prefer the smallest coherent implementation that meets the contract. Keep errors actionable, validate boundary inputs, and remove unreachable scaffolding. Split mechanical transformations from behavioral changes where that aids review.

Give components and modules one cohesive responsibility and a clear reason to change; separate presentation, orchestration and external effects where that improves comprehension. Keep state near its owner and avoid redundant synchronized state. Do not split files merely to meet a line count. Minimal footprint means low maintenance burden, not compressed code.

Document public functions, classes, types and interfaces with concise contract comments or docstrings: semantics, invariants, units, side effects and failure behavior where relevant. Do not repeat names or signatures in prose. Explain why consequential branches or non-obvious operations exist and what breaks without them. Preserve language conventions and generated/vendor code boundaries.

Before calling implementation done, inspect the final diff and affected boundaries for speculative abstractions, redundant wrappers, duplication, unused code, unnecessary dependencies, swallowed errors, misleading fallbacks, stale comments and filler text. Fix in-scope findings and verify changed behavior; report remaining blockers or verification gaps. This audit is required even without a specialist agent, but does not authorize delegation or unrelated cleanup. Static checks and self-review do not prove independent review or production behavior.

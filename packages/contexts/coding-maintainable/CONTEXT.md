# Maintainable coding preset

This is an optional starting convention, not a description of an existing repository.

Prefer explicit interfaces, cohesive modules, clear data ownership, typed boundary data, and errors that preserve useful context without exposing secrets. Keep IO at well-defined boundaries and separate deterministic transformations from external effects. Tests should describe observable behavior and include failure cases. Reuse the project's established library and formatting choices. Introduce a dependency only when its value exceeds maintenance and supply-chain cost. Small changes are easier to inspect; artificial fragmentation is not. Repository-specific conventions override this descriptive preset; binding constraints belong in policy.coding.

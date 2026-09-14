# Feature recipe

Use for a new user-visible capability or substantial extension.

## Outcome and boundaries

Name the user/job, current limitation, measurable success condition and explicit non-goals. Describe the principal journey plus empty, error, permission-denied and cancellation states when relevant. Identify accessibility and privacy requirements before choosing interactions.

## Contracts and chosen design

Describe responsibility boundaries, data ownership, interfaces, state transitions and invariants. Use one end-to-end normal path and the most consequential failure path. Define idempotency, concurrency, retries and ordering where the design depends on them. A diagram should explain a relationship that prose alone obscures.

## Alternatives and trade-offs

Compare credible approaches against the actual requirements, including extending existing behavior. State why the recommendation wins and which condition would change it. Avoid a fixed quota of alternatives or a technology catalog.

## Compatibility and validation

Identify existing consumers, data changes, rollout dependencies and rollback limits. Define observable acceptance evidence, including user journeys and integration behavior; a mock-only test cannot establish a real dependency contract. Separate proposed targets from measured baselines.

Optional supporting sections: domain vocabulary, API/data contract, accessibility, threat boundary, capacity assumptions, operational signals. Load the cross-cutting guide selectively. Finish the design decision before planning implementation work.

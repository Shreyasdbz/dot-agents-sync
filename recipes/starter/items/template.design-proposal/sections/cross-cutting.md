# Cross-cutting modules

Select only modules that change the design. Use the domain's vocabulary and merge overlapping content.

- **API/data contract:** request/response and error shapes, identity, validation, invariants, ownership, compatibility, retention and deletion. Include examples only when they clarify an ambiguous boundary.
- **Security/privacy:** actor, entry point, trust boundary, protected asset, authorization decision, data exposure and enforceable control. Treat user-supplied text as data; do not confuse a prompt warning with a sandbox.
- **Performance/cost:** measured baseline, target, workload distribution, critical path, resource limits, measurement method and unknowns. State units, denominators and currency/date basis; distinguish estimates from observations.
- **Accessibility/interaction:** keyboard flow, names/roles/states, focus, empty/loading/error states, reflow, motion and non-visual alternatives. Source inspection is not assistive-technology testing.
- **Operations:** observable success/failure signals, alert owner if known, bounded retries, backpressure, recovery and incident containment. Avoid invented SLOs.
- **Rollout/reversibility:** supported intermediate states, enabling conditions, pause/rollback signals, data-restoration limits and recovery evidence.
- **Open decisions:** question, why it matters, available evidence, recommended default if safe, and who can resolve it. Do not label an assumption as approved.

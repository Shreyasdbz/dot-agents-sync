# Perspectives on the same change

Use these questions to uncover consequences. They are lenses, not claims that experts reviewed the work. Select depth by reachable effects, uncertainty and audience need. Briefly record examined, not applicable, and unavailable areas; do not manufacture an impact for every row.

| Perspective | Trace and explain when relevant |
| --- | --- |
| Principal engineer: architecture and scaling | Ownership, shared contracts, state lifetime, compatibility, fan-out, backpressure, concurrency and resource limits. Follow the path at expected workload; mark workload assumptions. |
| Performance and cost | Work added/removed, queries, round trips, payloads, caching and invalidation, allocations, tail latency and paid calls. Separate operation counts from measured latency, throughput and spend. |
| Security and privacy | Entry trust, authentication/authorization, tenant isolation, input/path validation, executable content, dependencies, data collection, retention and disclosure. Explain preconditions and reachable effects without copying sensitive payloads. |
| Reliability and operations | Timeouts, retries, duplicate effects, partial failure, durable state, migration/rollback, flags and compatibility during rollout. Explain what can be recovered and which actor owns recovery. |
| Observability | Changed logs, metrics, traces, analytics and alert signals; correlation across boundaries, sampling/cardinality and sensitive fields. Explain how operators detect the concrete success/failure, and identify missing signals. |
| AI and LLM systems | Prompt/context assembly, instruction/data boundaries, retrieval provenance, tool permissions, output schemas, model/version changes, token/call cost, retries, fallbacks, nondeterminism and evaluation leakage. Distinguish fixtures, model evaluations and production behavior. |
| Coding standards and maintainability | Public contract, error semantics, boundary validation, dependency ownership, meaningful tests, stale comments, generated/vendor boundaries and unnecessary abstraction. Explain a maintenance consequence, not personal style preferences. |
| Product: user value and delivery | Affected people/journeys, problem and intended outcome, acceptance criteria, scope, dependencies, rollout/support implications and remaining work. Requirements come from accepted decisions, not code guesses. |
| Product: platform, data and growth | Integrators and API compatibility; data meaning/quality and measurement; adoption, experiment exposure or commercial effects only with supporting context. Keep hypotheses separate from measured outcomes. |
| UI/UX and accessibility | Journey, information hierarchy, interaction/empty/loading/error states, focus/keyboard, contrast, reflow, motion and perceived delay. Label source-inspected versus browser-exercised behavior; a schematic mockup is not a screenshot. |

## Connect the conclusions

Organize around mechanisms: “The retry uses the same key” can connect state ownership, duplicate prevention, user feedback, trace correlation and data exposure. Give one shared diagram and explain those implications together. If two lenses disagree, state the constraint or evidence behind each and the remaining decision. Do not bury a material risk beneath a positive summary.

Use a compact coverage table near verification for minor/irrelevant areas. Keep deep explanations for material effects. Broad coverage means every meaningful area was considered, not equal text for every role. Depth means a reader can follow causes, conditions and results, including the strongest supported limitation.

## Independent review when authorized

Check actual role/tool availability and applicable role instructions. Assign bounded high-risk mechanisms to independent agents when the task and host authorize delegation. Give exact snapshots, minimal authorized raw artifacts, applicable guidance, permitted read/isolated checks, exclusions and required evidence; prohibit further delegation unless authorized. Avoid passing a preferred conclusion or private context the child cannot access.

Reconcile findings against owning sources, deduplicate shared causes and resolve conflicting assumptions. Failed or incomplete agent work remains a gap. If delegation is unavailable, do the necessary passes inline and say so. Do not describe inline lenses, static content tests or agreement as independent review. Explanation delivery does not post reviews or alter readiness state.

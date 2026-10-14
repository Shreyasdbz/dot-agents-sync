# Walkthrough and risk coverage

## Establish the active path

Read purpose, acceptance criteria, linked design and known failures within authorized scope. Inventory semantic changes; identify deployables, public interfaces, flags and authoritative sources behind generated artifacts. Classify bug fixes, features, migrations or tooling changes by their actual contract, not only title.

For each affected vertical, trace registered UI route, API handler, command, worker or scheduled job through validation/authorization to the state owner, persistence/external effects and downstream readers. Verify registrations and runtime dispatch: a familiar helper or unused legacy path can be a decoy. Search definitions/callers, follow imports/contracts and inspect tests on both sides. Include unchanged code enforcing the invariant or consuming new behavior. Cross-repository exploration requires the affected producer, contract and consumer at recorded revisions, authorized access and known environment combinations.

Record the invariant, actor/input, ownership/isolation key, expected result and consequential effects. Trace a realistic failure path as deeply as success: invalid input, stale permissions, empty data, cancellation, replay, partial writes or external timeout where relevant. Expand until behavior reaches an established boundary with supported guarantees; do not read the whole repository without a decision-critical reason. An inaccessible boundary is a coverage gap, not evidence that no guard exists.

## Keep a coverage ledger

Use compact working notes, not a mandatory extra report. For every changed unit or coherent generated/mechanical group, record contract/path, risk, reviewer, inspected boundary owners/callers, evidence and status: examined, candidate, unresolved or unexamined. Include important unchanged consumers and shared invariants. Separate fact, inference and assumption. Prioritize privilege, data sensitivity, durability, fan-out, compatibility and user impact rather than file size. The ledger exposes omissions and focuses follow-ups; a filled checklist is not proof of correctness.

## Apply relevant perspectives

| Perspective | Questions at the owning boundary |
| --- | --- |
| Requirements/correctness | Does the journey and original failure meet requirements? Are units, identity, ordering, null/empty/boundary inputs and errors preserved? Which reachable case distinguishes base/head? |
| Security/privacy | Which actor controls input and crosses which trust boundary? Follow authorization/tenant isolation to actual read/write/disclosure/execution; inspect affected redaction, retention, logging, paths, injection and permissions. A suspicious API requires reachability and missing controls. |
| State/recovery | What is authoritative versus cached/derived? Inspect transactions, concurrent read-decide-write, replay across restart, partial commit, acknowledgements and recovery. Local rollback cannot undo external effects. |
| Compatibility/rollout | Inspect serialized contracts, schemas/generated clients, migrations, defaults, flags and mixed producer/consumer versions. What remains deployed during rollout? Which retained data/rollback constraints apply? |
| Performance/scaling | Trace query/index/access patterns, N+1 calls, pagination/limits, hot-path allocation, cache invalidation, retries and concurrency. Ground concerns in cardinality, query plans, workload evidence or reproducible growth; do not invent load figures or prescribe infrastructure for hypothetical scale. |
| Organization/footprint | Is the correction at the authoritative owner? Inspect dependencies, duplicated contracts, wrappers, abstractions, redundant state, dead/generated code and scope creep. Preserve ownership/conventions; fewer lines are not safer when checks merely move into callers. |
| UI/accessibility | Exercise the registered journey, loading/empty/error recovery, keyboard/focus, accessible names and representative viewports when available. Source inspection cannot establish visual quality or interaction success. |
| AI/tooling | Inspect instruction/context assembly, untrusted retrieval, grants, delegated inputs, tool effects, retries/stopping behavior and eval claims where changed. Prompt wording/agent availability is not runtime enforcement. |

## Validate mechanism and correction

Seek the strongest counterexample: upstream guard, downstream constraint, feature gate, unreachable registration, alternate environment or existing regression test. Compare base/head at the same boundary. Determine whether a defect is introduced, explicitly left unsatisfied by requirements or pre-existing outside scope. Pre-existing behavior matters when the PR makes it reachable or materially worsens it; show the causal link.

Choose focused checks that could falsify the claim. Reproduce before/after on disposable snapshots when allowed. Inspect CI requirements and run relevant project gates; use real disposable storage for persistence/transaction claims where feasible. For concurrency, control the dangerous ordering rather than trusting an unsynchronized burst. Mocks validate orchestration but cannot establish backend isolation, deployed compatibility or load behavior. If an essential guarantee cannot be checked, state the missing condition and gate precisely.

Propose the smallest coherent correction closing the reachable failure while preserving adjacent contracts. Prefer existing owners/abstractions. Avoid blanket rewrites, speculative defensive layers or independent shared-contract copies. Explain a necessary larger change by its invariant rather than equating fewer changed lines with lower risk. Suggestions do not authorize implementation.

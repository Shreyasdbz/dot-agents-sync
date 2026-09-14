# Scenario A — Propose

# Design proposal: billing webhook retries

## Outcome

Use at-least-once job execution with a durable, immutable payment idempotency key. A retry after a worker crash repeats the same payment operation with the same key, then records its result in Postgres. This closes the charge-before-completion crash window without trying to make Postgres and the payment provider share a transaction.

## Requirements and non-goals

Support 20 jobs/second, recover crashed workers, and preserve every existing job's original key. This proposal covers retry and recovery semantics, not a new billing model or an implementation plan.

## Assumptions and open decisions

Assume the payment API binds a key to one operation and safely returns or resolves the original result when the same request is repeated. Its key retention window, treatment of concurrent requests, and lookup capability must be verified. Automatic retry is safe only within those guarantees. A job whose original key is missing or whose provider retention has expired requires reconciliation before another charge request.

## Chosen design

Persist the payment key and canonical charge parameters before making the first provider call. Make both immutable for that payment operation. Workers claim jobs using short Postgres transactions and leases, release the transaction before network calls, and record results in another short transaction. Expired leases make jobs recoverable. Claim generations prevent an old worker from overwriting newer job state; the provider's key protects the payment even if two executions overlap.

Retry transient failures and ambiguous outcomes with exponential backoff and jitter, bounded by attempt and elapsed-time budgets and the provider's idempotency retention window. Honor provider rate limits. Permanent declines stop automatic retries. Exhausted or unsafe-to-repeat ambiguous operations enter a reconciliation state, not a fresh-key retry.

## Interfaces, state and data flow

The job retains its payment key, immutable request, execution state, next eligible attempt time, attempt count, lease generation and expiry, provider payment reference, and last failure classification.

A worker claims an eligible job, calls the provider with the stored key and request, then records completion and the provider reference. If it crashes after charging, lease recovery repeats the original request under the original key and records the existing payment result. A timeout is an unknown outcome: resolve or repeat under the same key, never generate a replacement key. Job completion updates must be conditional on the worker's current claim.

## Trade-offs and meaningful alternatives

This design accepts duplicate execution while preventing duplicate payments within the provider's documented guarantees. At 20 jobs/second, a Postgres-backed queue is a reasonable starting point; actual capacity depends on call latency and database contention and should be measured.

Marking a job complete before charging can lose payments. Charging before completion without idempotency can duplicate payments. Holding a database transaction during the API call cannot roll back the external charge and adds lock pressure. A separate broker may improve queue isolation later, but does not solve this crash window.

## Compatibility and migration

Existing jobs keep their original keys and request semantics. Do not regenerate keys from a new format during retries or deployment. Only new payment operations use any new key-generation convention. Historical jobs lacking a provable original key are quarantined for reconciliation. Mixed worker versions must preserve these same invariants before both can process jobs safely.

## Risks and validation needs

Validate crashes immediately before and after the provider call and before the completion commit; concurrent lease recovery; long-running calls that outlive leases; timeouts after successful charges; retention expiry; provider rate limits; and unchanged keys for old jobs. Observe one provider charge and eventual durable completion for safe recovery cases, and no automatic charge for ambiguous cases outside the provider guarantee. Load testing should confirm sustained 20 jobs/second with bounded database contention and retry backlog.

## Evidence

Based on the supplied worker behavior, Postgres job storage, provider idempotency support, throughput, and compatibility constraint. No repository or provider contract was available for verification.

# Scenario B — Plan Out

# Plan Context: inventory product

This is a read-only planning preview. Nothing has been published. GitHub remains the sole writable authority. Board access is unavailable, so INV-7's in-progress status is user-reported and unrefreshed. All `draft:` references below are stable preview identifiers, not newly created GitHub items. The GitHub project reference and native relationship fields remain unresolved and must be loaded before publication or execution.

- Authority: GitHub.
- Project reference: unavailable.
- Plan reference: `draft:inventory-product`.
- Design reference: approved design supplied in this request: import and editable inventory, followed by reconciliation, then analytics.
- Active milestone: `draft:mvp`.
- Status: draft preview; authoritative refresh blocked by unavailable board access.
- Native mapping: provisionally Milestone → Epic, Phase → Feature, Task → Task, with the Plan linked through project metadata. Epic/Feature/Task names are supplied; parent and dependency fields are not verified. Preserve explicit parent references if native nesting cannot express the hierarchy.
- Execution rule: refresh authoritative state and resolve preview references before using this context to implement work. Reuse INV-7 and any matching existing items; never publish a duplicate CSV parsing task.

## Immediate milestone: MVP (`draft:mvp`)

Outcome: users can import inventory and edit the imported records. Dependencies: none among the later milestones. Status: proposed, with INV-7 reported in progress. Exit criteria: a representative valid CSV produces editable inventory; malformed input yields actionable feedback without unexplained partial results; edits survive reload; the import-to-edit journey passes verification. Reconciliation and analytics are outside this milestone.

The proposed task locations below identify responsibilities, not verified repository paths. Repository discovery may require resizing; no indivisible sizing exceptions are assumed.

### Phase 1: Persist and edit inventory (`draft:mvp:inventory`)

Parent: `draft:mvp`. Order: 1. Outcome: a minimal usable inventory list and editing journey. Acceptance: records can be read and edited with validation and persisted results. Integration: establish the inventory contract consumed by import. Rollback: preserve stored data and keep schema changes backward compatible where practicable.

| Task / authoritative reference | Outcome and scope / likely location | Acceptance and verification | Dependencies / commit boundary |
| --- | --- | --- | --- |
| `draft:inventory-storage` / unresolved | Define minimal inventory persistence and validation; domain and persistence modules | Representative valid records round-trip; invalid records are rejected; test persistence and constraints | None / one storage-contract change |
| `draft:inventory-edit` / unresolved | Add validated read/update operations; application service or API | An update persists and invalid updates leave the record intact; integration checks | `draft:inventory-storage` / one service operation change |
| `draft:inventory-ui` / unresolved | Display and edit inventory; inventory view | User can edit, see validation feedback, and reload the saved result; UI journey check | `draft:inventory-edit` / one usable inventory screen change |

### Phase 2: Import inventory (`draft:mvp:import`)

Parent: `draft:mvp`. Order: 2; depends on Phase 1's inventory contract. Outcome: CSV import produces inventory that users can edit. Acceptance: valid and malformed files have understandable outcomes; successful imports appear in the inventory view. Integration: reuse INV-7's parser and the inventory write contract. Rollback: disable import entry while retaining existing inventory. Detailed import atomicity and duplicate behavior must follow current design and repository conventions; if neither defines them, resolve that bounded contract before implementing import persistence.

| Task / authoritative reference | Outcome and scope / likely location | Acceptance and verification | Dependencies / commit boundary |
| --- | --- | --- | --- |
| CSV parsing / `INV-7` | Reuse existing parsing work; parser module, actual location unverified | Review authoritative acceptance criteria and existing checks when accessible; confirm parsed output and malformed-row diagnostics meet the import contract | Existing dependencies unknown / retain existing item's scope and in-progress status pending refresh |
| `draft:import-persist` / unresolved | Connect parsed records to inventory persistence; import service | Valid input stores expected records; invalid input follows the agreed atomicity contract; integration fixtures | INV-7, `draft:inventory-storage` / one import persistence change |
| `draft:import-ui` / unresolved | Upload CSV and present results; import view | Users receive understandable success/error feedback and can open imported inventory; import-to-edit journey check | `draft:import-persist`, `draft:inventory-ui` / one import UI change |

## Future milestone: Reconciliation (`draft:reconciliation`)

Outcome: reconcile inventory using the approved reconciliation workflow. Scope boundary: reconciliation only; analytics remains later. Dependencies: MVP, plus current design details loaded when this becomes immediate. Exit criteria: representative discrepancies can be detected and resolved with durable, explainable results. Known risks: identity matching, conflicting edits, and unclear reconciliation rules. Status: future, unelaborated.

Exactly one task: **Plan Out Reconciliation** (`draft:plan-reconciliation`; native type Task; parent `draft:reconciliation`; authoritative reference unresolved). Reload design, repository, completed MVP work, and live GitHub state; replace this placeholder with current phases and tasks. Verification: a refreshed Plan Context with bounded implementation units and reconciliation acceptance criteria. No implementation phases are defined now.

## Future milestone: Analytics (`draft:analytics`)

Outcome: provide analytics over inventory and reconciliation results. Scope boundary: the approved analytics capability; no additional data product is assumed. Dependencies: Reconciliation. Exit criteria: approved metrics agree with representative underlying inventory and reconciliation data. Known risks: metric definitions, data quality, and query performance. Status: future, unelaborated.

Exactly one task: **Plan Out Analytics** (`draft:plan-analytics`; native type Task; parent `draft:analytics`; authoritative reference unresolved). Reload design, repository, completed work, and live GitHub state; replace this placeholder with current phases and tasks. Verification: a refreshed Plan Context with approved metric acceptance criteria and bounded implementation units. No implementation phases are defined now.

## Publication preview

The candidate mutations are three milestone Epics, two MVP Features, five new MVP Tasks, and one planning Task for each future milestone, with INV-7 reused and linked into the import phase after its existing relationships are checked. These are proposed counts pending deduplication against the board. No publication is authorized or attempted. Machine-schema validation and tracker identity reconciliation remain unperformed; this context records the available plan and the unavailable fields explicitly.

# Scenario C — Propose

Two requirements determine whether this should use globally coordinated writes or regional ingestion with later convergence:

1. Does “globally consistent” require every acknowledged event to be immediately visible in the same order everywhere, or is a bounded delay acceptable? What acknowledgment latency do you need in each region?
2. During a region partition, should isolated regions keep accepting events and reconcile afterward, or reject/wait when they cannot establish the required global ordering?

Those answers change the architecture. Strong global ordering requires coordination and can sacrifice availability during a partition; regional ingestion can keep local acknowledgments fast and available but cannot promise immediate global agreement. Once these requirements are set, I can select the architecture and document its trade-offs.

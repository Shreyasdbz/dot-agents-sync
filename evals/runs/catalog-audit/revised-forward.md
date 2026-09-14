# Scenario A

Use Postgres to own durable retry state and reuse the payment API's original idempotency key for every attempt of the same charge. A crash after payment success must lead to resolving that same payment, never issuing a new logical charge.

The worker remains an at-least-once processor. Avoid claiming exactly-once execution across Postgres and the payment API: the payment guarantee depends on the provider's actual idempotency contract, which is not supplied.

Persist an immutable operation key and charge payload before the first payment call. Existing jobs retain their original key unchanged. Different intended charges require distinct keys; retries do not. An old job whose original key cannot be recovered must enter reconciliation instead of receiving a replacement key.

Postgres owns pending, leased, retry-wait, completed, permanently-failed and reconciliation-required states, together with attempt count, next attempt time, lease generation and provider result. A short database transaction claims due work and assigns a lease. The network request runs outside that transaction. Completion and retry updates require the current lease generation, so a stale worker cannot overwrite a newer attempt. Lease expiry recovers crashed workers; leases alone cannot prevent duplicate network requests, so provider idempotency remains essential.

Normally, a worker claims a job, submits the persisted payload with its original key, receives a successful payment result and records completion. If the card is charged and the worker crashes before recording completion, the lease expires and the next worker resolves or repeats the operation using exactly the same key and payload. It records the existing payment result when the provider contract permits that. An ambiguous timeout remains unresolved work, not proof of payment failure.

Transient failures use capped exponential backoff with jitter and any applicable provider retry guidance. Definitive payment rejection can be terminal; exhausted retries with an uncertain payment outcome go to reconciliation. Operators must not reset such work with a new key. Retry scheduling and a concurrency bound protect the service from a retry surge. At 20 jobs/sec, retain the existing Postgres queue unless measured lock contention or latency demonstrates a need for another queue. Required concurrency depends on payment latency and retry volume, which are not given.

Keeping a database transaction open around the payment request cannot roll back an external charge and extends lock duration. Marking completion before charging risks missing a charge. Adding a broker or an outbox could change delivery mechanics but does not resolve the ambiguous external payment result; neither is justified solely by the supplied throughput.

The critical counterexample is an old job retried after the provider has expired its idempotency record. Reusing its original key might then create another charge. Therefore automated retry is allowed only within a verified safe provider contract; outside it, query authoritative payment history using the original identity or reconcile manually. Do not assume key retention, concurrent same-key deduplication, payload matching or result replay. These guarantees must be verified before enabling automated retries for ambiguous outcomes. No external provider was identified or consulted here.

Validation should demonstrate crash-after-charge recovery, concurrent attempts with the same key, stale lease completion rejection, retries after the provider's retention boundary, missing legacy keys and unchanged old-job keys. A load check should sustain 20 jobs/sec plus an agreed retry margin. This is a design decision only; no code or implementation plan is included.

# Scenario B

The draft plan is in `/private/tmp/dasync-revised-plan.json`. It passed `dasync validate plan-context --path /private/tmp/dasync-revised-plan.json --json` with `ok: true` and `valid: true`. GitHub remains the sole writable authority. Its state is explicitly unavailable and unrefreshed; the draft carries portable identities, proposed work and unresolved external references. INV-7 is reused for CSV parsing with its supplied in-progress status preserved, without claiming that the board was checked.

The logical mapping is Plan → GitHub board, Milestone → Epic, Phase → Feature, Task → Task. Epic, Feature and Task are the supplied native types. The board identity and native parent/child relationship fields remain unverified; this mapping is proposed for reconciliation when access returns. An Epic label does not imply a verified GitHub milestone field or relationship API.

The MVP has two independently mergeable PR phases. The import phase completes INV-7, persists parsed inventory, and connects file import to a reloadable inventory view. The editing phase adds validated persistence and connects editing and save feedback to that view. Each task includes acceptance and verification alongside its behavior. Parser and persistence commits are intermediate components inside the import PR; the PR boundary delivers the usable path. Editing follows import so its user journey has persisted inventory available.

Reconciliation and analytics retain only their outcomes, boundaries, risks, exit criteria and one planning task each. Their order follows the approved delivery sequence. Analytics' dependency on reconciliation expresses that delivery order; no technical dependence on reconciled data is asserted.

Provisional sizing is three tasks for import and two for editing, aiming for 1–5 related files and 25–250 substantive lines per task and 150–800 lines per PR. No repository inspection was authorized for this scenario, so these are review limits rather than measured estimates. Reassess if a phase exceeds two guardrails, preserving a usable vertical boundary. Inventory fields, import failure semantics and concurrent-edit rules need the approved design details before implementation; the draft exposes these inputs rather than choosing new product behavior.

Proposed tracker changes: reuse INV-7; add the MVP and two future milestone Epics if absent; add two MVP Feature phases, four other immediate Tasks and one planning Task for each future milestone. No new tracker IDs are invented. On restored access, refresh existing items, match stable identity, preview changes and native relationships, and preserve current statuses. Publication still requires authorization. Nothing has been published or implemented.

# Scenario C

Two requirements determine the architecture before I can responsibly choose it:

1. During a region partition, must conflicting writes stop so every acknowledged event has one globally agreed order, or must each isolated region continue accepting events and reconcile later? If global consistency is the hard requirement, I recommend quorum-based writes and explicitly accepting that an isolated region may reject or defer writes.
2. What p95 or p99 latency target should apply, and does it measure local receipt, durable global acknowledgement, or visibility to readers in all three regions? These are different promises. Also specify whether ordering is needed across every event or only within a tenant or stream; that determines the scope of coordination.

Pending those answers, the conditional recommendation is replicated consensus per required ordering domain, with acknowledgements only after the required quorum has durably accepted the event. That supports an agreed order but adds inter-region coordination latency and cannot keep every partition writable. If continuous regional ingestion is required instead, use local durable acceptance with asynchronous replication and define conflict and ordering semantics explicitly; that weakens the global acknowledgement promise.

For example, if two disconnected regions both acknowledge conflicting events as final, they cannot simultaneously guarantee a single immediately consistent result everywhere. Calling local acceptance “globally consistent” would hide that contradiction. I would leave the final architecture decision open until the partition behavior and latency contract are settled. No implementation work is planned.

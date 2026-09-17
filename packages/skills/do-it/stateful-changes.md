# Stateful changes

Use this review for durable writes, retries and concurrent callers; omit irrelevant cases rather than inventing infrastructure.

## Establish the guarantee

State the invariant, its authoritative owner and the externally required result. Identify every caller that can cross the boundary, the identity/isolation key, and which effects can commit together. Reuse existing durable records before adding a parallel ledger or cache.

Inspect the actual runtime's transaction start, commit, rollback and locking semantics. A context manager, annotation or callback name does not prove that earlier reads are inside a transaction. For read-decide-write logic, show what prevents another caller changing the decision's inputs before the write. A unique constraint may prevent duplicate effects yet still fail the required successful-retry contract.

## Challenge the ordering

Use the real disposable backend. Coordinate contenders at the dangerous boundary, such as after a decision read but before a write; a burst of unsynchronized requests can pass by luck. Observe locks or transaction state with a bounded trace/fault seam when needed. Record the ordering, expected result, actual result and persisted state; distinguish instrumentation from an end-to-end external run.

Exercise exact replay across restart, conflicting reuse, isolation and invalid inputs where relevant. Inject failure between coupled writes and after commit before acknowledgement; verify retry and recovery preserve the invariant. If an external effect cannot share the transaction, identify the existing idempotency/reconciliation contract rather than pretending local rollback undoes it.

## Gate completion

For each decision-critical guarantee, retain evidence or state the missing check. Do not call work complete while a required concurrency, durability or isolation assumption remains unverified. If the environment cannot establish it, return a conditional result and the precise gate, not an unconditional success with a footnote.

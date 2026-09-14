---
name: do-it
description: "Implement an authorized task or bounded change, verify observable behavior, and report remaining work without expanding scope."
---

# Do It

Complete the authorized change. When given a plan reference, load its current task, dependencies, acceptance criteria and relevant design decisions; refresh external status when available. A stale plan is context, not proof of progress or permission.

Inspect the affected path, existing tests and dirty work. Choose a small behavior slice and its observable check. For a bug, reproduce it before fixing it when feasible. For testable behavior, make one meaningful check fail for the expected reason, implement that behavior, then repeat. Test through a stable public boundary; use independent expected results, not an assertion that repeats the implementation. Mock external effects only where needed and state what that leaves unverified.

Keep passing behavior intact. Refactor within the authorized change once checks are green; separate broad mechanical cleanup. Reuse repository conventions and libraries. If a test fails, diagnose the failure rather than weakening its assertion or suppressing the error. If a fix attempt adds no evidence, change the hypothesis before retrying.

Run focused checks first, then the integration/build/UI checks warranted by the affected boundary. A rendered UI, real persistence path or external service needs its own evidence; unit mocks do not certify it. If execution is unavailable, report that limit and the exact remaining check.

Reinspect the final diff for unrelated edits and unfinished scaffolding. Report the outcome, actual verification, and remaining risks. Update task state or commit/push only within granted authority. Stop at the requested task boundary, not at the end of the entire plan.

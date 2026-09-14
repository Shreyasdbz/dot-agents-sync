---
name: do-it
description: "Implement one authorized task from a plan and verify its outcome."
---

# Do It

Given one implementation task, make the scoped change using the relevant repository context, policies, and existing conventions. Establish a failing test first when it is a meaningful way to prove the behavior, implement the change, run proportionate verification, and report the observed outcome.

- Boundary: execute one authorized task; do not broaden scope or treat a plan as permission for unrelated work.

- Output: a concise outcome-first summary, the relevant verification evidence, and a commit only when the invocation explicitly authorizes Git mutation.

- Typical dependencies: coding, testing, security, scope, and Git policies plus stack and repository context.

---
name: do-it
description: "Implement an authorized task or bounded change, verify observable behavior, and report remaining work without expanding scope."
---

# Do It

Complete the authorized outcome, not merely the first plausible patch. For a plan reference, resolve the requested/current task, acceptance criteria and design decisions; refresh available dependency and completion status before implementing. Preserve dirty work. A stale plan is context, not proof of progress or permission.

## Discover the mechanism

Apply policy.repository-guidance to resolve applicable instructions, selected context and role boundaries. Trace active entrypoints and registrations through owning logic, state/effects and observable result; verify against effective configuration, tests and other consumers. Do not patch legacy or generated lookalikes.

Keep a compact map of ownership, invariants and unresolved facts with source pointers. Inspect history or widen the search only to answer a concrete gap; batch related reads and delegate only independent questions. Inspect unfamiliar scripts for side effects before running them. Missing documentation is not permission to invent a mechanism or ask the user to rediscover facts available locally.

## Choose the change

Reproduce the problem or establish the expected behavior through a stable public boundary. Separate observed failures from assumptions. Compare credible alternatives at the owning boundary: reuse or configuration changes, a focused fix, and new machinery only when needed. Reject caller-only patches that leave another reachable path broken. Record why the chosen approach fits and what evidence would overturn it; challenge it with the strongest plausible counterexample.

Assess trust boundaries, authorization, input validity, compatibility and data-loss risks. For durable state, retries or concurrency, load [stateful-changes.md](stateful-changes.md) before choosing the mechanism and completion checks. Ground scaling in actual volume, concurrency and latency; measure an uncertain bottleneck before adding queues, caches or services. Never weaken safety for a small project.

## Implement and verify

Record a focused regression failing for the expected reason when feasible, then fix the authoritative source using existing abstractions. Assert independent expected results, not a copy of the implementation. Keep passing behavior and user edits intact; do not weaken assertions, swallow errors or introduce success-shaped fallbacks. If an attempt adds no evidence, change the hypothesis instead of repeating it.

Cover the public path, other consumers and consequential negative cases. Use target-defined test/build commands; missing required tooling is a gap, not permission to add runners, shims or environments. Start focused, batch related selectors, then run required integration/build/UI gates. Exercise real persistence, concurrency or external boundaries in authorized disposable environments; mocks cannot certify them. Never use production data or destructive probes without explicit authority.

## Completion gate

Inspect the final diff for scope creep, duplicated mechanisms, dead code and unfinished paths. Finish only when acceptance is supported and material alternatives and counterexamples are resolved by evidence or explicit constraints. Do not enumerate imaginary alternatives indefinitely; stop when further exploration would not change the decision. A material unresolved risk means a conditional result or blocker, not "done."

Report the outcome, decisive checks, trade-offs and remaining limits concisely. Distinguish proposed, mocked, locally executed and external evidence; never label an untested solution secure, scalable or battle-tested. Commit, publish or update external state only within granted authority. Stop at the requested task, not the entire roadmap.

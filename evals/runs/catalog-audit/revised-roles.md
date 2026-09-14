# D — PR review

Block — one SEV_1 regression in the supplied offline snapshot for PR 17, base `aaa`, head `bbb`.

`cache.py:8` — Preserve zero-valued cache hits. With an existing entry `cache[key] = 0`, `cache.get(key)` is false, so execution reaches `charge_customer(order_id)` again. This violates the prohibition on duplicate charge calls. The original membership check correctly distinguishes a cached zero from a missing entry. Restore `if key in cache: return cache[key]`.

The unchanged Database behavior supplies no tenant-isolation finding: its constructor selects the tenant and `find_user(id)` is internally scoped.

Verification limits: reviewed only the authoritative supplied snapshot; no execution, network access, or posted review.

# E — Investigation

The deployment's readiness check targeted port 8080 while the application listened on port 3000. That mismatch explains the readiness refusal.

Observed sequence: deployment began at 12:00; at 12:01 readiness on 8080 was refused and the app reported listening on 3000; rollback succeeded at 12:02. Configuration independently confirms `readinessPort=8080` and `appPort=3000`.

A startup delay could also cause connection refusal, but the explicit port mismatch provides the direct explanation here. The evidence does not establish whether the application was otherwise healthy or whether readiness failure automatically triggered rollback.

The smallest proposed correction is to align readiness with the intended application port. No change or restart performed. I can provide a Markdown report or pitch deck if needed.

# F — Security review

High priority — The proposed export embeds private `design.md` content in the public HTML response. Any visitor can retrieve the source and read the comment; visual hiding provides no access control. Customer names and unreleased plans would cross the private-to-public disclosure boundary.

Location: the export step that inserts the document into an HTML comment. Preconditions: the proposed export executes and its HTML is publicly served. The plan establishes the disclosure path; it does not establish that publication has already occurred.

Exclude the private document from the public output. If context is required, include only an explicitly approved public summary. Verify the generated HTML contains no private source content before publication.

Scope: export path only; no live access or broader security assessment.

# G — Architecture review

Blocking contract failure — The gap between committing the order to Postgres and publishing its queue event can permanently strand an accepted order. A worker death after the commit but before publication leaves durable order state with no fulfillment event; the supplied plan has no retry mechanism. This violates “accepted order must eventually reach fulfillment.”

Location: the separate database-write and queue-publish steps. The ordinary path succeeds, but neither that success nor queue durability repairs a publish that never happened.

Smallest useful correction: commit a pending event alongside the order in the same database transaction, then have a recoverable dispatcher publish pending events with retries. Handle duplicate delivery through idempotent fulfillment, since a crash after publishing but before recording completion can cause a repeated event.

This is a demonstrated failure of the supplied plan; no implementation or runtime verification performed.

# H — AI systems review

The evidence does not establish that prompt B improves general quality. B's 10/10 is a development-set result: the same ten examples informed prompt edits and the final score. A's one-time 8/10 is therefore not a comparable estimate of unseen performance.

Consequential gap: selection on the evaluation examples can reward overfitting. The observed two-example gain may disappear on new tasks; its size and reliability are unknown.

Freeze both prompts and compare them under the same model, settings, and scoring rubric on an independent representative set that has not informed either prompt. Keep scoring blind to prompt identity and account for run-to-run variation where relevant. Report per-example outcomes and failures, not only totals.

No latency or token measurements were supplied, so efficiency claims are unsupported. No model calls or configuration changes performed.

# I — UX review

Two source-supported accessibility findings:

1. Primary action: a `div` with only `onclick` has no native keyboard focus or button activation behavior. A keyboard user trying to Tab to and activate this action lacks the expected control. Replace it with a named native `button`; retain its standard Enter/Space handling. No runtime keyboard check was performed.

2. Dialog: missing focus management leaves no supplied mechanism to move focus into the dialog and restore it on close. If modal, focus must also remain within it while open. Implement the appropriate dialog semantics and focus behavior, then verify opening, keyboard navigation, dismissal, and focus return.

These findings come from source only. Rendered focus behavior, accessible names beyond the supplied facts, screen-reader output, visual quality, and overall accessibility conformance remain unverified. No screenshot or browser session was available.

# J — Slop audit

Finding — Report phrase “production-ready”: mocked unit tests alone do not substantiate this completion claim. They demonstrate behavior under the supplied mocks, leaving real integration and operational behavior unverified. Replace the claim with the precise evidence: “Mocked unit tests passed; production readiness has not been established.” Identify any remaining release criteria before asserting readiness.

No finding against the deliberate fake payment client in the test fixture: a test double is appropriate in that context and does not prove production payment behavior is unfinished.

No finding against `AUTHOR` slots in the reusable template: authoring placeholders are intentional unless they leak into a finished deliverable. No such leak was supplied.

Scope: the report claim and those two constructs only. No production execution or broader code review performed.

# K — Travel recommendation

I cannot identify a verified currently available hotel under $150 from the undated $129 screenshot. It provides neither current availability nor a reliable total for Friday, September 18, 2026; the currency, stay length, taxes, fees, and restrictions are also unspecified.

The pictured hotel is only a provisional candidate, not a confirmed recommendation. With browsing unavailable, the next necessary check is its official booking page for the intended destination, exact stay dates, occupancy, currency, and total including mandatory charges. No supporting live link or verified alternative was supplied.

No booking, payment, or outreach performed.

# Actual action summary

Read the eight requested package instruction files under `/Users/shreyas/Dev/repos/dot-agents-sync/packages` and applied them to the supplied scenarios. Located those files with a scoped filename search. Created this output file with `apply_patch`. Did not inspect repository implementation, other agent outputs, research, or evaluation cases; did not edit the repository, execute scenarios, access external services, or post anything. This is an instruction-following forward test, not an authenticated native provider integration.

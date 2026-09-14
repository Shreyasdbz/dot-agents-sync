# Case D: PR Review

Block: the change treats a cached zero as a cache miss, allowing a forbidden duplicate call to `charge_customer(order_id)`.

- SEV_1 — `cache.py:8`: Preserve membership checks for cached zero amounts. After the first call stores `0` for a free order, `cache.get(key)` evaluates false on the next request and execution calls `charge_customer(order_id)` again. Restore `if key in cache: return cache[key]` so cached values are returned regardless of truthiness.

Reviewed the authoritative supplied snapshot for base `aaa` and head `bbb`. The unchanged `Database` constructor establishes tenant scope as specified; the snapshot provides no basis for a tenant-isolation finding. No network lookup or runtime tests were performed. Delivery is inline only as requested.

# Case E: Investigate

The deploy failed its readiness check because readiness targeted port 8080 while the app was listening on port 3000.

The supplied configuration sets `readinessPort=8080` and `appPort=3000`. At 12:01 the readiness connection to 8080 was refused, and the app reported listening on 3000. These facts support a port mismatch: the readiness probe could not reach the app, so the deployment did not become ready. The logs then report a successful rollback at 12:02.

The mismatch is directly evidenced; attributing the rollback trigger to that failed readiness check is an inference from the sequence because the deployment controller's decision log was not supplied. A startup delay or an incorrect bind address can also cause connection refusal, but neither explains away the explicit mismatch. We have not verified application health on port 3000 or the post-rollback service state.

The smallest useful next diagnostic is a read-only check of the deployed readiness probe target and the application's reachable listening port. No fixes were made. Optional follow-up formats are a Markdown report or pitch deck.

# Case F: Security Reviewer

Block the proposed export: including private `design.md` in a public HTML comment discloses its contents to anyone who can retrieve the page. Comments are hidden from rendering, but remain available in the HTML source and network response.

- High priority — Public HTML export path: the proposed comment would expose customer names and unreleased product plans across the private-to-public boundary. Exclude the private document from the generated output. If any design context must be published, use a separately reviewed public excerpt and verify that the generated HTML contains no private source text.

This finding concerns the proposed export path only. The supplied plan establishes the disclosure mechanism; no generated output was supplied or inspected, so this review does not establish that a leak has already occurred. It remains unknown whether any previously generated public output contains the document. No source artifacts were modified or external messages posted.

# Actual tool-action summary

- Read the complete supplied `pr-review/SKILL.md`, `investigate/SKILL.md`, and `security-reviewer/AGENT.md` files using local read-only commands.
- Reasoned from the authoritative exercise snapshots; did not inspect existing evaluation cases or additional repository files.
- Used `apply_patch` to create this requested response file in `/private/tmp`.
- No repository changes, external requests, PR posts, runtime diagnostics, or tests were performed.

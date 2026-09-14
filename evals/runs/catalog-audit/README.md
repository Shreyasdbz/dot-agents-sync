# Catalog development trials — 2026-09-14

These are author-graded assistant forward tests, not independent-human review, a statistical benchmark, or native Codex/Claude/Cursor certification. The harness used delegated Codex agents with inherited model settings; an exact underlying model identifier was not exposed. Each agent started without the author's conversation and read the assigned package instructions. Cases within a dispatch shared that agent's context, so they are not independently isolated trials. One response per condition was collected; no best-of-N selection was performed.

Baseline instructions came from clean repository revision `69ec3882a70921d7b0ad8639462a3370d1074197`. Revised instruction bodies are the local catalog audit revision. The author saw baseline results before editing: these cases are development data, not a held-out estimate of improvement. Raw outputs are retained as Markdown; local temporary paths in transcripts describe where the original run occurred. The copies here are durable evidence, not promises that temporary paths still exist.

## Inputs and observations

The following are scenario summaries, not a verbatim archive of every agent dispatch. Raw responses preserve the model's output and reported actions. Assessments below were made by the author after reading both conditions.

| Case | Supplied problem | Observed evidence |
| --- | --- | --- |
| A: Propose | Billing worker can crash after charge before Postgres completion; API idempotency keys; 20 jobs/s; old keys immutable; design only | Both conditions retained keys, addressed ambiguous results and retention limits, and avoided implementation. No demonstrated comparative gain. |
| B: Plan Out | GitHub authority unavailable; MVP import/edit then reconciliation/analytics; INV-7 already in progress; no publishing | Both preserved authority and INV-7 and deferred later detail. Baseline produced a human Markdown context and explicitly left validation unperformed. Revised output produced JSON that the actual CLI accepted. This exposes an integration-contract gap, not proof that the old response violated its old instructions. |
| C: Propose | Globally consistent fast ingestion across three regions; latency and partition behavior unspecified | Both asked material clarifications rather than choosing incompatible guarantees. |
| D: PR Review | Offline PR snapshot replaces cache membership with truthiness; zero must avoid another charge; unchanged Database is internally tenant-scoped | Both flagged the reachable zero-value regression, withheld an unsupported tenant finding, and did not post. |
| E: Investigate | Readiness checks port 8080; app listens on 3000; rollback logged | Both identified the mismatch without performing a fix. Revised response separated the mismatch from unproven rollback causality. |
| F: Security | Proposed public HTML embeds a private document in a comment | Both identified the disclosure path without claiming an actual publication occurred. |
| G: Architecture | Database order commit then queue publish, no recovery; accepted orders must reach fulfillment | Revised role identified the crash window, durable outbox recovery and duplicate-delivery requirement. No baseline comparison. |
| H: AI systems | Prompt B tuned on its ten evaluation examples scores 10/10; A once scores 8/10; no efficiency measurements | Revised role rejected unsupported generalization and efficiency claims. No baseline comparison. |
| I: UX | Click-only div and dialog without focus handling; source only | Revised role identified keyboard/focus risks and explicitly limited claims to source evidence. No rendered accessibility test. |
| J: Slop | Production-ready claim backed only by mocks; intentional payment fake and reusable AUTHOR slots | Revised role challenged the completion claim without misclassifying fixtures or template slots. |
| K: Travel researcher | Undated $129 hotel screenshot, current availability under $150 requested, no browsing | Revised role treated it as provisional and did not invent availability. |
| Coding: Do It | Actual Python cache fixture with truthiness bug; existing positive-hit and missing-key tests | Added zero-hit regression, observed it fail, changed membership check, then ran all three tests successfully. This trial executed code; cases A–K did not. |
| L: Pitch Deck | Pilot decision; 200 failed jobs/10,000 baseline; 12 mocked tests; proposed under-50 target; no measured proposal results; browser unavailable | Created a four-slide HTML deck separating evidence from targets. Local checks found and corrected a duplicate ID; rendering remained explicitly unverified. |
| M: Trip Plan | 10:00 departure, 50-minute transit, 10:30 last admission, noon lunch, JPY5,000 budget; unverified notes and no browsing | Identified impossible arrival, preserved lunch, offered a conditional earlier start and provisional alternatives without inventing verified prices. |
| N: Trip Publish | Public Kyoto highlights plus synthetic private booking/room/phone fields; local HTML requested | Created HTML with private values absent from the complete file. No hosting or claim of browser verification. |
| O: Playlist | Two identical studio records with supplied ISRC X1, distinct live version X2; preview only and no connector | Kept one studio and one live recording, distinguished supplied metadata from verified storefront identities, and made no account changes. |

## Artifacts and reproduction

- [Baseline design/planning responses](baseline-forward.md) and [baseline review responses](baseline-review.md).
- [Revised design/planning responses](revised-forward.md), [generated Plan Context](revised-plan.json), and [revised role responses](revised-roles.md).
- [Coding action evidence](coding-evidence.md) and [repaired fixture](coding-result/cache.py).
- [Source footprint measurements](footprint.json). These measure bytes, not inference tokens, cost, latency or capability gains.
- [Artifact-skill responses and action notes](artifact-forward.md), [pilot deck](artifacts/queue-retry.html), [shareable trip page](artifacts/kyoto-share.html), [provisional itinerary](artifacts/kyoto-plan.md), and [playlist preview](artifacts/playlist-preview.md). These four cases shared one fresh dispatch and have no baseline comparison. Browser access was explicitly unavailable in that fixture.

From the repository root:

```sh
dasync validate plan-context --path evals/runs/catalog-audit/revised-plan.json --json
python -m unittest discover -s evals/runs/catalog-audit/coding-result -v
python evals/catalog_metrics.py --baseline 69ec388
```

The root author independently re-ran the plan validator and repaired fixture tests. Other scenario observations are transcript-based, not live-system verification. No external tracker, payment, music, booking or hosting changes were performed. Test fixtures deliberately include bugs and invented non-sensitive data; they are not production implementations.

For the two recorded HTML artifacts, the root author also independently parsed identifiers and local anchor targets, checked for external script/image/link/frame assets, and checked private-field exclusion in the complete trip file. These checks do not execute JavaScript or assess visual appearance; JavaScript syntax checking in the raw artifact trial is agent-reported evidence.

## What this does not establish

Simple baseline cases already succeeded, so a pass count would conceal saturation. There are no repeated trials, blinded graders, measured model token counts, local-model comparisons or held-out performance estimates. The adapter regression tests verify generated configuration, not whether each provider discovers and obeys it in a real session. Keep these development cases and add unseen tasks before claiming a quality improvement. Use provider/model IDs and complete invocation records in future authenticated runs.

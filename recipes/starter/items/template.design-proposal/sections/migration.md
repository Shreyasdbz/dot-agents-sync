# Migration and refactor recipe

Use when data, interfaces, dependencies or deployment versions must change without breaking existing behavior.

## Before, after, and invariant

Describe the current and target contracts, the reason to move, and externally visible behavior that must remain stable. Identify readers, writers, background jobs, retained data and supported versions; avoid claiming this inventory is complete without inspection.

## Compatibility states

| State | Readers / writers | Source of truth | Safety condition | Exit evidence |
| --- | --- | --- | --- | --- |
| Expand | Existing and compatible new versions | Identify actual authority | Old readers still work | Contract checks |
| Migrate | Explicitly supported mixed versions | Define conflict resolution | Retries and partial backfills are safe | Reconciliation evidence |
| Contract | Supported target versions only | Final authority | No remaining old consumers | Measured removal gate |

Replace these states with the real transition; they are design states, not implementation tasks. Explain ordering requirements, checkpoints, partial failure, replay safety and how progress is verified. Do not call an eventually reconciled process atomic.

## Reversibility

Name the point of no return. Distinguish code rollback from data restoration and from forward repair. Specify retention and recovery prerequisites without inventing recovery time or data-loss guarantees.

## Cutover decision

Define the evidence for continuing, pausing or reverting. Cover observability, ownership and mixed-version validation. A refactor with no migration should use only the before/after invariant and behavior-preservation sections.

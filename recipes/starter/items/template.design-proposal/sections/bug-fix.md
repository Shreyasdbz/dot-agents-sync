# Bug-fix recipe

Use for a reproducible defect or regression. A small bug can fit in a few paragraphs using these headings; avoid expanding it into a feature specification.

## Contract and failure

State expected versus observed behavior, affected users/versions, and the smallest reachable input/state that exposes the defect. Include reproduction steps and an observed result when available. Distinguish a hypothesis from a reproduced failure. Quantify blast radius only from evidence.

## Cause and correction

Trace the causal path from input through the faulty decision to the result. Identify the violated invariant. Show the smallest proposed correction and why it addresses the cause rather than suppressing a symptom. If more than one fix is viable, compare behavioral differences, compatibility and maintenance cost.

## Regression boundary

State behavior that must stay unchanged, existing data or cached state affected, and whether old/new implementations can coexist. A schema or protocol change triggers the migration recipe; do not hide it under “bug fix.”

## Verification and containment

Define the failing regression, neighboring edge cases, failure paths and expected results independently of the implementation. Separate tests already run from tests proposed. Include containment/rollback only if relevant, and flag data that cannot be reconstructed. End with unresolved questions that actually block the fix.

Optional concise structure: **Failure → Cause → Correction → Regression proof**. Do not add personas, full system inventories or arbitrary alternatives to a localized defect.

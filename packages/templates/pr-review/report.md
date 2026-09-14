# PR review composition guide

Create one canonical review and project it into requested formats. Preserve the skill's severity definitions and inline default.

## Review header

Identify PR or supplied diff, base/head revisions, review status (draft/posted), scope and actual checks. Unavailable identities remain unknown; a snapshot is not a refreshed PR.

## Verdict

Approve, Suggest or Block with the consequential reason. “No supported findings in the examined scope” is valid; it is not exhaustive correctness or evidence that unrun checks passed.

## Findings

For each finding, use **severity + concrete title**, then location, reachable trigger, consequence, evidence, counterevidence considered and feasible correction. Keep the finding readable without opening every link. Consolidate one root cause; distinguish regressions from pre-existing behavior and preferences.

A useful structure is: **Location → Trigger → Impact → Evidence → Correction → Verification**. Remove redundant labels in short findings. Do not invent a finding to fill a category.

## Adaptation

- Bug fix: check that the proposed correction closes the original failure without changing adjacent contracts.
- Feature: check the stated user journey, authorization, empty/error states and integration boundaries.
- Migration: inspect mixed-version behavior, retained data, partial progress and rollback limits.
- Documentation/configuration: check executable examples, discoverability, compatibility and unsafe instructions; do not demand irrelevant runtime tests.
- Large diff: state sampling and unreviewed areas. More surface area does not justify stronger certainty.

## Verification and publication

Distinguish inspected source, executed tests, mocks, live integrations and unavailable checks. Preserve head revision and finding identities across Markdown, [report.html](report.html) and posting. Refresh anchors before posting; record returned IDs only after confirmed submission. Load [components.md](components.md) for HTML composition and empty/filter states. Remove sample findings from a real review.

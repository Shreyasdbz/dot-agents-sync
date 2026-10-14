# Design proposal composition guide

Produce a decision record, not a filled questionnaire. Select a recipe below and load only its linked file. Rename headings to convey the actual decision; omit inapplicable sections instead of writing “N/A.” Respect a requested output format.

| Context | Load | Deciding question |
| --- | --- | --- |
| Bug fix / behavioral regression | [Bug fix](sections/bug-fix.md) | What failed, why, and what restores the intended contract? |
| New feature / capability | [Feature](sections/feature.md) | What user outcome and system boundaries justify this design? |
| Migration / refactor / deprecation | [Migration](sections/migration.md) | How does every intermediate version remain safe? |
| Architecture choice / dependency selection | [Decision](sections/decision.md) | Which criteria distinguish credible alternatives? |

## Minimal spine

Start with a specific title, document type, decision status (proposed/accepted/superseded), owner if known, and source revision/date when relevant. State the decision and intended outcome in the first paragraph. Include the recipe's consequential sections, then unresolved decisions and evidence. Never fabricate ownership, approvals, measurements or source freshness.

## Add only the cross-cutting modules you need

Load [cross-cutting sections](sections/cross-cutting.md) for security/privacy, performance/cost, data/API contracts, observability, accessibility, rollout and reversibility. A one-function correction rarely needs all of these. A feature spanning authorization, storage and an external API usually needs several. Mix recipes when the change genuinely combines concerns, but retain one decision and remove repeated sections.

## Evidence and finish

Attach facts to code locations, observed behavior or dated primary sources. Separate observed, inferred and proposed claims. Explain what would invalidate the recommendation. Leave material questions visible rather than burying them in an appendix. Do not introduce implementation milestones, phases or tasks; Plan Out owns decomposition.

For an HTML view, use [proposal.html](proposal.html) and [components.md](components.md). Keep the same claims, alternatives and uncertainties across formats. The HTML is a worked illustrative composition, not content to preserve in a real proposal.

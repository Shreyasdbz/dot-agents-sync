# Trip navigation and expenses

Verified locally on 14 September 2026. Changes are uncommitted; the prior E2E testing batch remains intact.

Moved the five section links into the trip top bar with icon-only print/theme controls. The bar is sticky, adds supported backdrop blur over scrolled content, uses an opaque fallback and disappears in print. Its measured height sets anchor clearance. Theme icons represent the applied theme, update with system changes until manual selection and retain the Dark mode toggle's accessible pressed state.

Added a reusable Expenses section after To do and before metadata, with category totals, line items, quantity/rate or allowance bases, reservation links, per-person average and payment/sharing/exclusion explanations. Sample leaf rows sum to the US$12,000 headline; repeated category/overview amounts are excluded from that sum. Unknown payments remain unknown. Currency switching includes all estimate displays while original unit-price bases retain explicit USD labels.

## Verification

- Complete suite: 85 passed in 84.40 seconds.
- All four template browser checks passed at 320/390/1440 widths, including print restoration, no-JavaScript reading and automated accessibility checks.
- Focused travel tests passed sticky position, blur activation, unobscured anchor heading, theme-icon system changes/manual override, section ordering and expense leaf reconciliation, plus earlier currency/copy/print cases.
- Deck navigation regression passed after regenerating all pages with the shared theme behavior.
- Ruff lint/format, source/generated parity and whitespace checks passed.
- Visually inspected the mobile full page and expanded Expenses section. Browser artifacts are in /private/tmp/dasync-travel-expenses; the focused expense screenshot is in the OS temporary directory as dasync-expenses-mobile.png.

The first catalog run caught the larger template exceeding its old package allowance. The trip entrypoint limit is now 70 KB and the manifest's aggregate approximate token allowance is 25,000, retaining explicit finite checks. Final entrypoint: 66,555 bytes; SHA-256 d8e453c44618c012568e4da62f60b37bc39fc0266902d5fdff09dd00194c8be1. No external assets or runtime dependencies were added.

Axe reported no violations but retained incomplete contrast checks for travel preview/navigation and deck SVG text. Native screen-reader/browser interoperability and actual financial data were not certified. Expense amounts and exchange rates remain illustrative, not current prices. Clipboard tests still use a double.

# Template system verification — 2026-09-14

Local author-run verification of the revised templates, not independent-human review or blanket production/accessibility certification. Existing catalog changes from the preceding audit were preserved. No personal provider configuration, tracker, booking, hosting or publishing state was changed.

## Scope and result

All eight Template packages now ship composition guidance appropriate to their context. Design proposals have separate bug-fix, feature, migration and architecture-decision recipes plus cross-cutting modules. Investigation, review, itinerary, playlist and machine Plan Context guides adapt without requiring every possible section. The four HTML entrypoints share one canonical foundation and ship individually loadable fragments where applicable.

The complete Python suite passed **70 tests in 45.78 seconds**. New tests enforce generated/source parity, package-local Markdown links and module distribution through all three provider adapters. Lint and formatting checks passed, as did source-distribution and wheel builds. One earlier suite ran while template bytes were being regenerated and correctly rejected a changed source pin; the final run used a stable catalog and passed.

## Browser checks

[Raw results](browser-results.json) were produced by scripts/test_templates.cjs using headless Chromium **151.0.7922.34** and axe-core **4.13.0**. Screenshots and PDFs were written to /private/tmp/dasync-template-browser; temporary files may expire. Re-run the documented command to regenerate them.

All four pages passed: 320/390/1440px document reflow, long-title reflow, light/dark switching, IDs and local anchors, no page errors, and no-JavaScript readable fallback. Applicable interaction checks passed: native keyboard disclosure, closed defaults, expand/collapse all, deep-link reveal, repeated print-state restoration, local finding search and empty states, inclusion of filtered findings during print, and deck navigation/endpoints.

The browser run found two defects during development: nested/repeated print events overwrote the saved card state, and the presentation select's intrinsic width overflowed mobile. Both were fixed and the same checks re-run. Long-title wrapping and hiding an empty-search message during printing were also hardened.

Automated WCAG-tagged checks reported **zero violations in the tested states**, not full conformance. The only incomplete rule reported was SVG text color contrast in the itinerary. The relevant declared foreground/background ratios were separately calculated as **14.95:1 in light mode** and **16.27:1 in dark mode**. Equivalent route text exists outside the SVG. These calculations do not replace screen-reader or comprehensive manual accessibility testing.

Desktop/mobile itinerary, desktop proposal, dark review and mobile briefing screenshots were visually inspected. The pages have readable hierarchy, coherent spacing, closed-card summaries and narrow layouts. PDFs were generated and print expansion/restoration was exercised; final-document pagination must still be reviewed when consumers change content.

## Exact HTML inputs

| Page | UTF-8 bytes | SHA-256 |
| --- | ---: | --- |
| design-proposal/proposal.html | 19,862 | dbd2f76b2135c32f0e94776b4b4f2905435defe198d45e52183df4bec534c69e |
| pr-review/report.html | 19,125 | 0a35e6a2bf1d7d0229d9b8b8b0397f4ab518b6e146c00091f0fdeedaacc23386 |
| trip-publish/trip.html | 22,709 | bd16db5353d64673d120e8591d0f7f53949f9745bd13ea8683f5bdf37bf0f55d |
| pitch-deck/deck.html | 18,599 | f3d7628e3eea9edd4f6bfbcec9b3a1397d50174e79a126e130c6fb88498e2aad |

These are larger than the original baseline shells because they include actual components, interactions and illustrative content. They remain self-contained: no framework, CDN, remote fonts, map tiles, telemetry or storage. Shipped fragments inherit the parent page's styles; they are not standalone pages. The catalog package count remains unchanged.

## Limits

- Browser coverage is Chromium, not Safari/Firefox or native assistive technology.
- Automated scans and selected visual inspection are not a WCAG certification.
- The route component is a schematic, not a geographic map or live flight track.
- Costs are explicit static examples, not a live calculator or quoting system.
- Markdown recipes and component distribution were checked structurally; no new held-out model-generation benchmark was run for this template revision.
- Consumer changes require their own content, privacy, keyboard, contrast, responsive and print checks.
- No commit or push was performed.

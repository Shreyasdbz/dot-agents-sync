# Template refinement — 2026-09-14

This revision responds to direct user feedback about promotional copy, oversized/generic layouts, stalled presentation navigation, insufficient technical components and multi-group mobile travel planning. Prior trial transcripts and verification records remain historical evidence, not current template descriptions.

## Navigation defect and regression

The original browser reproduction clicked Next, waited for normal scrolling, and pressed ArrowRight with the button focused. The reported selection was 1 after Next and remained 1 after ArrowRight, instead of advancing to 3. Two source defects explain the behavior: intersection callbacks could reset explicit navigation during scrolling, and the key handler excluded focused buttons.

The replacement uses explicit slide selection with no intersection observer. Presentation mode shows one slide; Read all slides shows a compact document. Native input/select controls and nested sequence players retain their keys. Print reveals all slides and restores the current mode. The dedicated regression now reports **2 after Next, 3 after ArrowRight**, then passes rapid forward traversal through all eight slides and reverse traversal to slide 1. Dense desktop and mobile slides were also captured and inspected.

Run: `node scripts/test_template_navigation.cjs` with Playwright available in Node resolution. This is a real Chromium interaction test, not a source-pattern assertion.

## Changes

- Shared typography, buttons, borders, spacing and review metadata are more restrained. Live headings identify actual subjects or decisions. Travel uses destinations, local dates, routes, group assignments and booking states instead of slogans. The shared communication policy and Pitch Deck skill carry the same requirement.
- Both technical template packages ship individually loadable bar/line charts, data-flow, entity-relationship, sequence and dense-context fragments. Sequences are opt-in and pausable; every step remains readable without animation. Dense slides use labeled groups and scrolling rather than forced small text or clipped canvases.
- The itinerary uses compact chronological disclosure rows. It demonstrates connecting flights, independent group arrivals, rail, airport transfers, rental vehicles, activities, hotel room allocations, rental houses, apartments and family stays. Shared events name all applicable groups. Known departure instants are ordered using their offsets rather than raw local clock strings.
- Schedule-only group/date filters have an explicit empty state and restore after print; print includes every event. Stays and traveler allocations remain separate. Candidate data and missing accommodation/return coverage are not represented as confirmed bookings.
- Common UI behavior and page-specific deck, sequence and travel modules have separate canonical files. The builder includes only page-specific behavior required by the composition. No external runtime dependency, storage or network request was introduced.

## Verification

The full Python suite passed **70 tests in 57.27 seconds**. Lint, formatting, generated/source parity, the skill validator and package build passed. The new component files are declared in manifests and package-relative Markdown links pass validation.

[Browser results](browser-results.json) record Chromium **151.0.7922.34** and axe-core **4.13.0**. All four pages passed tested 320/390/1440px layouts, dark/light, long-title reflow, no-JavaScript fallback, IDs/anchors, applicable keyboard controls and print-state restoration. Added checks cover group/date intersections, empty schedules, restoration of filtered events, sequence controls, both presentation modes and dense-slide reflow.

Automated accessibility scans reported no violations in the tested states. The line-chart SVG text contrast remains an incomplete automated check; its values are also supplied in an accessible table. This is not screen-reader, cross-browser or WCAG certification. Screenshots were visually inspected for the itinerary, proposal, full document view, and dense slide on desktop/mobile. Generated PDFs and print state are tested; final consumer content still needs pagination review.

Final self-contained HTML sizes: review **22,948 bytes**, proposal **29,589 bytes**, deck **32,277 bytes**, itinerary **34,801 bytes**. This is larger than the preceding version because of the new working components and richer examples; it is not represented as a token reduction.

Deck SHA-256: `ca96b543fe695551b8e41705cd50ece89ff2a035eb03fafdd38f92aa03dd947d`.

Itinerary SHA-256: `13e44f17eac1fbdb44f2701ec506052f983b8690c6196025469eab3a30ccf872`.

Visual quality remains subject to user review. Map schematics are not live routing, cost examples are not calculators, and schedule filters are not privacy controls. No changes were committed, pushed or installed in personal provider configuration.

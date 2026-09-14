# Template system

A small authoring system, not an application framework. Markdown recipes select an appropriate document shape. Shared CSS, progressive JavaScript and semantic HTML fragments compose self-contained HTML examples. Consumers need neither Python nor Node to open or adapt a delivered page.

## Source and delivery boundaries

- `ui.css`: design tokens, layout and component styles, including reflow, theme, focus, motion and print behavior.
- `editorial.css`: proposal, review and presentation shell; compact sticky navigation, neutral themes and document-specific typography. Excluded from travel output.
- `icons.json`: canonical decorative SVG paths, expanded from `{{icon:name}}` at build time. Pair section icons with text; name every icon-only control. `components/page-tools.html` shares theme and print controls across the editorial pages.
- `ui.js`: theme, disclosure controls, hash reveal, print restoration and finding search. No network calls or storage.
- `behaviors/*.js`: separate deck navigation, sequence playback and optional travel currency modules. The builder includes only modules used by the composition. Travel-only styles live in `travel.css`.
- `components/*.html`: reusable charts, data flow, entity models, sequences, dense context, travel events, stays, costs and finding fragments.
- `pages/*.html`: complete worked compositions. `{{component:name}}` includes a local fragment; `{{styles}}` and `{{interactions}}` inline the foundation.
- `packages/templates/*/*.html`: generated distribution files. These are self-contained, not separate runtime applications.
- `packages/templates/*/components.md`: shipped usage contracts and copyable markup, loaded only when needed.
- `packages/templates/*/components/*.html`: shipped, individually loadable fragments generated from the same canonical components. They inherit the entrypoint's foundation; they are not standalone pages.

Edit canonical HTML source rather than generated HTML. Run `python scripts/build_templates.py --page trip` (or proposal/review/deck) to emit an apply_patch-compatible update; apply that patch. `python scripts/build_templates.py --check` detects stale outputs. The normal Python tests enforce exact generated/source parity and shipped Markdown links. Add new fragments under components, reference them from a page, and regenerate; never hand-maintain several copies of the CSS.

The builder processes trusted repository source, not arbitrary external HTML. It is not a sanitization service. Unknown component files fail the build; delivery tests reject unresolved template markers.

## Composing a document

For Markdown, begin at the package entrypoint and load only the relevant recipe. A bug-fix proposal should explain the failing contract, correction and regression evidence; a feature needs journeys and interfaces; a migration needs intermediate compatibility and reversibility. Cross-cutting sections are optional, not a completeness quota. Plan Context remains schema-bound rather than becoming free-form Markdown.

For HTML, begin with the appropriate worked page. Replace sample content from approved evidence, select useful components, remove irrelevant examples and preserve their semantics. The examples intentionally label their data as illustrative: they are not final travel plans, reviewed PRs or accepted designs. Keep one source of truth for facts across formats.

Use direct headings, restrained type and compact organization. Labels should identify a subject, date, place, action, state or decision; do not insert slogans, poetic day names or paragraphs advertising the document's usefulness. Dense information is appropriate when it serves the task. This is consistent with research on concise, scannable, non-promotional web writing, not a claim that one visual style suits every product. [NN/g writing study](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/)

The travel view has a headline, horizontal route preview with one trip paragraph, compact type-specific reservations, detailed daily timelines, to-dos and metadata. The preview wraps for print. Use names for split plans; no group/date filters. Transport-colored outgoing timeline segments also name their modes in text. Events carry local dates/zones and booking state; order known instants chronologically rather than sorting wall-clock strings across zones. Stays separate units, bedrooms, beds and occupant allocation. Optional copy controls use visible references/addresses and report blocked clipboard access honestly.

Presentations use explicit selection, not intersection-based slide state. Arrow keys work when Next/Previous has focus; native editors and nested sequence controls retain their keys. Read all slides removes slide-sized whitespace. Dense slides use grouped content and scrolling rather than clipped fixed-height canvases. All slides appear without JavaScript and in print.

Animated sequences are opt-in, pausable and non-looping, with every step available as static text. No essential explanation depends on watching the animation. [WAI animation and user-control guidance](https://www.w3.org/WAI/tutorials/carousels/)

## Component decisions

**Disclosures:** native details/summary, closed by default. Multiple cards may be open. Essential dates, status, totals and warnings remain visible. Do not hide a critical caveat inside a collapsed body. This follows the distinction between optional supporting detail and information most readers need. [GOV.UK details guidance](https://design-system.service.gov.uk/components/details/)

**Keyboard and state:** native controls supply semantics and Enter/Space behavior. Do not add a second conflicting ARIA state to native details. Custom disclosure controls would need an explicitly synchronized expanded state and associated content. [WAI disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/)

**Reflow and targets:** layouts collapse at narrow widths; tables scroll inside named regions rather than widening the page. Buttons and navigation links use at least 44px vertical targets as this system's design choice, not a claim that every WCAG target rule mandates 44px. Long titles and controls are tested at 320px. [WCAG reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)

**Charts and route drawings:** visible values, units, denominators and caveats remain in text. The route component is a schematic; a real geographic map needs verified coordinates, projection, routing provenance and antimeridian handling. It must not imply live tracking. SVG includes a title/description and equivalent route text.

**Totals:** the travel page optionally converts immutable USD estimates using explicit per-currency rates, without live requests. The sample rate is illustrative, not current. Consumers must reconcile line items, preserve original booking amounts/currencies and replace sample rates with dated sources. This is not a live quote or payment service.

**Printing:** disclosures open before printing and restore afterward, including repeated browser print events. Filtered findings are included in print so a search cannot silently remove evidence. Print controls and empty-search notices do not appear. Browser tests generate PDFs; pagination still needs review for each materially different finished document.

**Privacy:** no telemetry, external assets or local storage. Never place private facts in hidden DOM, comments or scripts. Collapsed content remains part of the file. Safe text insertion and URL validation are the consumer's responsibility; static examples do not sanitize untrusted markup.

## Verification

Run the ordinary Python suite and `python scripts/build_templates.py --check`. Browser acceptance uses `node scripts/test_templates.cjs OUTPUT_DIRECTORY` with Playwright available through Node resolution. Set `AXE_PATH` to a local axe-core script to include automated WCAG-tagged checks; results explicitly say not-run when absent. Dependencies are test tooling, not shipped runtime requirements.

Browser checks cover closed defaults, keyboard toggling, expand/collapse, hash reveal, repeated print restoration, finding search/empty states, all-findings print, deck navigation, light/dark, narrow layouts, long titles, IDs/anchors, no-JavaScript fallback and page errors. Captured screenshots and PDFs are evidence for the test fixture, not all possible consumer compositions.

Run `node scripts/test_template_navigation.cjs` for the focused navigation regression: Next → ArrowRight with button focus, followed by rapid traversal across the complete deck with normal motion. The main browser checks also cover travel currency round trips, day disclosures, step controls and both presentation modes.

Do not call an automated audit full accessibility certification. Screen-reader/assistive-technology testing, non-Chromium engines and final-document content accuracy remain distinct gates.

See the [latest refinement evidence](../evals/runs/template-refinement/README.md) for the navigation reproduction, expanded component coverage, current sizes and browser results.

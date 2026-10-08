# Template system

A small authoring system, not an application framework. Markdown recipes select an appropriate document shape. Shared CSS, progressive JavaScript and semantic HTML fragments compose self-contained HTML examples. Consumers need neither Python nor Node to open or adapt a delivered page.

## Source and delivery boundaries

- `ui.css`: design tokens, layout and component styles, including reflow, theme, focus, motion and print behavior.
- `brand.css`: optional workspace logo/name/label slots and type tokens, appended after format styles. It activates only with `data-workspace-brand` on the root; private colors and assets come from an authorized context, not the public catalog.
- `editorial.css`: proposal, review and presentation shell; compact sticky navigation, semantic light/dark palettes and document-specific typography. Excluded from travel output.
- `visual.css`: typed diagram shapes, semantic lanes, identity tracks, actor selection and composition/motion tokens; included only for editorial pages containing slides, sequences or process diagrams.
- `icons.json`: canonical decorative SVG paths, expanded from `{{icon:name}}` at build time. Pair section icons with text; name every icon-only control. `components/page-tools.html` shares theme and print controls across the editorial pages.
- `ui.js`: theme, disclosure controls, hash reveal, print restoration and finding search. No network calls or storage.
- `quiz.css` and `behaviors/quiz.js`: visual question layout, immediate all-option explanations, retry, per-snapshot progress and print restoration. Only quiz pages include them. Answers are session-only; history is preserved HTML content.
- `explanation.css`: scrollable before/after mechanisms and integrated perspective rows, included only in change explanations; interactions use the shared page tools and disclosures.
- `behaviors/*.js`: separate deck navigation, sequence playback and optional travel currency modules. The builder includes only modules used by the composition. Travel-only styles live in `travel.css`.
- `components/*.html`: reusable charts, data flow, entity models, sequences, dense context, travel events, stays, costs and finding fragments.
- `pages/*.html`: complete worked compositions. `{{component:name}}` includes a local fragment; `{{styles}}` and `{{interactions}}` inline the foundation.
- `packages/templates/*/*.html`: generated distribution files. These are self-contained, not separate runtime applications.
- `packages/templates/*/components.md`: shipped usage contracts and copyable markup, loaded only when needed.
- `packages/templates/*/components/*.html`: shipped, individually loadable fragments generated from the same canonical components. They inherit the entrypoint's foundation; they are not standalone pages.

Edit canonical HTML source rather than generated HTML. Run `python scripts/build_templates.py --page trip` (or proposal/review/deck/quiz/explanation) to emit an apply_patch-compatible update; apply that patch. `python scripts/build_templates.py --check` detects stale outputs. The normal Python tests enforce exact generated/source parity and shipped Markdown links. Add new fragments under components, reference them from a page, and regenerate; never hand-maintain several copies of the CSS.

The builder processes trusted repository source, not arbitrary external HTML. It is not a sanitization service. Unknown component files fail the build; delivery tests reject unresolved template markers.

## Composing a document

For Markdown, begin at the package entrypoint and load only the relevant recipe. A bug-fix proposal should explain the failing contract, correction and regression evidence; a feature needs journeys and interfaces; a migration needs intermediate compatibility and reversibility. Cross-cutting sections are optional, not a completeness quota. Plan Context remains schema-bound rather than becoming free-form Markdown.

For HTML, begin with the appropriate worked page. Replace sample content from approved evidence, select useful components, remove irrelevant examples and preserve their semantics. The examples intentionally label their data as illustrative: they are not final travel plans, reviewed PRs or accepted designs. Keep one source of truth for facts across formats.

For a selected `context.workspace-artifacts`, follow the Visual Artifacts lookup before styling. Set `data-workspace-brand` on `html`, inline its authorized CSS after all format styles and embed the needed assets as data URLs. Use an unchanged logo image with class `brand-logo`, adjacent text `brand-name`, and an optional artifact type `brand-label` inside `.brand`. A decorative mark beside the workspace name has empty alt text; a standalone identity needs meaningful alt text. Preserve intrinsic aspect ratio. Explicit light, explicit dark, system dark and print need separate override coverage; preserve semantic diagram/status roles. Never ship a binding path, private context body, expiring asset URL or unrelated workspace brand. With no selected brand the worked templates use their default palette and hide supplementary opening scenes.

Use direct headings, a readable type hierarchy and compact organization. Let expressive scale, semantic colors and distinct shapes clarify explanatory scenes. Labels should identify a subject, date, place, action, state or decision; do not insert slogans, poetic day names or paragraphs advertising the document's usefulness. Dense information is appropriate when it serves the task. This is consistent with research on concise, scannable, non-promotional web writing, not a claim that one visual style suits every product. [NN/g writing study](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/)

Selected workspace branding also activates `.artifact-cover`: an asymmetric opening with `.artifact-cover-copy` beside a subject-specific `.artifact-cover-visual`, stacked below 800px. Without a selected workspace, wrappers use `display:contents` and the supplementary cover visual is hidden. Replace the worked identity, cache, ownership or dated-route scene with evidence for the document; these are fictional examples, not decorative brand graphics. Keep visible HTML labels readable at narrow widths rather than shrinking a desktop SVG. The identity scene's orbit lines are decorative; the three labeled paths explain the invariant in text. Do not reuse that scene for an unrelated subject.

Each worked page identifies its format with `data-artifact-kind` on `html`: `proposal`, `review`, `deck`, `quiz`, `trip` or `explanation`. Scope private format treatments beneath both this attribute and `data-workspace-brand`. Use a common identity while varying canvas, accent balance, type scale, density and organization according to the reading task. These hooks have no visual effect on their own. Test explicit light/dark, system dark, print and narrow layouts for each materially different treatment.

Use composition according to purpose: a cover makes the question clear, an evidence view gives the diagram or comparison most of the space, aligned ruled rows hold reference information, and bounded surfaces mark interactive choices or ownership boundaries. Avoid enclosing every paragraph in the same card. A selected private context should record source observations, chosen adaptations and measured render results separately. Reference sites inspire hierarchy and rhythm; their copy, images, proprietary typefaces and animations are not template assets.

The travel view has a headline, horizontal route preview with one trip paragraph, compact type-specific reservations, detailed daily timelines, to-dos and metadata. The preview wraps for print. Use names for split plans; no group/date filters. Transport-colored outgoing timeline segments also name their modes in text. Events carry local dates/zones and booking state; order known instants chronologically rather than sorting wall-clock strings across zones. Stays separate units, bedrooms, beds and occupant allocation. Optional copy controls use visible references/addresses and report blocked clipboard access honestly.

Presentations use explicit selection, not intersection-based slide state. Arrow keys work when Next/Previous has focus; native editors and nested sequence controls retain their keys. Read all slides removes slide-sized whitespace. Dense slides use grouped content and scrolling rather than clipped fixed-height canvases. All slides appear without JavaScript and in print.

Animated sequences are opt-in, pausable and non-looping, with every step available as static text. No essential explanation depends on watching the animation. [WAI animation and user-control guidance](https://www.w3.org/WAI/tutorials/carousels/)

The payment example pairs a labeled SVG ownership/request/recovery graph with equivalent text. The sequence synchronizes persistent actors with the selected step using data-phases; it stops on document, slide or disclosure hiding and before print. Deck entrances follow immediate selection, cancel on rapid navigation and honor reduced-motion changes. These are working examples, not a mandatory palette, diagram shape or effect for every artifact. Apply skill.visual-artifacts for the subject-specific visual decisions.

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

Set BROWSER_EXECUTABLE_PATH to an installed Chromium-compatible browser when the Playwright-managed binary is unavailable. Run `node scripts/test_visual_artifacts.cjs OUTPUT_DIRECTORY` for measured semantic contrast in both themes, key-path movement and reversal, synchronized actor selection, terminal replay, rapid slide traversal, reduced-motion changes, disclosure hiding, zoom-equivalent reflow and print/static fallbacks. Browser captures still need visual inspection.

Browser checks cover closed defaults, keyboard toggling, expand/collapse, hash reveal, repeated print restoration, finding search/empty states, all-findings print, deck navigation, light/dark, narrow layouts, long titles, IDs/anchors, no-JavaScript fallback and page errors. Captured screenshots and PDFs are evidence for the test fixture, not all possible consumer compositions.

Run `node scripts/test_template_navigation.cjs` for the focused navigation regression: Next → ArrowRight with button focus, followed by rapid traversal across the complete deck with normal motion. The main browser checks also cover travel currency round trips, day disclosures, step controls and both presentation modes.

Do not call an automated audit full accessibility certification. Screen-reader/assistive-technology testing, non-Chromium engines and final-document content accuracy remain distinct gates.

See the [latest refinement evidence](../evals/runs/template-refinement/README.md) for the navigation reproduction, expanded component coverage, current sizes and browser results.

Quiz checks run with `node scripts/test_change_quiz.cjs`, using host-provided Playwright. They exercise immediate feedback for all four options, retry isolation, independent snapshot progress, keyboard controls, history, deep links, repeated print restoration, themes, reflow, text zoom, no-JavaScript reading and invalid-question handling. Evidence is saved in a temporary directory. These checks use fictional contracts and do not establish model question quality.

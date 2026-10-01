# Presentation UI components

Start from the decision and source, then choose only the slides needed. The example deck's pilot story is sample content, not a mandatory outline.

## Slide recipes

- **Decision:** direct subject/decision title, recommendation, and necessary status. No decorative eyebrow or slogan is required.
- **Comparison:** two columns or a captioned table with consistent criteria; omit unsupported scores.
- **Evidence:** metric with denominator, period and source; distinguish baseline, estimate and target in visible text.
- **Process:** ordered .flow sequence; only use when order matters.
- **Deep dive:** dense code, contracts, tables or diagrams when understanding requires that context together. Use an appendix only for genuinely supplementary detail.
- **Ask:** specific decision, resources if known, success/stop conditions and unresolved authority.

Each section.slide needs a unique id and a meaningful h1/h2. In JavaScript presentation mode exactly one slide is visible; Read all slides reveals the document. Without JavaScript all slides remain readable. ArrowLeft/Right, PageUp/Down and Home/End navigate even when Next/Previous has focus. Inputs, selects, editable content and nested sequence players retain their own keyboard behavior. Navigation state does not depend on a scroll observer. Dense slides may scroll vertically; printing includes every slide.

Use .bars only for a clearly stated comparable scale with values in text. Recompute widths from the source, retain units and distinguish goals from measured results. Do not imply a forecast through bar length or hide uncertainty in notes.

The controls use .deck-controls with data-prev/data-next buttons, one labeled select, role=status and a labeled progress element. Remove unused controls rather than leave inert buttons. Print creates one slide section per page; check actual page breaks for dense content.

## Foundation contract

Use the compact header from the worked page. Document navigation keeps icon + text labels; familiar utility actions use 44px icon buttons with accessible names and hover titles. Icons are inline SVG with a consistent 24px viewBox and 1.6px stroke, hidden from assistive technology when the adjacent text or button name already conveys their meaning. Theme icons show the applied theme, including system-theme changes. Keep status and severity in words; never rely on an icon or color alone.

Write headings as subjects, decisions or actions. Put the conclusion and material uncertainty first, then supporting evidence. Remove slogans, duplicate summaries and authoring instructions from the delivered page. Keep a short, visible sample label while demonstrating invented content. Native disclosures hold secondary detail, not the verdict, recommendation or critical caveat. Use tables for comparable values, diagrams for actual relationships, and plain paragraphs for everything else.

The header stays visible with a solid-color fallback and progressive background blur. Narrow document navigation scrolls within the header; the page itself must not overflow. Print removes navigation and controls. Preserve comfortable text size and reading measure as the content area widens; dense reference material can use the available width without turning ordinary paragraphs into full-width text.

The HTML entrypoint includes CSS and JavaScript and works offline without third-party assets. Reuse semantic markup and the existing class/data attributes; do not import a framework. CSS custom properties control colors, radius and type. Change tokens first, then layout only where the content needs it. Test both themes after customization.

Shared components: .panel (content group), .grid (two columns collapsing on narrow screens), .metrics with dt/dd (summary values), .badge plus explicit text (status), .callout (consequential note), .table-wrap with a named region and tabindex=0 (wide table), .empty (honest empty state), .source-list (evidence).

A collapsible card uses native details/summary and omits the open attribute. Keep the title, status and essential summary outside the hidden detail body. Do not nest links or buttons inside summary. Keyboard Enter/Space toggles it natively; custom aria-expanded is unnecessary on native details. Every copied id and matching anchor/title reference must be unique.

```html
<details class="disclosure" id="unique-item">
  <summary><span><span class="summary-title">Specific outcome or day</span>
    <span class="summary-meta">Date / status / essential constraint</span></span></summary>
  <div class="detail-body"><p>Supporting information.</p></div>
</details>
```

Theme and print buttons use data-theme-toggle and data-print, with hidden in the source; JavaScript reveals them when operational. No theme preference or private content is stored. data-expand=all and data-expand=none control the page's disclosure cards. Deep links reveal enclosing details. beforeprint opens cards and restores them afterward; inspect actual PDF output for clipping.

## Safe composition and delivery

Treat the entrypoint's content as an explicitly illustrative fixture. Replace its facts, headings and evidence with authorized source material; delete unused components, examples and authoring comments. Never hide private content in comments, data attributes, scripts or collapsed cards. Escape untrusted text, and use textContent for runtime text insertion. Only include verified safe links; disallow javascript: and untrusted embedded HTML. The examples are not a sanitizer for arbitrary input.

Deliver one self-contained HTML file. Read only the relevant modules, retain semantic headings/landmarks, and verify keyboard operation, 320px reflow, dark mode, reduced motion, print and long content. An attractive screenshot does not certify accessibility. Without a browser, report visual and interactive validation as outstanding.

## Technical components

Load individual fragments instead of the entire collection: [bar chart](components/chart.html), [line chart with data table](components/line-chart.html), [data flow](components/data-flow.html), [entity relationships](components/entity-relationship.html), [step-through sequence](components/sequence.html), and [dense context](components/dense-context.html).

Use charts only with consistent scales, units, periods and denominators; distinguish measured data from targets. Keep visible values and chart data synchronized. The line chart's table supplies equivalent values without relying on the graphic. A data-flow diagram names producers, stores, consumers and edge semantics. An entity model states keys, cardinality and optionality explicitly; boxes alone are not a relationship model.

Sequence steps remain readable together. The actor scene keeps the same identity across persist, send, recover and record; data-phases lists zero-based step indices for each actor. The sequence controller synchronizes data-scene-active with the current step and exposes aria-current=step. A visible selected-step label supplements color. Adapt the actors and mapping together when changing the source story; the illustrative provider guarantees are not verified facts.

Play is opt-in, pausable and stops at the end; activating Play at the end replays from the first step. Back/Next step controls work without animation. Playback stops when the document, owning slide or enclosing disclosure hides and before printing. Reduced motion removes transitions without hiding meaning. Print keeps all steps and actor roles, omitting the transient selection. Copy unique IDs and SVG title/description/marker references when placing several components on one page.

The data-flow SVG separates application ownership from the external provider, labels directed request/confirmed-result paths, and names the dashed unknown-outcome branch in its visible legend. A named scroll region preserves readable geometry on narrow screens; the adjacent node list and recovery text supply the full relationship without following the drawing. Adapt endpoints, labels and text together. The sequence scene supplies temporal state; the data-flow drawing supplies architecture, not a claim of request timing.

The deck changes selected state immediately and uses a short directional entrance only for a new slide in presentation mode. Rapid navigation cancels the previous animation. Read-all and print cancel entrances; reduced-motion preferences skip them. The shell supplies motion tokens, not a requirement to animate every element. Apply the Visual Artifacts workflow for subject-specific composition and explanatory visuals beyond these examples.

Dense context is intentional: use labeled groups, contracts, code, tables and cross-references when readers need them simultaneously. Keep normal body text readable; do not shrink a crowded slide to force it into a fixed canvas. Allow vertical scrolling or split at a meaningful boundary. Sparse summary slides and dense reference slides may coexist.

## Semantic palette and path motion

The worked theme uses navy ink, violet execution, teal storage and amber external services, with separate light/dark surfaces. The architecture uses a request document, storage cylinder, execution hexagon and an external double outline. Keep semantic colors and shape meanings consistent when adapting the example; add a legend for a new grammar. Measure actual text and essential graphic contrast in both themes rather than trusting token names.

The recovery track moves one labeled key between persistent actors over 720ms, with a 1.8-second opt-in playback cadence. These are explanatory timings, not system latency. data-scene on each step supplies the selected explanation through textContent. The four endpoint coordinates and the return lane live in the sequence behavior; update that mapping and SVG geometry together when changing actors or steps. State commits before movement, and pause, hiding or reduced-motion changes cancel the effect while keeping its selected endpoint. The static track and all step descriptions remain available without JavaScript; print omits the transient key and readout.

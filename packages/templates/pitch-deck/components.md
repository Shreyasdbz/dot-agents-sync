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

Sequence steps remain readable together. Play is opt-in, pausable and stops at the end; no autoplay or looping. Back/Next step controls work without animation. Reduced motion removes transitions without hiding meaning. Copy unique IDs and SVG title/description references when placing several components on one page.

Dense context is intentional: use labeled groups, contracts, code, tables and cross-references when readers need them simultaneously. Keep normal body text readable; do not shrink a crowded slide to force it into a fixed canvas. Allow vertical scrolling or split at a meaningful boundary. Sparse summary slides and dense reference slides may coexist.

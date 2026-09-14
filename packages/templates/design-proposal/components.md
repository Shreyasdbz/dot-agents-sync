# Proposal UI components

Copy the [comparison fragment](components/comparison.html) into the entrypoint when alternatives share meaningful criteria. It inherits the page foundation; it is not a standalone document.

Use a decision-first hero, short metadata/status, a visible recommendation callout and section navigation. Reuse the Markdown decision record; the HTML must not strengthen uncertain claims.

Choose a layout by proposal type: bug fix uses contract → failure path → correction → regression evidence; feature uses journey → boundaries → alternatives → validation; migration uses compatibility states → cutover → reversibility. Do not preserve the example payment narrative in unrelated work.

Use .flow with an ordered list for a real sequence, not decorative boxes. Use a captioned comparison table when alternatives share actual criteria. Keep the recommendation visible; place supporting failure-path or compatibility detail in collapsed cards. Critical caveats must stay visible.

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

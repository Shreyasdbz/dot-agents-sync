# Review UI components

Copy the [finding fragment](components/finding.html) into the entrypoint for each supported finding. It inherits the page foundation; remove its illustrative content.

Compose a verdict hero, scope/revision metadata, accurate summary metrics, finding cards and a verification section. The canonical review model owns findings; the UI never calculates a verdict from color or count.

A finding card is details.disclosure with data-finding. Its summary carries severity text, title and exact location; its body carries trigger, consequence, evidence, correction and verification. Copy the existing card and assign unique IDs when linking to findings. Zero findings needs an explicit scope-limited conclusion, not a fake sample card.

Optional search uses an input with data-filter inside a hidden .filter-bar, a visible label, a data-filter-status live region and a data-empty message. It matches finding text locally; no content leaves the page. Keep the verdict and total findings unchanged when filtering. Printing includes every finding, not merely current matches. Remove the filter if the report is short.

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

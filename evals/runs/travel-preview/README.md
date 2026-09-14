# Travel preview and reservation refinement

Verified locally on 14 September 2026; uncommitted. Prior dirty work was preserved.

At a glance now uses one trip paragraph and six linked route stops in a horizontally scrolling region. Keyboard scrolling stays inside the region; print wraps all stops into three columns. Flights have route-focused cards, stays have compact lodging rows and tickets have a distinct dashed treatment with appropriate icons. Reservation columns collapse on mobile. Date tiles include lowercase weekdays. Dark mode uses neutral charcoal surfaces with light text.

The reusable copy-details fragment demonstrates confirmation and address fields with explicitly marked placeholder values. Buttons copy visible text only on click, announce successful completion only after resolution, and select text with manual-copy guidance when clipboard access is denied or missing. The template is not an authentication or privacy boundary; real references and addresses require authorized content and export review.

## Checks

- Python: 70 passed in 54.84 seconds.
- Ruff lint and format checks, generated/source parity and whitespace checks passed.
- All four template browser regressions passed in Chromium 151.0.7922.34 at 320/390/1440 widths with long-title reflow, keyboard disclosures, print restoration, no-JavaScript fallback and light/dark states.
- Focused travel regression passed currency cases, horizontal keyboard scrolling, print width, system-dark paper colors, nine weekday labels and clipboard success/denied/unavailable behavior. Clipboard tests use a controlled double and do not write the system clipboard; native OS clipboard interoperability is not certified.
- Visually inspected mobile reservations and the charcoal route preview. Screenshots and PDFs are under /private/tmp/dasync-travel-preview; focused captures include /private/tmp/dasync-travel-preview-dark.png and /private/tmp/dasync-travel-reservations.png.

Axe 4.13.0 found no violations but retained incomplete contrast checks on some route text and decorative arrows; raw results are in browser-results.json. Separately calculated declared foreground/background contrasts: light muted 5.57:1, dark muted 9.74:1, light primary 10.84:1, dark primary 15.55:1. These calculations and visual inspection do not constitute screen-reader, user usability or full accessibility certification. Safari/Firefox and native clipboard behavior remain untested.

Run scripts/test_templates.cjs with Playwright through NODE_PATH and optional AXE_PATH, plus scripts/test_travel_currency.cjs. Browser launch required macOS sandbox escalation. Python used the temporary uv cache at /private/tmp/dasync-audit-uv-cache.

Final trip.html: 57,387 bytes, within its existing 60 KB guard. SHA-256: cfbefcc0639b88146b615e775d18088ea1077312c373bf452821b7d18fe683fb. No external fonts, images, network requests or runtime dependencies were added.

# Visual artifact checks · 2026-09-30

This change adds original visual-authoring guidance and working template examples. Inspiration and inspected sources are recorded in [composition.md](../../../packages/skills/visual-artifacts/composition.md#inspiration-and-provenance). The two visual-artifacts cases in cases.json are future model-evaluation scenarios; neither has a recorded model run. The evidence below establishes catalog distribution and example-template behavior, not comparative model quality or native instruction activation.

## Executed checks

`UV_CACHE_DIR=/private/tmp/dasync-visual-uv uv run pytest -q`: 180 passed. The first sandboxed attempt could not download wheel-build dependencies and also exposed the prior 40KB template-size gate; the final run used network access for temporary test installations. Deck/proposal budgets are now 50KB to accommodate inline SVG, actor scenes and local motion; actual generated sizes are 47,643 and 45,526 bytes. No shipped runtime dependencies were added.

`uv run ruff check cli tests packages/hooks`, `uv run ruff format --check cli tests packages/hooks`, `uv run python scripts/build_templates.py --check` and skill-creator's quick_validate.py for visual-artifacts passed. Tests install the shared visual skill and its loadable references through the Engine for Codex, Claude, Copilot and Cursor in temporary projects and verify an idempotent sync.

Browser checks used Playwright from the host runtime and isolated Google Chrome 154.0.8037.93 via BROWSER_EXECUTABLE_PATH. Reproduce with NODE_PATH pointing to a local Playwright installation and BROWSER_EXECUTABLE_PATH pointing to a Chromium-compatible executable:

```sh
node scripts/test_templates.cjs /private/tmp/dasync-visual-browser-final
node scripts/test_visual_artifacts.cjs /private/tmp/dasync-visual-browser
node scripts/test_template_navigation.cjs
```

All three passed. General acceptance covers the deck, proposal, review and travel fixtures: light/dark, 320/390/1440px reflow, long headings, unique IDs, fragment links, navigation, disclosures, no-JavaScript fallback, printing and no page errors. Focused checks cover actor/step synchronization, manual stepping, pause, terminal replay, playback completion, hidden slide/disclosure stopping, rapid reversals, dynamic reduced-motion cancellation, static print and a zoom-equivalent viewport. The initial focused test checked cancellation before the media-query change event arrived; it now waits for the captured animation to become idle, distinguishing cancellation from natural completion.

Rendered desktop flow, selected recovery actor and narrow sequence captures were inspected. That inspection removed the redundant desktop node list and corrected an edge so the worker, rather than the provider, records the result. Narrow layouts retain the adjacent text representation. Captures wait for finite transitions to settle, preserving the selected state accurately. PDF output was generated; complete pagination review remains outstanding.

## Limits

Chromium checks do not establish Safari/Firefox behavior or screen-reader conformance. axe-core was unavailable, so automated accessibility audits are explicitly not-run; keyboard, accessible names and reflow checks are separate evidence. A 640px layout viewport approximates reflow at 200% zoom but is not an actual browser zoom action. The diagrams and payment claims remain labeled illustrative, with unverified provider guarantees. No independent reviewer or model evaluator ran.

## Color, shape and motion refinement · 2026-10-01

The second pass changes the shipped examples as well as the guidance: navy ink with violet execution, teal durable state and amber external/uncertain outcomes; separate light/dark surfaces; request documents, storage cylinders, execution hexagons and external double outlines; stronger chart/data-model hierarchy; and a persistent key moving along the recovery path with a synchronized selected explanation. Navigation uses a directional 420ms arrival; the key path uses 720ms within an opt-in 1.8-second step cadence. These are illustrative explanatory timings.

The visual browser runner measures 14 foreground/background pairs in each theme, requiring 4.5:1 for checked text and 3:1 for checked essential graphics. This is a bounded token-pair check, not an audit of every rendered text node. It exercises actual key motion, endpoint cancellation on reversal, actor/step synchronization, pause/replay/end, hidden scenes/disclosures, dynamic reduced motion, 320px and zoom-equivalent reflow, print and no-JavaScript use. An opened proposal disclosure initially widened the mobile page to 669px; constraining its grid track fixed the reproduced regression. General browser checks now include that open state.

Working-tree verification passed 180 Python tests, Ruff checks/format and generated parity; the working tree also contains five preserved unrelated edits. Headless Chrome 154.0.8037.93 passed all four template acceptance fixtures and the visual runner. All eight A4 deck pages were rendered with Poppler and inspected without clipping. Browser screenshots were inspected in light/dark, desktop and narrow layouts. Artifacts remain in /private/tmp/dasync-visual-v2-browser, /private/tmp/dasync-visual-v2-general and /private/tmp/dasync-visual-v2-print rather than the catalog.

Deck/proposal HTML is approximately 56/54KB after adding the geometry, theme tokens and path behavior; the fixture limit is now 60KB, while review/travel limits are unchanged. The shared skill's larger supporting-reference budget does not enlarge its entrypoint. The proposal reference-package budget is 22,000 approximate tokens; deck remains at 20,000. There are no new runtime libraries or remote assets.

Axe, assistive technology, non-Chromium engines, actual browser zoom and behavioral model evaluations remain unrun. The zoom-equivalent viewport and template fixtures do not prove arbitrary generated artifacts will have the same quality.

The clean 5a24b69 snapshot passed all 178 committed Python tests. A final print-state check found that explicit dark mode retained dark semantic fills; the follow-up resets those fills for print and adds a dark-to-print browser assertion. Focused template tests, generated parity and the full visual browser runner passed after that correction.

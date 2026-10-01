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

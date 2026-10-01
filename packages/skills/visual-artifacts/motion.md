# Motion for explanations and continuity

Animate a meaningful change, not the presence of a page. A transition can show continuity between states; a traced path can explain movement; a synchronized highlight can connect a selected step to the responsible actor. Keep the final meaning readable at rest. Do not make motion mandatory in an artifact whose question is static.

## Define the change

For each effect, identify the user action or trigger, persistent object, changed property, destination state and static equivalent. Keep unrelated elements still. Use short feedback for controls, slightly longer continuity for a scene change, and reader-controlled pacing for multi-step mechanisms. Choose durations by what must be followed; roughly 120–220ms for feedback and 200–400ms for a scene change are starting ranges, not correctness thresholds.

Prefer opacity and transform for scene continuity. Use stroke or position only when it encodes an actual path. Do not animate layout dimensions on every frame or add a library for a fade. CSS transitions or the Web Animations API usually suffice for a portable file; use the established application library when already present. Avoid scroll hijacking, parallax, unbounded particles, flashing and perpetual decorative loops.

## Preserve control and meaning

Apply state changes immediately; animation follows the state and must never block navigation or input. Cancel or replace an in-flight animation when input changes. Rapid Next/Back must end at the selected state without stale callbacks restoring an earlier scene. Never use animation completion as the only way to show essential content.

Temporal explanations need Back/Next, a visible step/status, and an opt-in Play/Pause that stops at the end. Replay should restart deterministically. Keep all steps available as text. Stop playback when the document or owning scene becomes hidden and before printing; do not continue announcing invisible steps. Give nested players ownership of their controls so deck navigation does not consume them. Do not stream every frame into a live region.

Honor prefers-reduced-motion in CSS and JavaScript, including preference changes during use. Replace movement with an immediate state update and a clear selected-state label; controls and explanations remain functional. Initial markup must remain readable without JavaScript. Print all relevant states as static text or small multiples, remove controls, and avoid printing a transient half-transition.

MDN documents the [reduced-motion media query](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Using_for_accessibility); WAI describes [user control of animated content](https://www.w3.org/WAI/tutorials/carousels/). Inspected 2026-09-30. These API and accessibility references do not prescribe a mandatory animation style.

## Verify temporal behavior

Check start, middle and terminal states; pause/resume/replay; rapid reversal; keyboard operation; scene/document hiding; reduced motion; and print. Observe the rendered transition at normal motion as well as testing final DOM state. Look for flicker, identity jumps, unexpected movement and delays. A screenshot cannot establish timing or cancellation behavior.

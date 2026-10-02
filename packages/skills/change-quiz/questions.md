# Write and challenge the questions

Use application and prediction: ask what happens to a concrete request, record, customer or failure under the changed mechanism, which boundary owns a decision, or which sequence follows from the contract. Supply necessary initial state and assumptions. Avoid vague “best” answers when the implementation has a determinate behavior; distinguish “what the code does” from “what the requirement intends.”

## Four plausible choices

Draft the supported answer first, then three distinct misconceptions rooted in the evidence: pre-change behavior, a nearby but different ownership boundary, confusing enqueue with completion, expecting atomicity across services, wrong retry scope, different tenant/cache key, or confusing configured intent with observed execution. These examples are optional, not a universal distractor recipe. Each option must be credible to someone who partly understands this exact change. If three credible alternatives cannot be written, change the scenario or drop the question; never pad with a joke or impossible behavior.

Keep choices mutually exclusive, comparable in detail, length and grammatical form. Avoid all/none-of-the-above, overlapping ranges, combined independent claims, negative/trick stems, unsupported universal words, and consistently making the correct option the longest. Distribute correct letters without a recognizable pattern, but never sacrifice correctness to a quota. Do not make a correct answer depend on unstated deployment facts or an opinion about the preferred design.

Challenge each option against the same scenario and evidence. Could another be correct under a reachable interpretation? Could someone answer by grammar, answer length, repeated phrasing or a label in the diagram? Does the right answer distinguish the actual mechanism from a plausible alternative? Repair ambiguity and clues before delivery. Sources need to establish both why the keyed option holds and which assumption invalidates each distractor.

## Visual and feedback contract

Every question's visual should be needed to reason about it: mark a missing step in a sequence, an uncertain branch, a before/after state, ownership lanes, or alternative paths. Do not reveal the answer through a green path, answer-bearing caption, title, alt text or code attribute used as an accessible name. The accessible text equivalent must supply the same scenario information as the drawing. Keep explanatory annotations and full source details below the answers, revealed with feedback. Neutral scenario facts remain visible.

For every option, write a concise explanation naming the mechanism, the mistaken assumption if wrong, and the resulting consequence. “Incorrect” alone teaches nothing. Explain the correct option too. Cite file paths, symbols and pinned line ranges in feedback where available; tests/requirements/external guarantees keep their separate evidence roles. Use safe pinned links if available and readable paths otherwise. Do not fabricate line numbers. For a diagram whose answer is a hidden intermediate state, reveal the completed relationship only in feedback, with an equivalent text explanation.

Selecting any radio option immediately reveals all four explanations and a textual selected/correct result without moving focus. Subsequent selections update the result; Retry clears only that question. A progress count measures answered questions, not understanding or deployment readiness. Answers are embedded in this learning file, not secret exam keys. Session state resets on reload; revision history is durable HTML content, not answer persistence.

## Grounding and calibration

Use the dated [research record](research.md) when revisiting pedagogical choices. Do not add claims of validated learning gains or label a model-generated quiz reliable solely because it meets HTML structure. Check every scenario and explanation against its source snapshot. A useful final self-check tries the strongest alternative reading, not merely whether the keyed letter matches the markup.

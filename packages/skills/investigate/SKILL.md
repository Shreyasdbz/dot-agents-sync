---
name: investigate
description: "Investigate a question or failure and return evidence and cause inline."
---

# Investigate

Given a question, failure, or unexplained behavior, trace the evidence across code, configuration, logs, connected systems, and available context. Determine the most defensible causal explanation while keeping observed facts, inferences, competing explanations, and verification gaps distinct.

- Default inline output: Return the direct answer or most likely explanation, supporting evidence, causal chain, facts versus inferences, competing explanations considered, remaining uncertainty, and the smallest useful next action.

- Uncertainty: If the cause is not proven, say so directly. Do not manufacture certainty, treat observed activity as a verified outcome, or collapse multiple plausible causes into one unsupported conclusion.

- Optional outputs: After the inline result, offer Create Pitch Deck and Create Markdown Report. The user may choose either or both. If the original invocation already requests an option, produce it without asking again.

- Pitch Deck option: Invoke the Pitch Deck skill with the completed investigation as its authoritative source. Transform the findings for presentation rather than restarting or independently changing the investigation.

- Markdown option: Load the investigation-report template and preserve the evidence, causal analysis, findings, uncertainty, and unresolved questions in a durable report.

- Boundary: Investigation is read-only by default. It may perform relevant diagnostics, but it does not implement a fix unless the user separately authorizes implementation.

- Typical dependencies: repository and runtime context, relevant connected systems, research-quality and verification policies, investigation-report template, Pitch Deck skill, and optional domain reviewers.

Pitch Deck is an optional capability. If requested, locate the installed skill; if absent, explain that it must be selected before invocation. Load `references/template.investigation/report.md` only when the user requests a Markdown report.

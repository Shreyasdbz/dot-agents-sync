---
name: pr-review
description: "Review a GitHub pull request with a severity-ranked inline verdict and optional reports."
---

# PR Review

Given a GitHub pull request URL, inspect the actual diff and relevant surrounding code through multiple review lenses. Validate and consolidate findings before returning a concise inline review; artifact generation and GitHub posting are optional delivery actions.

- Default inline output: Provide a one- or two-sentence outcome summary, an Approve, Suggest, or Block decision with concise reasoning, findings ordered from SEV_0 through SEV_3, exact locations and actionable remediation where possible, and a statement of what was inspected and any meaningful verification limits.

- Validation: Re-check every finding against the current diff and surrounding code. Consolidate duplicate symptoms that share one underlying cause, remove speculative or non-actionable observations, and preserve only attention-worthy findings.

- Severity: SEV_0 and SEV_1 block. SEV_2 is non-blocking but worth addressing now or in a follow-up. SEV_3 is a nit or optional improvement.

- Completion options: After the inline review, offer Post to PR, Create Markdown Report, Create HTML Report, or All Three. The user may choose any subset. If the original invocation already requests one or more options, perform them without asking again.

- Post to PR: Put the summary and verdict in the overall review body and use inline comments for location-specific findings where possible. Map Approve to approval, Suggest to a non-blocking comment review, and Block to requested changes. Posting changes an external system and requires explicit authorization.

- Posted finding format: Begin each finding with “[🫆AI Review] <🔴SEV_0 or 🟠SEV_1 or 🟡SEV_2 or ⚪️SEV_3> <comment title>”.

- Artifact consistency: Generate the inline response, Markdown report, HTML report, and posted review from the same canonical review model so verdicts, severities, locations, and remediation cannot drift between outputs.

- Typical dependencies: PR-review Markdown and HTML templates, repository context, review and security policies, GitHub capability, and optional security, architecture, UX, AI-systems, or slop-auditor agents.

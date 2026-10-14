# AI application defaults

Load for application model selection, inference routing or prompt lifecycle decisions. These defaults do not change the coding assistant's model, local model server or provider configuration, and do not authorize accounts, paid inference or data export.

## Routing and provider preference

Use Cloudflare AI Gateway whenever it supports the required workload and data constraints. Distinguish the gateway from the inference provider: OpenAI-backed requests can still pass through it. Prefer OpenAI next when the Cloudflare path cannot meet requirements; document the specific compatibility, privacy or operational reason for direct access. Do not infer a mandatory Workers AI model or permission to use every provider exposed by the gateway. Other providers remain subject to project approval.

Verify the actual endpoint, SDK and required modalities, streaming, tool calls and structured outputs before relying on compatibility. Keep credentials server-side, bound retries and fallbacks, and inspect logging/caching behavior before sending sensitive content. Do not silently bypass the gateway during failure or route data to an unapproved provider. This preference is not a claim that gateway routing removes model charges or supplies complete application tracing.

## Lowest cost that meets the quality bar

Start with the lowest-cost credible model for the task, not the flagship by habit or the cheapest model regardless of failure rate. Define the required correctness, instruction following, tool reliability, output structure and latency; compare representative cases before treating a candidate as suitable. During POC, use lightweight checks rather than a formal evaluation platform. Recheck current availability and pricing when choosing; do not hardcode an aging model list into this guidance.

Before upgrading, identify concrete failures and distinguish model limits from missing context, retrieval errors, broken tools, unclear prompts or unsuitable task decomposition. Compare the candidate upgrade on the same cases and record the quality improvement, latency and cost per successful task including retries and tool usage. Use a concise decision rationale, not an unsupported claim that a task needs a bigger model. If no inexpensive candidate meets the quality bar, escalate the trade-off rather than shipping knowingly inadequate behavior. Model upgrades and automatic escalation must stay within the approved project budget and routing policy.

## Public-facing build transition

Failure handling is project-specific: no global retry, escalation or manual-fallback default. Record eligible failures, limits and routes; budget alone does not authorize escalation. Resolve missing choices during design. Never report failure as success or replay consequential actions without checking their outcome.

Formal prompt versioning starts when work transitions from POC experimentation into building the public-facing product, not on release day. Do not require a prompt registry, release process or evaluation infrastructure for a disposable POC; ordinary Git history and basic correctness checks can remain lightweight.

At that transition, version prompts/templates, tool and output schemas, relevant retrieval configuration, model identifiers/settings and routing/fallback configuration together with the application release. Prefer repository files and existing release identifiers; a hosted prompt registry is optional, not a new mandatory service. Keep secrets and customer payloads out of versioned files. Record the actual prompt revision used by a run without logging sensitive content, and retain a known-good configuration for rollback. Pin explicit hosted prompt versions when using that facility rather than silently following the latest revision.

Maintain representative regression cases alongside the versioned behavior, including relevant adversarial inputs, malformed outputs and tool failures. Apply existing verification policy proportionately; distinguish proposed cases from executed model evaluations. A prompt version does not make model output deterministic, and a cheaper model or changed fallback must still satisfy the same product contract.

## Sources

Official documentation checked September 14, 2026; recheck endpoint support and version semantics during implementation.

- [Cloudflare AI Gateway with OpenAI](https://developers.cloudflare.com/ai-gateway/usage/providers/openai/).
- [OpenAI prompting](https://developers.openai.com/api/docs/guides/prompting).

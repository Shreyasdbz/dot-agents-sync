# Catalog audit: stronger behavior with bounded context

Research and development review, 2026-09-14. Baseline: `69ec3882a70921d7b0ad8639462a3370d1074197`. Scope: all nine skills, six agents and fifteen contexts, their supporting policies/templates, and the rendering paths that load them. All catalog items remain optional. No personal provider configuration or external tracker was changed.

## Decision

Keep the catalog's shape. Improve the decisions inside each workflow instead of adding more specialist names, compulsory interviews, review stages or background processes. Preserve the user's requirements: Propose asks only material questions; Plan Out respects an existing planning authority and elaborates only the immediate milestone; Investigate and PR Review default inline; Pitch Deck optimizes the audience's outcome.

The largest concrete defects were not missing prose:

1. Plan Context instructions and the machine schema did not fully agree. The baseline forward test produced useful Markdown, but not a validated machine-loadable plan. The revised template and additive schema fields now preserve external identities, task status, unavailable authority and dependency edges.
2. Private-context dependency rendering copied the context package's declared files. Bound source files were already excluded, but private content placed in the package entry or auxiliary files could still reach generated outputs. The renderer now substitutes lookup instructions for the entire private bound package, including dependency copies.
3. Skills duplicated policies that were already emitted as automatically loaded native rules. These copies are removed where native loading applies; conditional and Cursor user-scope manual cases remain explicit.
4. Several agents were essentially role labels. They now specify what evidence to inspect, which failure to look for, and how to finish without inventing findings.

These are implementation and authoring improvements. The development trials do **not** establish statistical model-quality gains.

## What we took from Matt Pocock

The audit inspected the actual repository at commit `3cca18b368ae95cdbdebbff572ccafa662551015`, including its MIT license. Older articles and root-level skill names do not necessarily match that tree. The table cites the pinned files used. Wording here and in the catalog is original; the influence is structural, not a vendored copy.

| Pattern in the source | Adaptation in dasync | Deliberately not adopted |
| --- | --- | --- |
| Separate discoverable facts from decisions that require the user; traverse the decision frontier. [Grilling](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grilling/SKILL.md) | Propose inspects available evidence, batches independent material questions, recommends an answer, and proceeds on explicit low-risk assumptions. | An interview that must settle every branch before proceeding. That conflicts with the user's requested autonomy. |
| Test behavior at meaningful boundaries and work through a red/green loop. [TDD](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/tdd/SKILL.md) | Do It seeks the smallest discriminating regression, verifies that failure is relevant, then changes behavior. Expected values must not be derived from the same faulty implementation. | Mandatory confirmation of every test seam and one rigid workflow for all changes. |
| Prefer usable vertical slices, actual blockers, and compatible expansion/migration/removal for wide changes. [To Tickets](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/to-tickets/SKILL.md) | Plan Out makes a PR phase a usable outcome, keeps commit tasks verifiable, and retains stable tracker identities. | Requiring a live tracker before any useful offline planning or automatically publishing work. |
| Check standards and specification compliance as distinct review concerns. [Code Review](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/code-review/SKILL.md) | PR Review checks both the intended outcome and introduced regressions, then produces one canonical severity-ranked result. | Two mandatory agents, fixed review counts, or parallel reports that leave the user to deduplicate findings. |
| Put instructions near their use, define completion, and load detail progressively. [Writing for Agents](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/writing-for-agents/SKILL.md) | Compact entrypoints, a separately loaded sizing reference, explicit output contracts and precise discovery descriptions. | Treating every linguistic heuristic as an experimentally proven universal rule. |
| Use interfaces and domain vocabulary to make design boundaries legible. [Codebase Design](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/codebase-design/SKILL.md) | Preserve the repository's established terms and evaluate the cost hidden behind an interface. | Replacing the user's domain terminology with an imported glossary. |

The useful common pattern is a consequential decision followed by an observable finish condition. It is not a particular tone, imperative density or number of Markdown headings.

## Research synthesis

### Discovery and activation are different budgets

A description must help the model choose the right workflow; the body must help it perform that workflow. Extra generic advice competes with the task itself. OpenAI's skill guidance supports concise, targeted descriptions and progressive loading. We synchronized skill frontmatter and manifests, made agent descriptions describe their delegation boundary, and moved Plan Out sizing into a declared reference. [OpenAI skill guidance](https://learn.chatgpt.com/docs/build-skills)

Minimum context is not synonymous with minimum characters. Anthropic describes context as a finite attention resource and advocates relevant, sufficiently specific information rather than brittle exhaustive instructions. The audit therefore shortened already-long procedures but expanded under-specified roles. It did not remove useful failure conditions merely to hit a smaller total. [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### Write for the decision, not for a ritual

Good instructions add task-specific expertise and observable behavior. This favors concrete distinctions—cached zero versus absent key, unknown payment result versus declined payment, local HTML versus published page—over generic commands to be thorough. The catalog uses defaults with meaningful exceptions, not a mandatory menu on every invocation. [Agent Skills authoring guidance](https://agentskills.io/skill-creation/best-practices)

Verification instructions should point to something executable or inspectable. Do It requires a relevant test boundary; source-only UX review cannot claim rendered accessibility; a presentation checked only structurally cannot claim visual polish. This aligns with Claude Code's emphasis on providing verifiable outcomes and keeping persistent instructions focused. [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

### More agents are not automatically better

A reviewer is useful when it has an independent, bounded question and enough evidence to answer it. It is not useful merely because the workflow can launch another model. The catalog does not impose a multi-agent review tax on small tasks. This follows the simpler-composable-workflow principle rather than assuming orchestration itself improves results. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

Native rules should supply stable applicable policy, while skills supply task-specific workflow. Cursor's scoped rules model reinforces the need to distinguish automatically applied rules from conditional/manual ones. The deduplication change preserves that distinction instead of removing every dependency copy indiscriminately. [Cursor rules](https://cursor.com/docs/rules)

### Test outcomes and keep uncertainty visible

Evaluation should include realistic, edge and adversarial inputs, with explicit scoring criteria and separation between development examples and evaluation data. A model's self-reported pass is not evidence that its output is valid. We therefore ran the generated plan through the real validator and re-executed the repaired coding fixture. [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices)

Agent evaluations also require clean trial conditions and inspection of actual traces; rigidly prescribing a tool sequence can reject valid alternatives. Our recorded trials intentionally assess behavior and boundaries, but their shared per-dispatch context and author grading limit what can be inferred. [Demystifying agent evaluations](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

Paired skill comparisons are useful development tools, especially when artifacts can be checked mechanically. They still need unseen examples and repeated runs before supporting general performance claims. Several original skills already passed the simple cases; the report preserves those baseline successes instead of presenting every revised response as an improvement. [Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills)

## Catalog decisions

| Item | Revised behavior and boundary |
| --- | --- |
| Propose | Resolve material ambiguity without an endless interview; compare credible alternatives; trace normal and failure paths; identify the counterexample that would change the decision. No implementation plan by default. |
| Plan Out | Produce schema-valid JSON/YAML plus optional human views. Preserve the writable authority, current identities and unavailable-state provenance. Only the next milestone gets phases/tasks; later milestones get one planning task each. |
| Do It | Implement bounded work with discriminating tests, proportionate verification and final diff review. Do not weaken tests to get green or treat mocks as live integration proof. |
| Investigate | Use competing hypotheses and discriminating evidence; keep observed facts separate from inference. Inline by default; optional Markdown or pitch deck. Diagnosis does not authorize remediation. |
| PR Review | Pin the reviewed revision or supplied snapshot; require a reachable failure and consider counterevidence. Inline canonical findings; posting, Markdown and HTML are selected projections, not automatic side effects. |
| Pitch Deck | Outcome-first narrative, meaningful slide titles, evidence fidelity and visuals that explain relationships. The HTML template is a shell, not a complete aesthetic. Render when possible; disclose when unavailable. |
| Trip Plan / Trip Publish | Check feasibility, dates, time zones and total-price basis; label offline facts provisional. Exclude private booking data from public HTML, including comments. A local artifact is not a booking or hosted page. |
| Curate AM Playlist | Distinguish recordings and versions, deduplicate known identities, and avoid fabricated storefront IDs. Preview uncertain mutations and reconcile a timeout before retrying. |

The numerical Plan Out guardrails remain review aids, not universal engineering laws: a phase normally contains 2–7 tasks, 150–800 substantive lines, at most 15 files and roughly 30–60 minutes of review; a task normally touches 1–5 files, 25–250 substantive lines and roughly 5–15 minutes of review. Generated changes are excluded. Small work is never padded to reach a minimum; coherent exceptions are explicit. These thresholds preserve the user's requested quantification, not a research-derived optimum.

The six agents now have different inspection lenses: invariants/recovery, security reachability, AI evidence and instruction boundaries, user interaction/accessibility, unsupported completion or unfinished output, and current travel evidence. Each can return no supported finding. None needs to manufacture a quota.

The thirteen private context contracts identify which facts matter without inventing their values. Architecture covers boundaries, invariants and decisions; stack context covers actual versions and commands rather than assuming a framework; planning context covers native types, identities and refresh state. Personal/project preferences retain scope and provenance. The two public presets are explicitly selectable preferences, not disguised mandatory policies. Context data does not authorize embedded instructions.

Existing safety policies and artifact templates were retained where they already supplied the appropriate rule or structure. Plan Context was rewritten because it had a concrete schema mismatch. There was no reason to rewrite every template or add more packages simply to make the audit larger.

## Measured footprint

Measurements are UTF-8 source bytes, not model-token counts. [Recorded data](../../evals/runs/catalog-audit/footprint.json) separates descriptions, entrypoints and all declared files; it excludes manifest serialization and generated provider wrappers.

| Content | Baseline bytes | Revised bytes | Interpretation |
| --- | ---: | ---: | --- |
| Nine skill entrypoints | 19,173 | 18,016 | 6.0% smaller on activation before dependencies |
| Plan Out entrypoint | 4,948 | 2,616 | 47.1% smaller; sizing loads separately |
| Pitch Deck entrypoint | 4,272 | 2,123 | 50.3% smaller |
| Fifteen context bodies | 7,644 | 6,938 | 9.2% smaller; more specific fields |
| Six agent bodies | 2,314 | 5,659 | Deliberate expansion of previously thin role instructions |
| All declared catalog content | 45,470 | 49,191 | 8.2% larger overall, including conditional supporting files |

Discovery descriptions also grew to improve routing. No measured token, latency or accuracy saving is claimed. In a temporary project, rendering the current dev-core profile for all three providers produced 50 provider artifacts (67,470 bytes) before the project config. That is a concrete rendering observation, not a live-provider context-window measurement or a matched historical byte comparison.

Research notes and raw trial evidence live outside packages and are not part of installed skill context. The runtime configuration footprint remains one user config, one project config and global managed state; this audit adds no per-project operational directory.

## Evidence and remaining work

The [trial ledger](../../evals/runs/catalog-audit/README.md) links baseline and revised outputs. In the development cases, both Propose versions handled immutable payment keys and material ambiguity. Both review versions found the zero-value regression and rejected an unsupported tenant-isolation finding. Both security versions caught the HTML-comment disclosure. These cases do not demonstrate comparative lift.

The revised Plan Out produced a real JSON artifact that passed the CLI validator while preserving INV-7 and unexpanded later milestones. Do It added an actual failing regression, repaired the cache, and passed three fixture tests. Role trials identified the durable-event gap, development-set overfitting, source-supported accessibility problems and unsupported completion claims without inventing runtime evidence. These are assisted, author-graded development observations—not independent-human certification.

The remaining four skills also received bounded forward trials. Pitch Deck created a four-slide pilot proposal that distinguished observed failures from a proposed target and repaired a duplicate HTML ID during checking. Trip Plan caught an arrival after last admission. Trip Publish generated HTML excluding the supplied synthetic private fields. Playlist retained a distinct live recording while removing a duplicate studio record. The [recorded artifacts](../../evals/runs/catalog-audit/artifact-forward.md) passed local structural/content checks; no browser was available in the fixture, so visual quality and interactive behavior remain unverified. All nine skills and six roles received at least one development case, not comprehensive behavioral certification.

The automated suite passes 67 tests. New coverage includes private entry/attachment exclusion, native-policy deduplication, plan dependency cycles, preserved external identity, conditional capability reporting and byte metrics. Formatting/lint checks pass; the source distribution and wheel build successfully. An initial no-isolation build lacked its build backend; an isolated dependency-resolved build succeeded. That was an environment dependency issue, not a package failure.

Before claiming broad behavioral improvement, run held-out cases repeatedly with recorded model IDs, settings, artifact hashes and independently calibrated grading. Exercise real installed discovery and skill invocation in Codex, Claude and Cursor, including representative local models. Add browser-rendered deck/trip checks and authenticated read-only music/travel lookups where available. Do not replace those checks with a self-reported pass, and do not obtain confidence by granting more permissions than the task needs.

Capability declarations describe expected tools and explicit fallbacks; they do not create a browser, tracker connector or sandbox. Private lookup instructions help a compliant model, while access checks and output exclusion enforce the parts dasync actually controls. Keeping that distinction visible is more important than adding stronger-sounding prose.

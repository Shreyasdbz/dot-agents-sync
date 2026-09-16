# Portable AI Dev Setup

Source: Google Doc 1HcNdeNTMOviO-gGgTQ1KbfBahBbO_u7Z44LYgw1GIHM

## Architectural design for dasync

Status: Proposed design

### 1. Executive summary

dasync is a scope-aware package and configuration manager for portable AI workflows. It keeps provider-neutral definitions in a canonical catalog, composes only the packages and local context allowed for a user or project, resolves that intent against a pinned catalog revision, and materializes disposable provider-native files for Codex, Claude Code, GitHub Copilot CLI, and Cursor.

The central pipeline is:

Catalog at a pinned revision → desired state → in-memory resolved graph → execution plan → materialized state → state database receipt

The design deliberately separates what an AI workflow means from how a provider consumes it. Skills, agents, context packs, policies, and templates remain portable. Provider adapters own filesystem layouts and feature translations. Hooks are supported, but treated as executable supply-chain content with stricter trust and consent rules.

The first implementation should build the package schema, resolver, state model, transaction engine, and one provider adapter before adding a large package catalog. The system is successful when repeated syncs are deterministic, project and user ownership remain distinguishable, private context cannot leak by inheritance, and both humans and AI coders can operate the CLI safely.

### 2. Decisions at a glance

- Skills are the primary product surface; agents are reserved for genuinely delegatable specialists.

- The only mutable scopes are user and project. An effective environment is a read-only composition of both.

- Project configuration may inherit user packages, but never mutates user state.

- User context is not exposed to projects unless its access policy and the project binding both allow it.

- Templates are normally transitive dependencies, not items users select manually.

- Tags and profiles are selectors; they never create implicit dependencies.

- Copy-based materialization is the default. Symlinks are an explicit adapter option, not the architecture.

- One user config and one project config express intent and pin the catalog revision; one global internal database records what was actually written.

- Desired, resolved, materialized, and observed state are architectural concepts, not separate user-facing files.

- Version 1 has no lockfile. The pinned single-source Git revision already determines package contents and dependency definitions.

- sync never fetches or upgrades packages. update is the only command that advances the pinned catalog revision.

- All mutations use one plan-and-apply engine with preconditions, staged writes, verification, receipts, and rollback.

- Generated provider files are owned by dasync. Unrecognized or modified files are protected by default.

- Machine-readable JSON and no-input behavior are first-class interfaces, not wrappers around the TUI.

- The catalog begins with concrete optional workflows and supporting packages, but nothing is enabled merely because it ships in the catalog.

### 3. Goals

- Maintain one portable source of truth for reusable AI skills, agents, context, policies, templates, and approved hooks.

- Install and configure independent user and project environments on any directory, whether or not it is a Git repository.

- Compose the smallest correct effective environment for a machine, project, provider, and capability set.

- Preserve provider-neutral wording while producing valid provider-native layouts for Codex, Claude Code, GitHub Copilot CLI, and Cursor.

- Make first-time setup, configuration, synchronization, updates, diagnosis, and recovery safe and predictable.

- Support interactive humans and autonomous AI coders through equally complete CLI surfaces.

- Keep discovery and runtime context token-efficient enough for smaller local models.

- Make every package optional unless selected directly or required by an explicit dependency.

- Provide reproducible, inspectable results across machines through pinned catalog revisions, content digests, and deterministic rendering.

- Protect private and machine-local context from accidental commits, inheritance, logs, and unrelated projects.

### 4. Non-goals

- dasync is not an agent runtime, model router, prompt marketplace, or secrets manager.

- dasync does not define one universal provider feature model. It negotiates capabilities and reports loss or degradation.

- dasync does not silently rewrite user-authored provider files or adopt existing files without consent.

- dasync does not make provider-native output canonical; materialized output must be reproducible and disposable.

- dasync does not automatically load every installed context into every workflow.

- dasync does not guarantee behavioral equivalence across providers that expose different capabilities.

- The first release will not support every provider, remote registry, or package-signing scheme.

### 5. Conceptual model

#### 5.1 Catalog

The catalog contains immutable package versions plus metadata. A source may be a Git repository, a local directory, or a future registry. Version 1 should support one trusted Git source and local development sources while keeping the source interface extensible.

#### 5.2 Desired state

Desired state is the user's declarative selection: enabled profiles and packages, explicit disables, provider choices, bindings, inheritance, trust policy, and a pinned catalog revision. It lives in the user config or the project's .dasync.yaml. It contains intent, not generated output paths.

#### 5.3 Resolved state

Resolved state is the complete, deterministic dependency graph computed in memory for a scope at its pinned catalog revision. The execution plan captures the selected and transitive packages, content digests, dependency edges, adapter version, platform facts, provenance, and capability decisions. The successful receipt is stored in the global state database. There is no separate resolved-state file in version 1.

#### 5.4 Execution plan

An execution plan is an immutable proposal to move from observed state to a target resolved state. It lists writes, replacements, removals, ownership conflicts, trust prompts, backups, validations, and hashes of every input used to create the plan.

#### 5.5 Materialized state

Materialized state is the provider-native filesystem output produced by adapters. It may combine user and project inputs for provider discovery, but every artifact retains scope and package provenance in state metadata.

#### 5.6 Observed state and receipt

The global state database records installation receipts, managed paths, owners, content digests, adapter versions, capability decisions, backup references, and verification results. Current filesystem hashes are compared with the receipt to detect drift. The database is operational metadata, never desired state.

### 6. Scopes and filesystem layout

#### 6.1 User scope

The only user-facing user-scope file is:

~/.config/dasync/config.yaml

It contains source definitions and trust roots, the pinned user-scope catalog revision, user package selections, provider defaults, private-context path bindings, and local overrides for known projects.

CLI-managed internal data lives under platform-native state and cache directories:

~/.local/state/dasync/state.db

~/.local/state/dasync/backups/

~/.cache/dasync/

state.db, backups, and cache entries are implementation details. Users do not edit, commit, or coordinate them. The CLI must honor platform-native config, state, and cache directories rather than assuming Unix paths internally.

#### 6.2 Project scope

Any directory may contain exactly one dasync project file:

.dasync.yaml

The file is intended to be committed. It contains a stable project ID, the catalog source ID and pinned revision, user-inheritance choice, selected packages, project-safe bindings, provider selection, and trust constraints. No project-local lock, state, cache, backup, or private directory is created.

Illustrative project configuration:

version: 1

project: pixpo

source:

  id: core

  revision: 78c2b91

inherit_user: true

packages: [skill.propose, context.pixpo-architecture]

providers: [codex, claude, copilot, cursor]

Private paths and machine-specific choices belong in the user config, keyed by the stable project ID. The user config may associate that ID with one or more local checkout paths. Private content remains wherever the user already stores it; dasync retains only a path or secret-manager reference.

#### 6.3 Effective environment

The effective environment is computed for a project path as project state layered over eligible user state. It is inspectable with status and explain, but it is never a writable scope. Every mutation must name user or project ownership.

### 7. Package primitives

#### 7.1 Skill

A repeatable workflow with an activation contract, inputs, steps, outputs, required capabilities, optional references, and evaluation cases. Skills are progressively discovered and load supporting content only when activated.

#### 7.2 Agent

A delegatable specialist with a bounded role, input contract, allowed tools, and return contract. If a behavior does not benefit from independent delegation, it should be a skill, policy, or context pack instead.

#### 7.3 Context pack

Facts, preferences, architecture, or domain knowledge. Context packs declare sensitivity, allowed scopes, loading triggers, token budget, and whether downstream packages may reference them. They do not contain executable behavior.

#### 7.4 Policy

Rules, constraints, and preferences that apply automatically when their selector matches. Policies replace the ambiguous top-level concept of “instructions.” They must declare scope, precedence behavior, and conflict strategy.

#### 7.5 Template

An output structure consumed by a skill or agent. Templates are normally dependency-only packages and may contain multiple formats when the package contract requires them.

#### 7.6 Hook

An executable or event-driven integration. Hooks are packageable but live in a separate trust tier. They must declare events, command entry points, permissions, supported platforms, inputs, timeouts, and side effects. Installing or changing executable content requires explicit policy approval.

Profiles are named selections of packages and bindings. Tags support search and interactive filtering. Neither is a dependency mechanism.

### 8. Initial optional package catalog

The catalog is part of the product design, not an example appendix. It defines the first useful workflows dasync should be able to distribute while keeping implementation order separate from catalog intent. Every item below is optional. Shipping an item makes it discoverable; it does not enable, inherit, or materialize it.

#### 8.1 Classification rules

Use the narrowest primitive that preserves the intended behavior:

- A user-invoked workflow with inputs and an output contract is a skill.

- A specialist worth delegating an independent task to is an agent.

- Facts, preferences, examples, architecture, or domain knowledge are context.

- A rule or quality constraint that should govern applicable work is a policy.

- A reusable output shape is a template.

- Executable behavior triggered by an event is a hook.

- A convenient named selection of packages is a profile.

This classification prevents “expert” labels from creating unnecessary agents:

- Python Expert becomes Python, FastAPI, and SQLAlchemy context plus applicable coding and testing policies. A Python reviewer agent is justified only for an independently delegated review.

- Coding Standards Expert becomes a coding-quality policy combined with repository-specific conventions context.

- Anti-Slop Expert becomes an anti-slop policy; a slop-auditor agent remains available when an independent final review is valuable.

- UI/UX Expert becomes design-preferences context plus accessibility and artifact-quality policies; a UX reviewer agent handles delegated critique.

- Cloud Expert becomes provider and infrastructure context; an architecture reviewer agent handles an independent architecture assessment.

- LLM Expert becomes AI-systems context; an AI-systems reviewer agent handles a bounded design or implementation review.

#### 8.2 Catalog behavior

- Packages are individually selectable and disabled by default.

- Required dependencies are enabled only because a selected package needs them and remain visible in plan and explain output.

- Suggested agents and contexts never activate implicitly.

- Profiles expand to an inspectable set of ordinary package selections; users may remove members before applying.

- Private context metadata may be cataloged, but its content is available only through an authorized user-side binding.

- Multi-pass and parallel review are preferred capabilities for Propose, Plan Out, and PR Review. If unavailable, the skill reports reduced assurance unless its selected configuration makes that capability mandatory.

- Catalog membership does not promise inclusion in the first implementation milestone. Rollout phases decide implementation order.

#### 8.3 Dev skills

The core development lifecycle is:

Propose → Plan Out → Do It

Investigate may feed Propose or Do It when the problem is unclear. PR Review validates a proposed change after implementation. Pitch Deck communicates any stage to an audience without changing the underlying engineering artifact.

##### 8.3.1 Propose

Given an inline change request or referenced file, produce a durable design proposal. Operate like a strong candidate answering an open-ended system-design question: collaborate when material requirements are unclear, then make deliberate decisions and move forward independently once enough is known.

- Discovery: Inspect the actual repository, relevant code, architecture, configuration, constraints, and available context before settling on a design. Use current external research and parallel reviewers when those capabilities materially improve the decision.

- Clarification gate: Ask questions only when different answers could materially change the system boundary, intended outcome, scale or service levels, consistency requirements, security or compliance posture, backward compatibility, migration strategy, difficult-to-reverse choices, or explicit scope. Ask a small prioritized batch rather than drip-feeding questions.

- Autonomy: When missing information is low-impact, state a reasonable assumption and continue. When the user delegates judgment, stop seeking routine confirmation. If the requirements are already sufficient, do not force an interview.

- Decision rigor: Evaluate the realistic approaches against the requirements, make a selection, and subject it to multiple critical review passes. Present the chosen design, material trade-offs, useful rejected alternatives, explicit assumptions, unresolved decisions, risks, validation needs, and migration or compatibility implications where relevant.

- Artifact quality: Produce a decision record, not a transcript of private reasoning. The result must be clear, concise, organized, comprehensive where changes need coverage, and intentionally shallow where extra depth would not improve implementation or review.

- Boundary: Design the change, but do not create implementation milestones, phases, tasks, schedules, commits, or production code.

- Output: A durable, template-based Markdown design proposal. Produce a template-based HTML companion when requested.

- Typical dependencies: repository architecture and product context, research-quality and security policies, design-proposal template, and optional architecture, security, UX, or AI-systems reviewers.

##### 8.3.2 Plan Out

Given an approved design proposal, produce a provider-neutral implementation plan from the current design, repository, relevant context, completed work, and configured planning authority. Plan Out separates the logical plan from its storage: it materializes work in the project's declared source of truth and always exposes a loadable Plan Context for downstream skills.

- Planning authority: Each project declares exactly one writable source of truth, such as a repository-local plan, GitHub, Azure DevOps, Linear, Jira, Notion, or another supported provider. Generated Markdown, HTML, and cached summaries are read-only projections unless explicitly configured otherwise.

- Portable hierarchy: Represent work as Plan → Milestone → Phase → Task. A Milestone is a major, independently demonstrable outcome spanning multiple pull requests; a Phase is one coherent, independently mergeable pull-request-sized outcome; and a Task is one independently verifiable, commit-sized implementation unit.

- Provider mapping: An adapter maps the portable hierarchy to the provider's native work-item model and preserves identity, ordering, dependencies, and parent-child relationships through native hierarchy, links, fields, labels, or metadata.

- Progressive milestone planning: For a large effort, fully elaborate only the next immediate milestone into phases and tasks. Do not create speculative implementation detail for later milestones.

- Future milestones: Record each future milestone's intended outcome, scope boundary, dependencies, high-level exit criteria, known risks, and exactly one task named “Plan Out <milestone name>.” When that milestone becomes immediate, reload the current design, repository, completed work, and provider state; then replace the planning placeholder with current phases and tasks.

- Milestone trigger: Consider milestone decomposition when any two conditions apply: more than six anticipated phases, more than roughly 25 anticipated tasks, three or more major subsystems, multiple independently shippable capabilities, strong dependence on discoveries from earlier implementation, or separate rollout, migration, or validation gates.

- Phase sizing: A phase should deliver one mergeable reviewer-visible outcome, normally contain two to seven tasks, change roughly 150–800 substantive lines across no more than about 15 implementation files, require approximately 30–60 minutes of focused review, and cross no more than one major architectural or migration boundary.

- Task sizing: A task should produce one independently understandable, testable, and revertible change mapped to an acceptance criterion. It should normally touch one to five closely related implementation files, change roughly 25–250 substantive lines, require approximately 5–15 minutes of focused review, and include explicit verification. Generated output, lockfiles, snapshots, fixtures, and mechanical formatting do not count toward these size ranges.

- Sizing exceptions: If a task or phase exceeds two guardrails, split it unless doing so would create an invalid intermediate state. Record a concise rationale for every indivisible exception.

- Plan Context: Always create or refresh a loadable context containing the planning authority, stable plan and work-item references, active milestone, active phases and tasks, dependencies, ordering, acceptance criteria, verification requirements, status, relevant design decisions, and a bounded summary of future milestones. Mutable external status must be refreshed from the authoritative provider.

- Write behavior: Preview proposed external work-item mutations by default. Apply them without another confirmation only when the invocation explicitly authorizes creation or updates in the configured planning system.

- Boundary: Structure implementation work without implementing it or silently reopening approved product decisions. Return material ambiguities that prevent responsible decomposition to the user or Propose.

- Typical dependencies: approved design proposal, repository architecture and coding-conventions context, planning and verification policies, provider adapter, Plan Context schema, and optional architecture or security review.

##### 8.3.3 Do It

Given one implementation task, make the scoped change using the relevant repository context, policies, and existing conventions. Establish a failing test first when it is a meaningful way to prove the behavior, implement the change, run proportionate verification, and report the observed outcome.

- Boundary: execute one authorized task; do not broaden scope or treat a plan as permission for unrelated work.

- Output: a concise outcome-first summary, the relevant verification evidence, and a commit only when the invocation explicitly authorizes Git mutation.

- Typical dependencies: coding, testing, security, scope, and Git policies plus stack and repository context.

##### 8.3.4 Investigate

Given a question, failure, or unexplained behavior, trace the evidence across code, configuration, logs, connected systems, and available context. Determine the most defensible causal explanation while keeping observed facts, inferences, competing explanations, and verification gaps distinct.

- Default inline output: Return the direct answer or most likely explanation, supporting evidence, causal chain, facts versus inferences, competing explanations considered, remaining uncertainty, and the smallest useful next action.

- Uncertainty: If the cause is not proven, say so directly. Do not manufacture certainty, treat observed activity as a verified outcome, or collapse multiple plausible causes into one unsupported conclusion.

- Optional outputs: After the inline result, offer Create Pitch Deck and Create Markdown Report. The user may choose either or both. If the original invocation already requests an option, produce it without asking again.

- Pitch Deck option: Invoke the Pitch Deck skill with the completed investigation as its authoritative source. Transform the findings for presentation rather than restarting or independently changing the investigation.

- Markdown option: Load the investigation-report template and preserve the evidence, causal analysis, findings, uncertainty, and unresolved questions in a durable report.

- Boundary: Investigation is read-only by default. It may perform relevant diagnostics, but it does not implement a fix unless the user separately authorizes implementation.

- Typical dependencies: repository and runtime context, relevant connected systems, research-quality and verification policies, investigation-report template, Pitch Deck skill, and optional domain reviewers.

##### 8.3.5 PR Review

Given a GitHub pull request URL, inspect the actual diff and relevant surrounding code through multiple review lenses. Validate and consolidate findings before returning a concise inline review; artifact generation and GitHub posting are optional delivery actions.

- Default inline output: Provide a one- or two-sentence outcome summary, an Approve, Suggest, or Block decision with concise reasoning, findings ordered from SEV_0 through SEV_3, exact locations and actionable remediation where possible, and a statement of what was inspected and any meaningful verification limits.

- Validation: Re-check every finding against the current diff and surrounding code. Consolidate duplicate symptoms that share one underlying cause, remove speculative or non-actionable observations, and preserve only attention-worthy findings.

- Severity: SEV_0 and SEV_1 block. SEV_2 is non-blocking but worth addressing now or in a follow-up. SEV_3 is a nit or optional improvement.

- Completion options: After the inline review, offer Post to PR, Create Markdown Report, Create HTML Report, or All Three. The user may choose any subset. If the original invocation already requests one or more options, perform them without asking again.

- Post to PR: Put the summary and verdict in the overall review body and use inline comments for location-specific findings where possible. Map Approve to approval, Suggest to a non-blocking comment review, and Block to requested changes. Posting changes an external system and requires explicit authorization.

- Posted finding format: Begin each finding with “[🫆AI Review] <🔴SEV_0 or 🟠SEV_1 or 🟡SEV_2 or ⚪️SEV_3> <comment title>”.

- Artifact consistency: Generate the inline response, Markdown report, HTML report, and posted review from the same canonical review model so verdicts, severities, locations, and remediation cannot drift between outputs.

- Typical dependencies: PR-review Markdown and HTML templates, repository context, review and security policies, GitHub capability, and optional security, architecture, UX, AI-systems, or slop-auditor agents.

##### 8.3.6 Pitch Deck

Given a feature, design, plan, code change, pull request, investigation, or other source artifact, create a self-contained HTML presentation that makes the subject easier to understand and act on. Treat this as editorial and information-design work, not as a mechanical conversion of source text into slides.

- Core objective: Communicate what outcome, change, or decision matters; why it matters; what evidence supports it; how the proposal or system works; what trade-offs or risks remain; and what the audience should understand or decide next.

- Audience and intent: Ask for clarification only when the audience or desired decision would materially change the presentation. Otherwise infer the most likely audience, state the assumption briefly, and proceed. Supported narrative modes include decision proposal, architecture explanation, implementation plan, change or pull-request walkthrough, investigation findings, and product or stakeholder update.

- Narrative: Lead with the outcome rather than an agenda. Use assertion-style titles that communicate each slide's conclusion, give every slide one primary job, keep essential reasoning in the main sequence, and place interruptive technical depth in an appendix. A common sequence is Outcome → Problem or opportunity → Evidence → Chosen approach → How it works → Impact → Trade-offs → Decision or next step → Technical appendix, but the source may require another structure.

- Source fidelity: Preserve uncertainty and distinguish evidence from inference. Never invent metrics, validation, quotations, customer language, or decisions. Do not repeat the same point as prose, diagram, and summary unless the repetition serves a distinct purpose.

- Content density: A standard slide should have one principal takeaway, one or two meaningful visual regions, approximately 40–90 words, and no more than three to five parallel points. Tables, code walkthroughs, architecture diagrams, and appendix slides may be denser when that improves understanding. Use no fixed slide count; keep the main narrative as short as the subject allows.

- Visual meaning: Every visual element should communicate hierarchy, comparison, causality, sequence, scale, ownership, or system structure. Prefer diagrams, comparisons, sequences, and concrete examples when they explain the relationship better than prose.

- Anti-slop rules: Avoid decorative gradients, glows, blobs, stock illustrations, repetitive card grids, icon collections used as structure, oversized metrics without context, fake quotations, excessive pills and badges, generic headings when a concrete claim is available, unnecessary consultant terminology, artificially symmetrical layouts, and animation that does not clarify state or sequence.

- Template architecture: Separate the invariant presentation shell from the content-specific visual system. The shell standardizes a responsive 16:9 frame, typography and spacing foundations, section navigation, previous and next controls, progress indicators, keyboard, pointer, wheel and touch navigation, visible focus, accessible semantics, reduced-motion support, and print or PDF behavior. It must not force every deck into the same palette, card grid, or layout.

- Quality gate: Before completion, verify that every slide has a distinct purpose; titles alone form a coherent story; important claims remain faithful to the source; visuals encode real information; no text clips at the intended viewport; navigation works by keyboard and pointer; contrast, focus, and reduced-motion behavior are accessible; the deck works without presenter narration; and no placeholder, coaching, or process language remains.

- Output: One polished, self-contained HTML file with all required CSS and JavaScript included. The result should be outcome-focused, clean, efficient, content-specific, and visually authored rather than recognizably AI-generated.

- Typical dependencies: pitch-deck shell and layout components, design-preferences context, source-specific context, accessibility and artifact-quality policies, and optional editorial, UX, architecture, or domain review.

#### 8.4 Travel skills

##### 8.4.1 Trip Plan

Create or revise a detailed trip itinerary through deep current research and an interactive constraint-gathering flow. Collect the participants, dates, origin, destinations, budget, dietary or accessibility constraints, pace, priorities, and firm preferences before finalizing recommendations. When revising an existing plan, preserve accepted decisions and use optional travel-research agents for bounded investigations.

- Output: a template-based Markdown plan designed for both quick-glance use and detailed review, with itinerary, bookings or candidates, logistics, constraints, costs where available, and unresolved decisions.

- Typical dependencies: trip-plan template, travel-preferences context, research and source-quality policies, web capability, and optional travel researchers.

##### 8.4.2 Trip Publish

Transform an approved trip plan into a polished, self-contained HTML experience. Preserve the plan's facts and unresolved items rather than performing a second independent planning pass.

- Output: an accessible, responsive, interactive page with clear itinerary navigation, light and dark modes, useful organization for mobile use, and all CSS and JavaScript contained in the file.

- Typical dependencies: trip-publish template, artifact-quality and accessibility policies, design-preferences context, and optional UX review.

#### 8.5 General skills

##### 8.5.1 Curate AM Playlist

Given a listening goal, mood, activity, seed tracks, exclusions, or other request, curate an Apple Music playlist using available music-preferences context. Explain the organizing idea and make sequencing intentional rather than returning an unordered song list.

- Boundary: preview the proposed playlist and any replacements before mutating an external account unless the invocation explicitly authorizes creation or editing.

- Output: a playlist proposal and, when authorized and supported, the resulting Apple Music playlist.

- Typical dependencies: music-preferences context, curation-quality policy, and Apple Music search or playlist-management capability.

#### 8.6 Optional agents

Agents are review or research workers, not containers for general knowledge. They load only when a skill or user delegates a bounded task.

- Security & Privacy Reviewer: assess threats, data handling, secrets, trust boundaries, permissions, and abuse cases; return prioritized findings with evidence.

- Architecture Reviewer: challenge boundaries, state models, failure modes, scalability, operations, and migration risk; load stack or cloud context as needed.

- AI Systems Reviewer: assess model, prompt, retrieval, evaluation, agent, and provider-integration decisions; load current AI-systems context rather than embedding it in the agent.

- UX & Accessibility Reviewer: evaluate interaction clarity, information hierarchy, responsiveness, keyboard behavior, and accessibility against supplied design context and policy.

- Travel Researcher: investigate one bounded travel question such as routing, lodging, logistics, or availability and return dated sources and uncertainty.

- Slop Auditor: independently inspect a nearly finished artifact or change for filler, vague claims, scaffolding, unnecessary terminology, or work presented as complete without evidence.

#### 8.7 Optional context packs

Context packs supply facts and preferences; they do not issue commands. The initial catalog should support both public reusable context and private user-bound variants.

Existing crafted context is source material to preserve, not replace with generic summaries. During onboarding, classify each statement: facts, preferences, examples, and architecture remain context; enforceable rules move to a policy. Mixed files may be split into linked packages, but the same instruction should not be duplicated across both.

- Personal coding preferences: favored patterns, trade-offs, tools, and conventions that are preferences rather than mandatory rules.

- Repository architecture: system boundaries, important paths, runtime topology, domain language, and current design decisions for a specific project.

- Repository conventions: existing naming, testing, migration, error-handling, and delivery practices observed in a project.

- Python stack: Python language and tooling context with separately loadable FastAPI, SQLAlchemy, data, and packaging references.

- TypeScript and web stack: TypeScript, frontend, server, framework, and package-management context split into independently loadable packs.

- Cloud and infrastructure: provider, deployment, identity, networking, observability, and operational context split by platform or project.

- AI systems: model, provider, prompt, retrieval, evaluation, and agent architecture context that can be refreshed without rewriting skills.

- Design preferences: visual principles, typography, color, interaction preferences, examples, and anti-patterns already crafted by the user.

- Product and audience context: goals, user groups, vocabulary, positioning, and decision constraints for an artifact or project.

- Security posture and data classification: system-specific assets, sensitivity, regulatory context, and known trust boundaries.

- Travel preferences: pace, budget tendencies, loyalty programs, dietary needs, lodging and transit preferences, and reusable traveler constraints.

- Music preferences: genres, artists, eras, moods, exclusions, sequencing preferences, and prior feedback.

Private context defaults to explicit project access. Highly sensitive packs may declare user-only access. A context package may provide a public schema and loading instructions while its actual content remains in a user-side binding.

#### 8.8 Optional policies

Policies contain operative rules. They activate only when selected directly, included by a profile, or required by another selected package.

- Scope and authorization: preserve user intent, protect unrelated work, distinguish diagnosis from implementation, and require consent for external or destructive actions.

- Coding quality: follow existing architecture and language conventions, prefer clear maintainable code, and avoid speculative abstractions.

- Testing and verification: prove behavior at the strongest practical source of truth and state verification limits precisely.

- Security and privacy: minimize data exposure, protect credentials and private context, validate boundaries, and use least privilege.

- Git hygiene: preserve dirty work, avoid destructive history changes, and commit or publish only with authorization.

- Anti-slop and communication: remove filler, invented terminology, private coaching, stale scaffolding, unsupported completion claims, and duplicated rationale.

- Research and source quality: use current primary sources where needed, distinguish evidence from inference, and preserve traceability.

- Accessible artifact quality: require readable hierarchy, keyboard access, responsive behavior, contrast, and meaningful visuals for applicable outputs.

A preference belongs in context; an enforceable rule belongs in policy. For example, “prefer muted colors” is context, while “all controls must be keyboard accessible” is policy.

#### 8.9 Related templates

Templates are normally dependency-only packages. Selecting a consuming skill includes the required template automatically.

- Design proposal: durable Markdown structure plus an optional self-contained HTML rendering.

- Implementation plan extension: phase and task structure appended to the approved proposal artifact.

- Investigation report: compact evidence, cause, uncertainty, and next-action structure for larger investigations.

- PR review: summary, decision, severity-sorted findings, and optional posting payload.

- Pitch deck shell: accessible self-contained HTML controls, navigation, layout system, and adaptive visual tokens.

- Trip plan: quick-glance overview followed by itinerary, logistics, costs, constraints, sources, and open decisions.

- Trip publish: responsive self-contained HTML travel experience with light and dark themes.

- Playlist proposal: concept, sequencing rationale, track list, exclusions, and intended account action.

Templates define shape, not truth. A skill remains responsible for source accuracy, content completeness, and appropriate adaptation.

#### 8.10 Optional hooks

No hook should be enabled by a general profile in the initial release. Candidate hooks may ship for explicit opt-in after trust review:

- Credential-path guard: block writes to declared credential-bearing paths unless the operation carries explicit authorization.

- Work-state checkpoint: record or restore workflow state at provider-supported lifecycle events without copying private context into logs.

- Verification trigger: run a manifest-declared local validation command after selected materialization events, with constrained permissions and a timeout.

Hook installation and every executable-content change must be disclosed separately from declarative package updates.

#### 8.11 Optional profiles

Profiles are editable starting selections, not opaque bundles:

- dev-core: Propose, Plan Out, Do It, and Investigate with core scope, coding, testing, security, Git, and communication policies plus required templates.

- dev-review: PR Review with the review template and suggested security, architecture, AI-systems, UX, and slop-auditor agents.

- technical-storytelling: Pitch Deck with its shell, design-preferences context binding, and accessibility and artifact-quality policies.

- travel: Trip Plan and Trip Publish with required templates and optional travel-preferences and design bindings.

- personal-music: Curate AM Playlist with an optional music-preferences binding.

Applying a profile shows the exact packages, dependencies, suggested bindings, capability gaps, and trust-sensitive items before it changes desired state.

#### 8.12 Representative dependency relationships

- Propose requires the design-proposal template; it may suggest architecture, security, or AI-systems reviewers and relevant project context.

- Plan Out consumes an approved proposal and requires the implementation-plan extension; it does not depend on Propose being installed.

- Do It consumes one authorized task and requires applicable scope, coding, testing, security, and Git policies rather than a generic implementation agent.

- PR Review requires the review template and may delegate independent lenses without loading every reviewer by default.

- Pitch Deck and Trip Publish require their HTML shells plus accessibility policy; design preferences remain optional context.

- Trip Plan and Curate AM Playlist may require external service capabilities, but account mutation remains a separately authorized action.

### 9. Package manifest

Every package owns a manifest.yaml. Catalog indexes are generated from manifests and must not become a second source of truth.

Required fields:

- apiVersion and kind

- globally unique id and human-readable name

- package version and content digest

- description, tags, and license

- entry points and included files

- required, optional, and conflicting package dependencies

- required and preferred capabilities

- supported scopes and provider constraints

- context-loading and sensitivity policy when applicable

- output contract for skills and agents

- trust class and executable declarations for hooks or scripts

Illustrative manifest:

apiVersion: dasync.dev/v1alpha1

kind: Skill

id: dev.propose

version: 1.0.0

entry: SKILL.md

requires:

  packages: [template.design-proposal]

  capabilities: [filesystem.read]

prefers:

  capabilities: [web.search, agents.parallel, git.read]

contexts:

  suggested: [dev.architecture, dev.security]

degradation: allowed

Manifests are schema-validated before resolution. Unknown fields fail in strict mode and warn only when explicitly allowed by a compatible schema policy.

### 10. Configuration and internal state

#### 10.1 User config

~/.config/dasync/config.yaml is the only user-scope configuration file. It records schema version, allowed sources and trust roots, the user-scope pinned revision, selected profiles and packages, provider defaults, private-context bindings, and project-specific local overrides. Ordered lists preserve user intent; CLI normalization must be stable.

#### 10.2 Project config

.dasync.yaml is the only project-owned file. It records the stable project ID, schema version, source ID and pinned revision, package selections, inheritance, project-safe bindings, providers, and trust constraints. It is portable and intended to be committed.

#### 10.3 Global state database

~/.local/state/dasync/state.db is CLI-owned. It stores receipts, managed-path ownership, expected digests, observed drift, adapter and capability results, transaction journals, backup references, and known project-path mappings. It may cache resolved graphs for performance, but cache entries never override configuration or the pinned catalog revision.

#### 10.4 Why version 1 has no lockfile

A single immutable Git revision fixes all package manifests, dependency definitions, templates, scripts, and content. The combination of the selected package IDs, pinned catalog revision, CLI and adapter version, and relevant platform facts is sufficient to reproduce the resolved graph. A second committed file would duplicate information without solving an independent-resolution problem.

A lockfile should be introduced only when sources or packages can advance independently—for example, multiple registries, version ranges across sources, or dependencies not fixed by one catalog commit. That future lockfile must be additive; version 1 commands and configs should not pretend it already exists.

#### 10.5 Private and machine-local values

The user config may bind a stable project ID to local checkout paths and private context locations. Secret values should be referenced through environment or secret-manager handles, never embedded. Project configuration may require a binding by ID, but it cannot contain or discover its private bytes.

### 11. Inheritance and precedence

Resolution proceeds from lowest to highest precedence:

Package defaults → user config → project config → project-specific local overrides in the user config → explicit CLI flags

CLI flags are ephemeral unless configure explicitly writes desired state. Project configuration never edits user files. Project-local overrides may supply paths and machine choices, but they cannot change the committed catalog revision or weaken project trust constraints.

Merge rules:

- Scalar fields replace lower-precedence values.

- Maps merge by key unless a field schema declares replace-only behavior.

- Package selections are set operations with explicit enable and disable tombstones.

- Bindings use add and remove operations; an empty list does not implicitly erase inherited bindings.

- Dependency requirements cannot be disabled while a dependent package remains enabled.

- Policy conflicts fail resolution unless the manifest declares an unambiguous precedence rule.

- The resolver retains provenance for every effective value and edge so explain can show why it exists.

User skills, agents, templates, and eligible policies may be inherited when inherit.user is true. Context packs and hooks require additional explicit authorization. The CLI must never infer a writable scope from an effective view.

### 12. Private and local context

Private content is physically separated from the catalog and is never copied into the public source checkout or a project-owned dasync directory. Context manifests expose metadata and a local binding key; the bytes stay wherever the user already stores them. The user config maps that key to a path or secret-manager reference.

Every context pack declares project access as one of:

- inherit: eligible for projects that inherit the user environment

- explicit: available only when the project binds it by ID

- never: user-only and rejected from project resolution

The safer default is explicit. Sensitive context also declares allowed consumers, allowed providers, redaction policy, and whether materialization may copy bytes or must use a reference. status and JSON output show identifiers and availability, not private content. Logs, plans, diffs, and errors redact secret values and avoid embedding context bodies.

Missing optional context produces a visible degraded result. Missing required context fails resolution before any write.

### 13. Dependency graph and resolution

Packages reference exact IDs plus semantic version constraints. Dependencies are explicit; tags, filenames, and directory nesting never imply edges.

The resolver must:

- expand selected profiles into explicit roots

- apply scope and access filters

- resolve required dependencies and optional feature edges

- reject cycles, unsatisfied constraints, conflicting packages, and forbidden scope crossings

- negotiate provider capabilities

- produce a stable topological order

- compute the same resolved graph for the same pinned catalog revision, configuration, platform facts, and adapter versions

- retain why each package was selected: direct, profile, inherited, binding, or dependency

Templates follow consumers automatically. Suggested contexts are recommendations only and never become implicit dependencies. sync resolves from the immutable pinned revision, so it does not depend on a moving source or a committed lockfile.

### 14. Capability negotiation

Capabilities use provider-neutral names such as filesystem.read, filesystem.write, web.search, git.read, github.review, agents.parallel, hooks.pre_tool, and ui.interactive.

Each package declares required and preferred capabilities plus one degradation policy:

- forbidden: fail if any required capability is absent

- allowed: run with a declared fallback and warning

- provider-override: use a manifest-declared adapter fragment reviewed with the package

Each adapter reports supported, unsupported, and conditionally available capabilities with evidence from installed provider version and configuration. Resolution records one result per package/provider: supported, degraded, or blocked. The CLI must explain missing capability names and the selected fallback; it must not silently drop behavior.

### 15. Provider adapter architecture

The core resolver never writes provider files directly. Each adapter implements:

- detect: locate provider installations, versions, and supported roots

- capabilities: report available provider features

- plan: map resolved packages to owned target paths and detect collisions

- render: produce deterministic bytes from canonical packages

- validate: parse or inspect rendered output using provider-native rules

- discover: identify existing unmanaged files and supported adoption paths

Adapters receive a resolved graph and sanitized context bindings. They return planned artifacts and diagnostics; they do not mutate the filesystem themselves.

#### 15.1 Codex adapter

Materializes Codex-discoverable skills, agent definitions, shared instructions, and hook configuration where supported. It preserves canonical SKILL.md content when the provider already accepts it and generates only the metadata or configuration required by Codex. Unsupported capabilities are reported through negotiation rather than embedded as Codex conditionals in package prose.

#### 15.2 Claude Code adapter

Materializes Claude-discoverable skills, agents, project instructions, and hooks using Claude's current native layout. It translates metadata and event wiring but does not fork canonical workflow content. Executable hook changes receive the same trust gate as every other provider.

#### 15.3 Cursor adapter

Materializes portable skills and scoped project rules in Cursor's current supported locations. Policies may compile into rule files; project context remains progressively referenced where possible. Features without a safe native equivalent are degraded explicitly or blocked.

Provider paths and feature mappings are versioned adapter data, not assumptions in core code. Adapter conformance fixtures protect against provider changes. Copy mode is the default; symlink mode is allowed only when the adapter and platform prove it safe.

### 16. CLI contract

Every command supports --json. Mutating commands also support --dry-run, --no-input, --yes, --scope, and --path where applicable. --dry-run builds the same plan as a real operation and performs no persistent write. In no-input mode, ambiguity and required consent are errors.

#### setup

Create a new user or project environment, validate the target, write the single scope configuration, pin the catalog revision, resolve the graph, and perform the first materialization as one transaction. Project setup creates only .dasync.yaml. Refuse to overwrite an existing environment unless --repair or an explicit migration path is selected.

Examples:

dasync setup --scope user

dasync setup --scope project --path /absolute/project/path

#### configure

Change desired state only. It does not fetch sources, advance the pinned revision, or materialize provider files. Interactive mode opens the TUI. Flag-based mode applies explicit set operations. Project-local private bindings are written to the user config under the project's stable ID, never to the project file. --apply may immediately invoke the normal plan/apply pipeline after saving the config.

#### sync

Make provider files match the current configuration at its pinned catalog revision. It performs no network fetch and never advances the revision. It may use a verified cached checkout or local canonical checkout, but fails if the pinned content is unavailable or its digest does not match. Repeated syncs with unchanged inputs are no-ops.

#### update

Fetch allowed sources, choose a newer immutable catalog revision within configured policy, resolve its graph, and plan both the configuration revision change and materialization. On confirmation, the revised config and provider outputs commit atomically. A failure preserves the previous revision and outputs. --config-only is allowed for review workflows but leaves status visibly pending.

#### status

Read-only summary of scope discovery, selected and inherited packages, pinned catalog revision, provider synchronization, drift, degraded capabilities, pending updates already known locally, and the last receipt in state.db. --effective composes user and project state without creating a writable scope.

#### doctor

Read-only diagnostics for configuration validity, pinned-source availability and integrity, dependency resolution, state database health, permissions, provider detection, capability support, managed output hashes, and recovery data. It never repairs automatically.

#### repair

Restore managed outputs and reconstruct safe receipt data from configuration, the pinned catalog revision, global backups, and observed files. It never fetches or upgrades. Unmanaged collisions or modified managed files require an explicit strategy and are previewed before mutation.

#### rollback

Restore the relevant configuration and managed provider outputs from a named successful transaction receipt in state.db. It validates current preconditions and never performs a Git reset. Rollback itself creates a new receipt and can be rolled back.

#### plan

Create an immutable JSON execution plan for another action, for example dasync plan sync. The plan includes schema version, operation, exact scope root, configuration hash, pinned and candidate catalog revisions, resolved package digests and edges, adapter versions, ordered file operations, required consents, validations, and expiry policy. It may be written to a file or stdout.

#### apply

Apply a previously generated plan. It rechecks every precondition and fails with PLAN_INVALIDATED if the configuration, pinned source content, adapters, capabilities, or observed target hashes changed. apply never silently regenerates a stale plan.

Supporting read-only commands should include list, search, explain, diff, capabilities, schema, and ai instructions. explain must show provenance for a package, binding, capability decision, or output path.

### 17. Human TUI and AI mode

The TUI is a view over the same configuration and plan APIs used by flags and JSON. It is enabled only on an interactive terminal when no machine-mode flag is present. It groups profiles, directly selected packages, inherited items, automatic dependencies, provider effects, warnings, and trust prompts without hiding provenance.

Machine and AI mode requires:

- stable versioned JSON schemas for input, output, plans, diagnostics, and errors

- explicit --scope and --path for mutations

- --no-input to forbid prompts

- --yes only to accept already disclosed non-security confirmations

- structured error codes, suggested next commands, and nonzero exit codes

- stdout reserved for the requested result and stderr for human diagnostics

- no ANSI formatting when --json or NO_COLOR is active

--yes must not bypass new-source trust, executable hook approval, private-context scope violations, unmanaged-file adoption, or destructive conflict resolution unless a narrower explicit policy flag is provided.

### 18. AI operator instructions

The repository includes docs/AI-OPERATOR.md as the canonical safe operating contract. Small provider bootstrap files point to it without duplicating the full instructions.

An AI operator must:

- use capabilities --json and schema commands instead of guessing syntax

- inspect status with explicit scope and absolute path

- inspect available packages and explain provenance before changing desired state

- preview every mutation with plan or --dry-run --json

- never edit generated provider files directly

- never expose private context bodies in prompts, logs, or summaries

- apply only a fresh plan whose scope and changes match the user's request

- run doctor --json after mutation and report exact verification limits

- stop for user input when trust, adoption, destructive conflict, or scope ownership is ambiguous

dasync ai instructions emits instructions matching the installed CLI version. dasync ai environment --json reports discoverable scopes, sources, providers, capabilities, and safe next actions without returning private content.

### 19. Ownership and drift detection

Each materialized path has one owner tuple: scope, provider, package ID, package version, adapter version, and transaction ID. state.db stores the expected digest and file mode. Optional lightweight generated headers may identify ownership when the native format permits, but headers never replace the database receipt.

Observed paths are classified as:

- clean: digest matches the last receipt

- missing: a managed path was removed

- modified: a managed path differs

- stale: a previously managed path is no longer planned

- unmanaged collision: the plan targets an existing unowned path

- orphaned: an ownership marker exists without a valid receipt

Default behavior protects data. sync may recreate missing managed files and remove clean stale files, but it refuses to overwrite modified files or unmanaged collisions. Explicit resolutions are protect, move aside, adopt where semantically supported, choose another target, or overwrite with a reviewed backup. Adoption imports ownership state; it does not make provider output canonical.

### 20. Transactions, rollback, concurrency, and idempotency

All mutating commands compile to the same transaction engine:

Resolve → observe → plan → validate → stage → acquire scope lock → revalidate → commit → verify → record receipt

The engine must:

- acquire a per-scope lock and report the owning process or transaction on contention

- stage files on the same filesystem as their targets

- validate schemas, digests, permissions, capability decisions, and adapter output before commit

- create recoverable backups for every replacement or removal

- commit using atomic renames where supported and a journaled fallback otherwise

- verify post-write bytes and provider-specific validity before recording success

- restore the prior state automatically when commit or verification fails

- write the receipt last

Plans bind to input hashes and cannot be applied after relevant state changes. Stale concurrency locks are detected rather than waited on indefinitely; recovery requires proof that no live owner remains. Repeated execution with identical inputs produces no writes and a no-change receipt or result. Renderers must avoid timestamps, random IDs, unstable ordering, machine-specific whitespace, and unnecessary absolute paths.

### 21. Supply-chain and security model

Threats include malicious packages, compromised sources, dependency confusion, path traversal, symlink attacks, executable hook escalation, private-context disclosure, poisoned provider output, and unsafe AI automation.

Required controls:

- allowlisted sources with pinned immutable revisions and verified package digests

- canonical package IDs and source-qualified dependency resolution

- manifest-declared files; reject traversal, special files, and writes outside adapter-owned roots

- separate trust classes for declarative content and executable scripts or hooks

- explicit review when executable content, permissions, or hook events change

- least-privilege hook execution with timeouts, sanitized environment, and constrained working directories where the platform permits

- no network access during sync unless an adapter validation explicitly declares and receives permission

- secret references instead of secret values in configuration, plans, state database receipts, and logs

- redaction tests for all machine-readable output

- signed releases and provenance attestations as a later hardening layer, without making signatures a substitute for content review

Package installation is code execution risk even when most files are Markdown. update must summarize changes by trust class and make executable changes impossible to miss.

### 22. Testing and evaluations

#### Structural and schema tests

Validate manifests, user and project configuration, state database receipts, unique IDs, referenced files, dependency constraints, cycles, scope rules, and deterministic index generation.

#### Resolver tests

Use table-driven and property-based tests for precedence, tombstones, inheritance, private-context gates, conflicts, version selection, capability degradation, and provenance explanations.

#### Adapter tests

Maintain golden outputs for each supported provider and version band. Parse or validate generated files using native schemas where possible. Run conformance tests for detection, path ownership, unsupported capabilities, and round-trip no-change syncs.

#### Transaction tests

Inject failures at every stage: lock acquisition, staging, backup, rename, permission change, validation, verification, and receipt write. Prove that partial state is detected and recoverable and that concurrent processes cannot interleave commits.

#### Security tests

Cover path traversal, malicious symlinks, source spoofing, digest mismatch, executable permission changes, secret redaction, unsafe archive contents, and hostile package metadata.

#### Behavioral evals

Each skill and agent may ship provider-neutral eval cases with expected invariants, prohibited behaviors, and token budgets. Run them across supported providers and representative smaller local models. Track regressions without claiming identical model behavior.

#### Context-budget tests

Measure discovery metadata, activated package content, referenced context, and total effective tokens. Set budgets per package and fail large unexplained regressions.

### 23. Repository structure

dot-agents-sync/

  packages/

    skills/

    agents/

    contexts/

    policies/

    templates/

    hooks/

  profiles/

  adapters/

    codex/

    claude/

    cursor/

  cli/

    core/

    commands/

    tui/

  schemas/

  docs/

    architecture/

    AI-OPERATOR.md

    package-authoring.md

    adapter-contract.md

  tests/

    structural/

    resolver/

    adapters/

    transactions/

    security/

  evals/

  AGENTS.md

  CLAUDE.md

  .cursor/

  README.md

packages defines what workflows know and do. adapters defines how providers consume them. cli owns resolution and transactions. schemas owns stable contracts. Provider bootstrap files contain only enough instruction to find the canonical operator and contribution documentation.

### 24. Rollout plan

#### Phase 0: contracts and fixtures

Finalize schemas for package manifests, the user config, .dasync.yaml, state database receipts, plans, capabilities, and adapter output. Create resolver and transaction fixtures, adversarial path cases, and a minimal example catalog. Decide the implementation language only after portability and packaging constraints are tested.

Exit: schemas validate; example graphs resolve deterministically; plan and JSON error contracts are reviewed.

#### Phase 1: deterministic core plus Codex

Implement scope discovery, the two configuration surfaces, precedence, pinned-revision resolution, the global state database, plan/apply engine, receipts, drift detection, status, doctor, sync, rollback, and the Codex adapter. Support copy mode only. Include one small skill, policy, context, template, and optional agent fixture.

Exit: clean setup on user and project scopes; offline repeated sync is a no-op; injected failures roll back; private context gates are enforced.

#### Phase 2: Claude Code and Cursor

Implement adapters through the same conformance suite. Add capability negotiation, degraded-mode reporting, adapter versioning, and cross-provider golden fixtures.

Exit: one project pinned to a catalog revision materializes valid environments for every supported provider with explicit, explainable differences.

#### Phase 3: robust update and operator UX

Add source fetching, candidate revision and package diffs, executable change review, TUI configuration, AI instruction surfaces, repair workflows, local-source authoring, and stable machine-readable schemas.

Exit: both a human and an AI operator can safely configure, preview, update, diagnose, repair, and roll back without editing generated files.

#### Phase 4: package catalog and hardening

Implement and mature the remaining initial catalog candidates only after the substrate is stable. Onboard existing context artifacts through the classification rules, add behavioral evals and token budgets package by package, and introduce source signing, attestations, additional platforms, and evidence-driven provider adapters.

Exit: catalog growth does not change core semantics, weaken security boundaries, or cause unexplained token regressions.

### 25. Version 1 acceptance criteria

- A user can initialize user scope and any project directory independently.

- User setup creates one user configuration file; project setup creates only .dasync.yaml and no project-local dasync directory.

- A project can inherit eligible user packages while provenance remains visible.

- Private user context cannot enter a project without both context policy and project authorization.

- The same configuration, pinned catalog revision, adapter version, and platform facts produce byte-identical outputs.

- sync works offline when the pinned catalog content is cached and never advances the revision.

- update either commits the configuration revision plus outputs together or changes nothing.

- Modified managed files and unmanaged collisions are never overwritten silently.

- A failed write can be repaired or rolled back from a verified receipt.

- Codex, Claude Code, GitHub Copilot CLI, and Cursor adapters pass one shared conformance suite.

- Every mutation can be planned and applied non-interactively with versioned JSON.

- doctor can distinguish invalid configuration, unavailable or corrupted pinned content, provider drift, missing capability, state database failure, permission failure, and an incomplete prior transaction.

- Token-budget and behavioral evals cover the initial packages.

- Every initial catalog candidate is independently selectable; profiles expose their complete expansion, and no optional agent, context, policy, template, or hook activates merely because it ships.

### 26. Open questions

- Implementation language: Rust, Go, or another option after measuring cross-platform packaging, startup time, filesystem APIs, and contributor ergonomics.

- Multi-source sequencing: which post-version-1 phase should introduce source-qualified IDs, independent constraints, and the accompanying lockfile.

- Future lockfile trigger: the precise feature boundary—such as multiple independently versioned sources—that justifies adding a committed lockfile.

- Adapter compatibility: exact provider-version ranges versus feature probes as the primary contract.

- Context references: copy, symlink, or provider-supported lazy reference when private content must remain outside generated roots.

- Adoption: whether existing provider-native files can be imported into canonical packages, or only registered as protected unmanaged files.

- Hook sandboxing: the minimum portable isolation guarantee across macOS, Linux, and Windows.

- Team policy: whether projects may impose trust and provider constraints that user-local overlays cannot weaken.

- Plan portability: whether a plan is valid only on one machine or can be transferred when all target path and platform facts match.

- Package lifecycle: deprecation, replacement, migration hooks, and configuration compatibility guarantees.

These questions do not block schema and engine prototyping, but each must be resolved before its related feature leaves experimental status.

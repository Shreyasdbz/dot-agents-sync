# Evidence and change coverage

## Choose the comparison

| Input | Record | Read next |
| --- | --- | --- |
| PR | Repository/PR identity, full base/head and merge-base IDs, comparison type and retrieval time | Description, complete file list/patch, relevant discussion and checks, then owning code at those revisions |
| Local diff | Full HEAD, baseline, staged/unstaged scope and SHA-256 of the captured diff; selected untracked files with hashes | Both versions, owners, callers, tests and configuration |
| Supplied patch | Content hash, named repository/baseline when known, omissions or truncation | Supplied context and authorized matching source; keep unknown revisions explicit |
| Session effort | Accepted intent/constraints, relevant artifacts, actual implementation state and available source snapshots | Current files and decisions; label design-only or incomplete portions |

Use a PR's merge-base comparison to explain its changes; name a different comparison if requested. Do not substitute the current checkout for a pinned PR head. Read-only Git inspection and temporary snapshots preserve dirty work. Do not fetch, switch branches, execute repo tooling or include unrelated untracked files merely to obtain an explanation. Use available authorized mechanisms; request additional authority only where needed. A source hash describes bytes, not a Git revision.

If tools return a partial patch, missing file or truncated document, recover the relevant content through an authorized read when possible. Otherwise show the precise gap. Discussion records intent; code records implementation; check status is not the full test result. A merged PR is not evidence of deployment.

## Reconstruct behavior

Build a compact working ledger, not a second deliverable. For each material group, record changed paths, purpose, old/new trigger and result, owning symbols, relevant consumers, invariant, success/failure/recovery paths, applicable lenses, sources and verification state. Group mechanical edits when their only effect is shared; investigate deleted paths, dependencies, generated contracts, migrations and configuration as possible behavior changes.

Trace from the user or service entrypoint through state and effects to the observable result. Follow authorization, tenant/data boundaries, asynchronous ordering, retry/idempotency, cancellation and rollback only where reachable. Check both producer and consumer of changed contracts, including another relevant local repository. Record their revisions and environments separately; similarly named LOCAL/PROD settings do not establish compatible deployments.

Use one concrete worked scenario per consequential mechanism. Specify inputs, state, branch, effect and result before and after. Add the most informative boundary/failure case and explain what stays unchanged when that prevents a likely misunderstanding. A proposed fix or alternative gets an explicit proposed label, never an arrow implying it already executes.

## Ground claims

| Evidence class | Appropriate wording |
| --- | --- |
| Observed source | “The new branch returns the stored value.” Cite revision/path/symbol. |
| Executed check | “This local test passed.” Name command, environment and scope. |
| Intended requirement | “The document requires…” Cite the accepted requirement and date. |
| Inference | “This can reduce loader calls for this case.” Show the causal path and assumptions. |
| Unknown | “Latency was not measured.” Name the missing evidence and consequence. |

Cite material claims and diagrams beside their explanation. Prefer immutable code links with verified lines and source IDs linked to a local appendix. The file must remain understandable offline: include a concise authorized excerpt or paraphrase of the relevant contract, not only a link. Protect secrets, customer data and private context bodies; summarize permitted facts and keep restricted details as gaps. Escaping a secret does not make it safe.

Current external API/runtime guarantees need current primary sources. Record source revision/date, retrieval date and applicability. Do not use a search snippet as the complete contract or silently resolve conflict by taking the newest document. Distinguish an absent result, absent access and a source actually checked with no relevant evidence.

Before delivery, compare the complete material file list and accepted session scope against the ledger and HTML. Every consequential group needs a visible explanation or specific gap. Recheck head/local fingerprints and relevant source freshness; revise affected analysis if inputs changed. Retain old snapshots only when the user asks for history; never silently describe old behavior as current.

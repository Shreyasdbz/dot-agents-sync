# Behavioral evaluation protocol

These cases test workflow decisions. Unit tests and catalog validation do not prove that a model follows the instructions.

Run each case in an isolated project using the installed target skill or agent. Give the model the prompt and fixture context, but do not reveal the assertions before it responds. Record provider, model, version, invocation, source pin, exact input, actual output, observed side effects and the grader's evidence for every assertion. Use separate runs for hosted providers and representative local models. Do not claim independence if the author evaluates its own output.

For engineering policy cases, install the named policy or the engineering-cloudflare profile specified in the prompt, then perform the task normally; a policy is not an invocable skill. Verify that the target provider actually loaded the policy, and retain that evidence with the run. The engineering cases are scenario definitions, not recorded passes.

`cases.json` contains the portable scenarios. To grade a recorded run, create a JSON object with `case_id`, `provider`, `model`, `source_revision`, `output`, `observed_actions`, and `assertions` (each with `id`, `passed`, `evidence`). Use `python evals/check_result.py result.json`. It rejects missing evidence and incomplete assertion coverage; it does not infer truth from a self-reported pass flag.

Catalog size budgets are approximate UTF-8-byte/4 measures checked during catalog load. They are regression guards, not exact tokenizer counts. Report discovery and activation sizes separately when running real model evaluations.

The [catalog audit runs](runs/catalog-audit/README.md) include recorded assistant forward tests, a schema-validated generated plan, and an executed coding fixture. They are author-graded development evidence, not authenticated native-provider certification or independent-human evaluation. Baseline and revised outputs are retained, including cases where both were already correct.

Measure source footprint with `python evals/catalog_metrics.py --baseline 69ec388`. The result separates discovery descriptions, entrypoints, and all declared supporting content. It excludes adapter output and dependency copies; bytes are not token, latency, or quality measurements.

The deliberately faulty cache under `fixtures/cache` is an input to a coding trial, not production code. The recorded repaired result lives under `runs/catalog-audit/coding-result`; run `python -m unittest discover -s evals/runs/catalog-audit/coding-result -v` to check it. Keep raw evaluation transcripts unchanged rather than autoformatting the recorded outputs.

## Repository-mechanism discovery

The three `*-active-mechanism` cases use `fixtures/credit-ledger`, a deliberately faulty SQLite application with stale prototype notes, an unused in-memory implementation, a configured console-handler path, and passing but incomplete baseline tests. Copy the fixture into a separate temporary directory for each run. Never repair the canonical input or give the actor the grader assertions, another actor's output, or a completed solution.

Give the actor only the selected case prompt, its disposable fixture, and the target skill with required dependencies. Keep proposals, diagnostic databases and grading artifacts outside the fixture unless the implementation case permits edits. Record fixture and instruction hashes, exact model identity, allowed tools, invocation, tool actions and output before grading. Distinguish native provider loading from a delegated assistant explicitly reading rendered instructions.

After the actor finishes, run `python evals/check_credit_ledger.py /absolute/candidate` against the disposable implementation copy. This checks the public CLI, shared service and persisted state for replay, tenant isolation, conflicting payloads, zero/invalid amounts, rollback and concurrent delivery; the deliberately faulty original must fail. It creates its own temporary databases and does not modify candidate source. Keep this grader outside the actor's supplied context.

Run only authorized candidate code. Temporary homes, synthetic databases and a reduced environment are test isolation, not an OS sandbox or a tool-permission enforcement mechanism.

The controlled-contention checks first let both stores finish initialization and install SQLite trace callbacks. The parent then takes a real writer lock and starts both deliveries, holding the lock until both reach their first write boundary. This exposes an unprotected read-before-write without blocking legitimate transactional initialization. Cases cover identical replay and conflicting accounts/amounts; conflicts must produce exactly one accepted payload and no durable effect from the loser. This is an instrumented schedule, not a mock database or a claim to cover every interleaving.

`tests/test_skill_evals.py` includes unprotected read-before-write and unchecked losing-insert controls, plus serialized and transactional-initialization positive controls. This distinction matters: finding the correct store and passing sequential replay tests do not establish atomic retry or conflict behavior. Keep environment-blocked attempts separate from executed failures, and never discard an earlier failed candidate when refining instructions.

Check source hashes for diagnosis/design-only runs. Grade discovery and alternative reasoning from the actual evidence, not keywords, test counts or a prescribed implementation. The fixture tests in `tests/test_skill_evals.py` check the input and grader's reproducibility, not skill behavior. Passing the boundary checker alone does not establish that the actor followed its authority or discovery contract.

These cases are development scenarios, not held-out benchmarks. A successful author-graded trial does not establish comparative improvement, production security or capacity, or exhaustive exploration. Report unsuccessful or incomplete runs without hiding retries; use unseen repositories and repeated, separately graded runs before making broader capability or efficiency claims.

## Layered guidance and handoffs

For `guidance-layered-investigation`, create a new permitted temporary/session project, copy `fixtures/credit-ledger` into `components/credits`, then overlay `fixtures/layered-guidance` at the project root, including its hidden `.claude` directory. The overlay contains root/component instruction imports, an import cycle, sibling-only web guidance, an archived AGENT.md role, a native but irrelevant release-agent definition, and selected stale context with no private-source grant.

Render the target skill for Claude into that disposable project through the normal Engine setup path. Keep the existing root CLAUDE.md/AGENTS.md and nested fixture instructions untouched; generated policies live in `.claude/rules`. If using a delegated assistant rather than a native Claude session, explicitly supply the selected rendered rules/skill and the provider model being simulated. Do not report manual reading as automatic provider discovery.

Redirect scratch paths to a location permitted by the host. Give the actor only the case prompt, composed project and selected instructions, not the assertions or prior outputs. Grade source preservation, actual command choice, context/role provenance and the causal diagnosis separately from file rendering. The other `guidance-*` cases cover provider differences, missing child grants, resumed stale context and instruction changes under review; they are scenarios until executed evidence is recorded.

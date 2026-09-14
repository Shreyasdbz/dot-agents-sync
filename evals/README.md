# Behavioral evaluation protocol

These cases test workflow decisions. Unit tests and catalog validation do not prove that a model follows the instructions.

Run each case in an isolated project using the installed target skill or agent. Give the model the prompt and fixture context, but do not reveal the assertions before it responds. Record provider, model, version, invocation, source pin, exact input, actual output, observed side effects and the grader's evidence for every assertion. Use separate runs for hosted providers and representative local models. Do not claim independence if the author evaluates its own output.

`cases.json` contains the portable scenarios. To grade a recorded run, create a JSON object with `case_id`, `provider`, `model`, `source_revision`, `output`, `observed_actions`, and `assertions` (each with `id`, `passed`, `evidence`). Use `python evals/check_result.py result.json`. It rejects missing evidence and incomplete assertion coverage; it does not infer truth from a self-reported pass flag.

Catalog size budgets are approximate UTF-8-byte/4 measures checked during catalog load. They are regression guards, not exact tokenizer counts. Report discovery and activation sizes separately when running real model evaluations.

The [catalog audit runs](runs/catalog-audit/README.md) include recorded assistant forward tests, a schema-validated generated plan, and an executed coding fixture. They are author-graded development evidence, not authenticated native-provider certification or independent-human evaluation. Baseline and revised outputs are retained, including cases where both were already correct.

Measure source footprint with `python evals/catalog_metrics.py --baseline 69ec388`. The result separates discovery descriptions, entrypoints, and all declared supporting content. It excludes adapter output and dependency copies; bytes are not token, latency, or quality measurements.

The deliberately faulty cache under `fixtures/cache` is an input to a coding trial, not production code. The recorded repaired result lives under `runs/catalog-audit/coding-result`; run `python -m unittest discover -s evals/runs/catalog-audit/coding-result -v` to check it. Keep raw evaluation transcripts unchanged rather than autoformatting the recorded outputs.

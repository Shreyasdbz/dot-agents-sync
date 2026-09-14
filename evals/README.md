# Behavioral evaluation protocol

These cases test workflow decisions. Unit tests and catalog validation do not prove that a model follows the instructions.

Run each case in an isolated project using the installed target skill or agent. Give the model the prompt and fixture context, but do not reveal the assertions before it responds. Record provider, model, version, invocation, source pin, exact input, actual output, observed side effects and the grader's evidence for every assertion. Use separate runs for hosted providers and representative local models. Do not claim independence if the author evaluates its own output.

`cases.json` contains the portable scenarios. To grade a recorded run, create a JSON object with `case_id`, `provider`, `model`, `source_revision`, `output`, `observed_actions`, and `assertions` (each with `id`, `passed`, `evidence`). Use `python evals/check_result.py result.json`. It rejects missing evidence and incomplete assertion coverage; it does not infer truth from a self-reported pass flag.

Catalog size budgets are approximate UTF-8-byte/4 measures checked during catalog load. They are regression guards, not exact tokenizer counts. Report discovery and activation sizes separately when running real model evaluations.

No authenticated model evaluation result is shipped as a claimed pass. The repo's structural CI and model behavior certification are distinct evidence.

# Provider adapter contract

Renderers receive resolved packages, bindings, configuration and scope. They return deterministic relative paths, bytes, modes, owners and capability decisions. They never write files, fetch packages, execute hooks or change provider settings themselves.

Core validation confines paths to the provider-owned roots. Every file has one owner in the global state database. Root instructions and native settings are collision-protected because replacing them can affect behavior outside an individual package.

Sources checked for the v1 format mapping:

- [Codex skills](https://developers.openai.com/codex/skills): `.agents/skills` in user and project scopes, with name and description in SKILL.md plus generated `agents/openai.yaml` display metadata.
- [Codex subagents](https://developers.openai.com/codex/subagents): native TOML agent definitions. dasync omits model pins so the parent environment controls the model.
- [Codex hooks](https://developers.openai.com/codex/hooks): scoped hooks.json and command hook event declarations.
- [Claude skills](https://code.claude.com/docs/en/skills), [subagents](https://code.claude.com/docs/en/sub-agents), and [hooks](https://code.claude.com/docs/en/hooks): native skill and agent directories plus settings-based event wiring.
- [GitHub Copilot CLI skills](https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/add-skills), [custom agents](https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli), [custom instructions](https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions), and [hooks](https://docs.github.com/copilot/how-tos/copilot-cli/customize-copilot/use-hooks): `.copilot` user discovery, `.github` project discovery and versioned hook files.
- [Cursor skills](https://cursor.com/docs/skills), [rules](https://cursor.com/docs/rules), and [hooks](https://cursor.com/docs/hooks): skills, project MDC rules and hooks.json.

Generated direct dependency references are relative to the consuming skill. Private bindings are represented by IDs, never copied bodies or embedded source paths. Hook commands contain a machine-bound absolute script path and Python executable; plans therefore bind to the executing machine.

Unconditional policies use native discovery rather than repeated dependency copies; Cursor user policies retain explicit manual references. Copilot policy files always include `applyTo`, using `"**"` when no path restriction is selected. Runtime exclusions and actual host loading remain outside the renderer's evidence. See [repository guidance](repository-guidance.md) for the dated discovery matrix, instruction/role distinction and known provider-documentation conflicts.

Tests check deterministic output, metadata parsing, expected discovery paths, no model pins, unsupported-feature diagnostics and idempotent sync through every provider. Live authenticated runtime behavior and future provider releases require separate conformance runs.

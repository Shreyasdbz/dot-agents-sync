# Security

## Reporting a vulnerability

Report suspected vulnerabilities through [GitHub private vulnerability reporting](https://github.com/Shreyasdbz/dot-agents-sync/security/advisories/new), which is enabled for this repository. Do not open a public issue or PR containing exploit details, credentials, private context, session transcripts, or unredacted user configuration.

A useful private report identifies the affected version or commit, operating system and provider, prerequisites, expected and actual behavior, impact, and minimal reproduction steps using a disposable catalog, project, and `DASYNC_HOME`. Use synthetic data and sanitized logs, not a real home directory or state database. If a credential was exposed, revoke or rotate it through its issuer; removing a public post is not sufficient.

No response or remediation timeline is guaranteed. There is no published supported-version or security-backport policy; see [release readiness](docs/releasing.md) for distribution status.

## Trust and execution boundaries

Selected packages can instruct AI agents and approved scripts can execute with provider permissions. Review source changes and executable digests. Pin trusted Git commits. Hooks are guardrails, not an OS sandbox. A local actor with write access to the state database or parent directories is outside the integrity boundary.

`--yes` confirms ordinary changes only; source trust, executable-digest approval, and private-context authorization remain separate gates. Never include private context bodies or private-path lookup results in public reports.

POSIX filesystem writes use no-follow directory traversal, staged replacement, durable journaling and post-write verification. Windows adversarial directory replacement is not certified, and native Windows hooks are blocked. `--conflict overwrite` explicitly permits replacement; originals remain in receipt backups. These mechanisms do not make untrusted package content safe to execute.

See the [operator contract](docs/AI-OPERATOR.md) for safe planning and recovery and the [implementation contract](docs/architecture/implementation.md) for the precise boundaries and known limitations.

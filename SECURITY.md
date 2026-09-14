# Security

Do not include credentials, private context, session transcripts or unredacted user configuration in an issue. Report a minimal reproducer using a temporary catalog and `DASYNC_HOME` sandbox. Use GitHub private vulnerability reporting when available.

Selected packages can instruct AI agents and approved scripts can execute with provider permissions. Review source changes and executable digests. Pin trusted Git commits. Hooks are guardrails, not an OS sandbox. A local actor with write access to the state database or parent directories is outside the integrity boundary.

POSIX filesystem writes use no-follow directory traversal, staged replacement, durable journaling and post-write verification. Windows adversarial directory replacement and native hook execution are not certified. `--conflict overwrite` is an explicit data replacement operation; originals remain in receipt backups.

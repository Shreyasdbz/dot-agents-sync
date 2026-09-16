# Implementation decisions

The design snapshot in `design.md` preserves the agreed product direction. This file records concrete v1 implementation choices and verification limits.

## Runtime and distribution

Python 3.11+ provides SQLite, TOML parsing, cross-platform paths, subprocess control, file descriptors and mature testing. `uv tool install .` or `pipx install .` installs the CLI; the catalog is independently pinned from a Git source. `uv.lock` pins development dependencies; it is not a dasync environment lockfile.

## Configuration footprint

One platform-native user configuration and one project `.dasync.yaml` hold desired state. `DASYNC_HOME` redirects config, state, cache and provider output into a sandbox for tests and demos. State, backups and crash journals share one private SQLite database. No project-local cache, backup, private directory or dasync lockfile is created. Provider-native output is additional materialized configuration, as required by the design.

JSON serialization is used for generated configuration because JSON is valid YAML and has a stable, lossless representation. Hand-authored YAML is accepted with duplicate keys, aliases, anchors and unsafe tags rejected. Config edits normalize formatting; comments are not preserved.

## Sources and inheritance

HTTPS Git sources use a global mirror cache and full immutable commit IDs. Local Git sources read commit objects rather than checkout bytes. Local development directories use an explicit `sha256:` tree pin and reject changes until update accepts a new pin. Manifests and declared content determine computed package digests; no self-referential manifest digest is required.

Version 1 resolves one catalog pin per effective environment. Inherited user and project environments must use the same source and pin; mismatches fail explicitly. Projects can have independent pins when inheritance is disabled. Multiple independently versioned source graphs remain a future feature requiring a lockfile design.

## Plan and transaction semantics

Plans contain operation hashes, input hashes, source digests, provenance, capabilities, versions, exact scope and the last receipt. File contents are re-rendered during apply and compared against the reviewed plan; generated bodies are not transported in plan JSON. A plan remains valid only while all bound inputs match. There is no wall-clock expiry. Plans are local-machine execution artifacts because paths and platform identity are bound.

All writes use one transaction engine. An OS advisory lock serializes transactions across scopes sharing the database, a stricter rule than per-scope locking. Locks release on process death. Backups are durably journaled before writes; each replacement uses a temporary file in the destination directory, fsync and atomic rename. A receipt and its backups commit only after verification. Several target files cannot change simultaneously at the filesystem level; the journal makes partial transitions recoverable.

POSIX file operations open path components with no-follow semantics and hold parent directory descriptors. Windows uses the available path checks and atomic replacement; protection against a hostile process concurrently replacing Windows directory junctions is not claimed. Local actors that can alter the private state database or parent directories are outside the integrity boundary.

Recovery restores only files matching either the recorded before or after state. Independent edits cause a recovery conflict and retain the journal. Overwritten unmanaged originals remain in successful receipt backups and can be restored with `rollback --before --receipt ID`.

Configure-only receipts preserve the prior output ownership and hashes, including drift. They do not silently adopt observed edits. Modified managed files and unmanaged collisions, even byte-identical ones, require explicit `--conflict overwrite`. That action preserves originals in receipt backups; no content is imported as canonical.

## Provider behavior

Codex uses `.agents/skills`, native `.codex/agents/*.toml`, and scoped instructions. Claude uses `.claude/skills`, `.claude/agents`, and `.claude/rules`. GitHub Copilot CLI uses `.copilot` for user skills, agents, instructions and hooks and `.github` for their project equivalents. Cursor uses `.cursor/skills` and project `.cursor/rules/*.mdc`; user policies and standalone agent roles fall back to explicitly reported manual references. Optional private context bytes are never copied. Generated references identify a binding that an authorized consumer can locate explicitly.

An explicitly requested setup migration may replace unmanaged content only within documented provider discovery paths. The plan enumerates regular files and leaf symlinks without following symlinks, requires source trust plus conflict overwrite, and journals each displaced entry before mutation. Inline hook settings are replaced while unrelated JSONC settings are carried through; a setting that disables all Copilot hooks blocks installation of a managed Copilot hook. Provider authentication, sessions, caches, plugins, MCP definitions and source repositories are outside this replacement boundary. Directory containers are not deleted; an old discovery-root symlink is restored only after transaction-created containers are proven empty. User-scope Copilot management rejects a nondefault `COPILOT_HOME` because independently rooted provider output is not represented in the v1 scope model.

Adapters detect executable availability and declare format support. Runtime service capabilities such as web search and parallel agents require explicit configuration; installation alone is not evidence those services work. Structural conformance tests do not establish behavior in an authenticated model session.

Native hooks are optional, separately approved executable packages. Codex and Cursor use scoped hooks.json, Claude uses settings.json, and Copilot uses a dedicated JSON file in its scoped hooks directory. Existing native files remain collision-protected. Hooks run in the provider execution environment using the installed Python interpreter; dasync does not claim a portable OS sandbox. Windows hook commands are blocked until their shell-specific invocation is tested. General profiles never include hooks.

## Planning output

Plan Out loads the project's authority and native hierarchy from context. Its portable Plan Context supports local, GitHub, ADO, Linear, Jira and Notion references, progressive milestones, phases and tasks. Tracker writes use the hosting agent's connected tools and configured work-item model. The dasync CLI validates and distributes the workflow; it is not an issue-tracker synchronization service. The schema and template supersede the old design snapshot's implementation-plan-extension references.

## Deferred from v1

Independent multi-source version resolution, cryptographic release signing, unattended model evaluation runs, native Windows hook invocation, importing provider files into canonical packages, and a portable hook sandbox need separate implementation and evidence. Behavioral eval cases and an evaluation protocol ship with the repository; successful live model runs must be recorded before claiming behavioral certification.

# Releases and work tracking

## Current distribution status

Original code and catalog content are covered by the [MIT license](../LICENSE). Install the CLI from source or use the inspected artifacts attached to a [GitHub release](https://github.com/Shreyasdbz/dot-agents-sync/releases). There is no PyPI publication from this project.

macOS and Linux are covered by the existing CI matrix. Windows lifecycle behavior and native hooks are not release-certified. Structural package and provider tests do not certify authenticated model workflows. See [testing](testing.md) and the revision-specific [verification record](verification.md).

## GitHub work tracking

The public [dasync Project](https://github.com/users/Shreyasdbz/projects/8) is linked to this repository and provides Board and Work list views. GitHub issues, milestones, and Project Status are the writable planning authority; this guide is not a second status board.

| Issue | Outcome |
| --- | --- |
| [#1](https://github.com/Shreyasdbz/dot-agents-sync/issues/1) | Approve the license and audit redistribution notices |
| [#2](https://github.com/Shreyasdbz/dot-agents-sync/issues/2) | Publish the documentation and contributor intake refresh |
| [#3](https://github.com/Shreyasdbz/dot-agents-sync/issues/3) | Create or designate the repository Project |
| [#4](https://github.com/Shreyasdbz/dot-agents-sync/issues/4) | Prepare and publish the first reviewed source release |

The [0.1.0 open-source readiness milestone](https://github.com/Shreyasdbz/dot-agents-sync/milestone/1) groups these initial release items. The release issue depends on licensing and documentation through native blocking relationships. These are standalone maintenance items, not feature implementation tasks requiring an artificial Feature parent.

Status values are Backlog, Ready, In progress, In review, and Done. Ready means scope, acceptance, and dependencies are clear. Done requires recorded acceptance, not just a merged PR. GitHub's default workflows remain enabled, including automatic closure/status workflows; preserve their configuration and read back issue and Project state after changes.

This personal repository does not expose working native issue types: `gh issue edit --type Task` reports no available types. Work therefore uses descriptive issue bodies, native milestones and dependencies, and Project Status without labels pretending to be Task, Bug, or Feature. [#3](https://github.com/Shreyasdbz/dot-agents-sync/issues/3) records the provider limitation and approved continuation.

Use the existing Project's exact identity: number `8`, ID `PVT_kwHOAOKmv84Bjuvj`, owner `Shreyasdbz`. Add each issue once, preserve existing metadata, and elaborate only the immediate milestone. Future milestones receive one planning task until they become current. Do not create a second writable roadmap.

## Licensing checks

Keep the root license, Python package metadata, and original catalog manifest licenses consistent. Audit new adapted guidance, templates, and vendored material separately from runtime dependencies; preserve required upstream notices.

[Third-party notices](../THIRD_PARTY_NOTICES.md) identify adapted catalog material and its packaged license. A notice needed by a distributed skill must be declared in its manifest so it accompanies provider-native output, not just the source repository.

Check built archives for required license files and notices. Historical verification reports describe their original revisions; do not rewrite them to imply the license existed before it was adopted.

## Candidate release checks

Start from a clean, reviewed candidate commit. The existing CI workflow is the authoritative automated gate:

```sh
uv sync --locked
uv run pytest
uv run ruff check cli tests packages/hooks evals scripts/build_templates.py
uv run ruff format --check cli tests packages/hooks evals scripts/build_templates.py
uv build
```

Run the [browser acceptance commands](testing.md#browser-acceptance) for the distributed HTML templates. Link the successful CI run for the actual candidate commit, not an earlier revision.

Inspect the wheel and source archive: console entry point, version, README, project URLs, license metadata, and included notices must match the candidate. The catalog is independently pinned; do not claim it is bundled in the CLI wheel.

Install the built wheel in a disposable environment, then run setup, doctor, and idempotent sync with temporary `DASYNC_HOME`, catalog, and project directories. The [installed-package tests](testing.md#installed-package-journeys) cover this boundary without touching real provider configuration. Also exercise the intended published Git source at the exact release revision.

## Publication boundary

Tagging, GitHub release publication, and package-index publication require explicit authorization. A passing build does not publish anything. PyPI publishing and automated release workflows are outside this first source-release milestone.

For an authorized GitHub release, record the tag's full commit ID, CLI version, catalog revision, artifact SHA-256 hashes, install instructions, supported platforms, and known limitations. Upload only inspected source and wheel artifacts, then read back the tag target and release assets. Do not include local plans, private context, credentials, caches, or test logs.

## After a release

Keep the CLI version and catalog pin distinct in upgrade notes. Catalog `update` advances workflow content; it does not upgrade the installed CLI. Record changed executable digests, new approvals, migration risks, and rollback guidance where applicable.

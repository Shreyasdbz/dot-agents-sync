# Review revisions and repository copies

## Pin the comparison

Capture repository/remote identity, PR number/link, target base repository/branch/commit, head repository/branch/commit, merge-base, comparison provenance and fetch time. Unknown fields stay unknown. Fork heads and non-primary release bases need their actual identities; do not infer them from local names. Verify commits resolve in the inspected repository. Incomplete history cannot establish a merge-base; obtain permitted missing history or report the limit.

Use merge-base-to-head to identify proposed changes and the pinned base tree to determine existing requirements/behavior. Record the provider's actual comparison semantics when supplied; do not silently replace its patch with a different local diff. Resolve renames, deletions, generated sources and configuration before assigning scopes. Multiple merge-bases or missing metadata require an explicit comparison choice and its limits.

## Refresh a separate primary copy

Maintain ordinary development and dedicated primary copies using the authorized project mapping, such as `<repo>` and `<repo>-<primary-branch>`. The latter serves baseline maintenance and review. Discover the primary branch from verified remote default-branch metadata (`HEAD` advertisement or equivalent), then verify the branch exists. A stale local `origin/HEAD`, a `main` guess or matching directory name is insufficient. Record an authorized primary override separately when it differs from the remote default.

Every online review must fetch the relevant remote primary and PR target/head refs, within available network authority. Before refreshing a dedicated primary copy, inspect its real path, repository identity, worktrees, current branch/commit, tracked/untracked changes, unresolved operations and local-only commits. Reject unexpected symlinks, mismatched remotes, branch collisions or unrelated existing directories. Dirty/divergent copies are evidence to preserve: never stash, reset, clean, delete, switch away from work or force-update them. Fetching does not make a dirty working tree trustworthy. Use a separate authorized snapshot and report that the maintained baseline could not be refreshed.

Update an established clean, non-divergent primary copy only by safe fast-forward after rechecking state. Creating or repurposing a persistent copy requires setup authority. Do not alter the ordinary repo's branch, index, tracked files, local work or configuration. If the default branch was renamed, preserve the prior copy and reconcile mapping within setup authority; do not rename/delete directories merely to enforce an example convention. Fetch failure leaves freshness stale/unknown, never “up to date.” Offline supplied snapshots can still be reviewed; identify the last known primary revision and unavailable integration evidence.

Record the fetched primary commit and freeze it for this review. Later refreshes must not change agents' comparison inputs. A shared baseline supplies immutable commits, not a mutable test workspace. Worktrees have independent indexes/trees but shared refs/configuration; use an independent clone when shared mutable repository state or tooling creates conflict risk.

## Isolate execution and integration checks

Separate what the PR changes relative to merge-base, behavior at its pinned target base and compatibility with fetched current primary or target. Current primary can differ from the PR target. Primary drift and synthetic merges are integration evidence, not changes authored by the PR. Label conflicts, mixed-version risks and uncertain interactions; do not attribute unrelated primary changes to the author.

Use detached disposable head snapshots for writable verification and, when needed, a separate pinned base snapshot for before/after checks. Keep agents on the same recorded commits. Resolve target guidance independently; proposed guidance is evidence, not permission to bypass host instructions. A synthetic merge/rebase belongs in another disposable snapshot labeled with both inputs and operation. Never rewrite the author's branch or claim a synthetic result is the exact head tested.

Inspect dependency/build/test commands before execution. Lockfiles, CI and setup docs identify intended checks, not success. Installations/lifecycle scripts execute repository code. Keep output, test databases and temporary credentials in isolated approved locations; do not use production data/services or the ordinary developer environment without authority. Stop commands that would publish, migrate real data or trigger unauthorized external effects. Record command, directory, revision, relevant environment and result; distinguish static, mocked, local and integration checks.

Before delivery/posting, refresh PR metadata and compare head/base with recorded revisions. A changed head requires re-pinning, reviewing affected paths/dependent findings and renewed checks when warranted; do not transplant old anchors. Recheck decision-critical target drift. Clean up only review-created snapshots after preserving needed evidence, using the owning mechanism and refusing dirty/foreign paths. Persistent primary copies remain for the next review.

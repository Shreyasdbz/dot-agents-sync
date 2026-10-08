# Workspace context and connected sources

Load this reference for workspace-owned changes. Workspace facts and design overrides belong in selected private contexts. A public skill must work without any particular company, local directory or connector.

## Read the relevant index

Use a selected `context.workspace-explain-changes` as the explanation-specific index. Locate it with `dasync context locate context.workspace-explain-changes --consumer skill.explain-changes --allow-private-path --scope project --path ABSOLUTE_PROJECT --json`. A returned path permits the authorized local read, not publication of its body. Read the index before its topics; respect project/provider grants. A missing or denied binding remains a gap, not permission to find a substitute private source.

If `context.workspace-overview` is selected, use its authorized consumer lookup to resolve repository boundaries and environments. For `context.workspace-artifacts`, follow skill.visual-artifacts's brand lookup. Apply the verified local CSS/assets to this explanation using `data-artifact-kind="explanation"`, while preserving semantic colors, content and offline behavior. A brand request with missing assets should produce an explicit limit, not a fabricated logo or font.

## Search for intent and contracts

Inventory the available authorized workspace repositories by identity, role, revision and checkout state. Check each for relevance to the changed producers/consumers; read applicable guidance and only relevant code/docs. Separate duplicate worktrees and primary copies; neither folder naming nor “main” proves freshness. Follow concrete contract edges across repos. “All available repos” means considering the authorized inventory and tracing affected repos, not loading all their files.

Use available connected Notion, Linear and GitHub search/read tools when the workspace selects those sources. Discover actual tools rather than embedding a provider-specific tool name as a guarantee. Search exact issue/PR IDs, changed symbols, feature names and cited document titles. Fetch relevant hits before relying on them. Validate the workspace/organization and project identity against authorized context; a matching title in another workspace is not the intended source.

Use Notion for relevant requirements/design/decisions, Linear for acceptance/scope/dependencies/status, and GitHub for pinned implementation/discussion/checks. Code may contradict a document: explain the difference rather than inventing a reconciled story. Repositories establish implementation, not product approval. Connector access does not authorize writing, posting, exporting unrelated data or broadening privacy grants.

Start with focused independent queries, then follow returned references and affected boundaries. Stop when consequential claims are supported or identified as gaps, and another query adds no new mechanism, requirement or risk. Paginate the material file list; do not imply full retrieval when results are truncated. Record the sources and relevant query coverage used, unavailable access, mismatched workspaces and remaining uncertainty. Do not require unbounded searching or stall all explanation work because one connector is absent.

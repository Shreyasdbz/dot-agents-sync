# Workflow catalog

The catalog is optional content, pinned independently from the CLI. Select profiles or individual packages; required dependencies follow automatically, but suggestions do not. Selection never authorizes account changes, external posting, purchases, or publishing.

## Inspect before selecting

```sh
# Inspect the checked-out catalog without installing it.
dasync list --source /absolute/dot-agents-sync --source-kind local --json
dasync search review --source /absolute/dot-agents-sync --source-kind local --json

# Inspect an existing environment.
dasync list --scope project --path /absolute/my-project --json
dasync explain skill.pr-review --scope project --path /absolute/my-project --json
```

`list` includes the actual profile membership, dependencies, and computed digests. It is the source of truth when catalog content changes.

## Profiles

| Profile | Selection |
| --- | --- |
| `dev-core` | Propose, Plan Out, Do It, Investigate |
| `dev-review` | PR Review and its supporting dependencies |
| `technical-storytelling` | Pitch Deck and its supporting dependencies |
| `ui-design` | One UI routing skill with on-demand guidance |
| `visual-artifacts` | Focused visual explanations, diagrams and interactive HTML |
| `engineering-cloudflare` | Cloudflare-first/GCP-next engineering conventions and public stack context |
| `planning-github` | Plan Out, native GitHub planning conventions, and public reference material |
| `travel` | Travel Planner and Trip Publish |
| `personal-music` | Apple Music playlist curation |

Add a profile to an existing environment with `dasync configure --scope user --profile ui-design --apply --yes`. Preview with `--dry-run --json` first. General profiles do not include executable hooks.

`--all-public` opts into every current and future non-private package compatible with the scope and all configured providers. Explicit disabled IDs still win. Newly selected executable packages require their own exact digest approval; private contexts require bindings and grants.

## Package kinds

| Kind | Purpose |
| --- | --- |
| Skill | A discoverable workflow such as proposing, investigating, or reviewing |
| Agent | A specialist role for bounded delegated work |
| Policy | Rules for scope, coding, verification, security, and communication |
| Context | Public reference material or a contract for private facts and preferences |
| Template | Reusable proposal, plan, review, presentation, travel, or playlist structure |
| Hook | An optional executable guardrail running with provider permissions |

Propose makes supported design decisions. Plan Out elaborates only the next milestone against the project's planning authority. Investigate and PR Review return inline results by default. Pitch Deck and Trip Publish can produce self-contained HTML artifacts; creating a file is distinct from hosting it.

`skill.change-quiz` creates a visual, four-option HTML quiz for a pinned PR or local change snapshot. It studies consequential behavior and external boundaries, varies question count by scope and severity, and reveals explanations for every option immediately on selection. Its `template.change-quiz` preserves prior revision sections inside one collapsed History disclosure. Select it with `--enable skill.change-quiz`; [the authoring research](../packages/skills/change-quiz/research.md) records the design choices and verification limits.

`skill.explain-changes` explains a PR, diff or current-session effort in one scrollable, self-contained visual HTML file. It traces before/after behavior through relevant code and documents, connects engineering/product/UX perspectives, and applies ASD-STE100 writing guidance without claiming unverified dictionary compliance. Select it with `--enable skill.explain-changes`. Its worked template includes offline sources, glossary, keyboard disclosures, themes and print. Default workspace destination is `artifacts/explanations/`.

`context.artifact-routing` is the shared public destination contract for requested review, quiz, deck, proposal, investigation, plan-view and trip-guide files. An explicit destination wins; otherwise an unambiguous workspace uses its `artifacts/<kind>/` folder. Ambiguous or unknown workspaces need a destination decision before writing. Inline answers stay inline, and Plan Context JSON remains with the selected planning authority. The contract guides skills; dasync does not itself write their artifacts.

All catalog skills and agents inherit the natural-paragraph Markdown rule through `policy.communication`. Templates are dependencies where required, not permission to invent missing content.

`skill.visual-artifacts` supplies shared visual craft for Pitch Deck, UI Design, Propose, PR Review, Investigate, Plan Out and Trip Publish. Those workflows load it when creating or improving visuals; their original scope and default formats remain authoritative. Its compact entrypoint routes to composition, diagram and motion references only when relevant. It chooses focused trees, diffs, tables or Mermaid for simple relationships and interactive HTML/SVG for explanations that need spatial layout or state exploration. See its [inspiration and provenance](../packages/skills/visual-artifacts/composition.md#inspiration-and-provenance); this is original catalog guidance, not an installation of the upstream skills.

Do It, Investigate, Propose, Plan Out, PR Review and the five engineering reviewers also require `policy.repository-guidance`. It defines scoped instruction discovery, selective context loading and bounded agent handoffs without activating private bindings or additional roles. See [repository guidance](repository-guidance.md) for native filename and loading differences.

## Optional integrations and conventions

The `ui-design` skill uses the read-only [UI Skills MCP server](https://www.ui-skills.com/mcp/docs) when available and requests registration at the selected scope when absent. SwiftUI guidance loads only for relevant Apple UI work; the supporting reference retains attribution to the MIT-licensed [fwc-swiftui-skills](https://github.com/FloWritesCode/fwc-swiftui-skills).

The [engineering profile](engineering-profile.md) adds platform, monorepo, and TanStack/shadcn conventions without changing the general profiles. Its public context covers workload-selected databases, LOCAL + PROD, and post-POC observability. The [observability comparison](observability-options.md) is dated research, not a selected or installed vendor.

The [planning and travel guide](planning-and-travel-context.md) explains GitHub-native planning conventions and the Travel Planner agent. Trip Plan remains a compatibility entrypoint; the travel profile selects the agent directly. dasync distributes these workflows but does not implement a tracker synchronization service.

## Private context

Private context packages define binding contracts, not fabricated personal facts. Bind an existing file in user scope, then authorize its use in a specific project:

```sh
dasync configure --scope user \
  --bind-context context.design-preferences=/absolute/private/design.md \
  --grant-project my-project --binding-provider codex --yes
dasync configure --scope project --path /absolute/my-project \
  --enable context.design-preferences --allow-context context.design-preferences --apply --yes
```

Both scopes must already be configured. The project ID must match `.dasync.yaml`, provider grants must cover its configured providers, and inherited scopes must share the same source and pin. Private bytes stay at their source; generated references identify an authorized lookup, not a copy of the private file. Never share private bindings or paths in public reports.

For a workspace spanning several repositories, `context.workspace-overview` holds a separately granted private source for repository boundaries and environment combinations. Optional `context.workspace-pr-review`, `context.workspace-plan-out`, and `context.workspace-do-it` bind narrower sources for those skills; each declares its authorized consumer. Select and grant these per project rather than adding organization facts to public skill packages. The shared repository-guidance policy asks for relevant cross-repository and environment walkthroughs and bounded context refresh during related work.

`context.workspace-explain-changes` binds the private repository and Notion/Linear/GitHub source index for Explain Changes, with `skill.explain-changes` as its sole consumer. It records actual connector identities, tested access and gaps; it does not assume every connected workspace belongs to the same company. Pair it with the existing workspace-artifacts brand binding. The public skill and template contain no workspace facts or assets.

`context.workspace-artifacts` optionally binds workspace branding for HTML artifacts across visual workflows. Its private source owns the brand tokens, offline assets and visual verification guidance; the public templates provide optional logo/name/label slots. Select and grant it per project. Generic templates remain unbranded without an authorized composition.

See [context authoring](context-authoring.md) for binding contracts and [the operator contract](AI-OPERATOR.md) for private-path access.

## Executable hooks

Hooks are separately approved executable packages and are never included by a general profile. Review source, permissions, and the exact digest reported by `list` before approving one. Content or permission changes require fresh approval.

The credential-path guard is a guardrail, not an OS sandbox. Hooks execute with provider permissions; native Windows hook commands are blocked pending platform-specific evidence. See [package authoring](package-authoring.md) for the executable contract.

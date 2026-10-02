# Workspace layout and artifact routing

This is a generic destination contract, not a list of configured workspace names or permission to read private context. A workspace root can contain `repos/` for source checkouts, `artifacts/` for requested durable outputs, and `contexts/` for separately authorized private sources. Do not write generated reports or decks into `repos/` or `contexts/` merely because a task started there.

An explicit user destination takes precedence, subject to the applicable path and privacy rules. Otherwise identify the workspace that owns the task from its authorized repository or source. Use `artifacts/<kind>/` only when exactly one workspace is supported by that evidence and has an `artifacts/` directory. If no workspace is established or two roots plausibly own the output, ask for a destination before writing a file; give an inline answer when the workflow permits it. Do not infer a workspace from a personal home-directory name alone.

| Requested artifact | Default kind |
| --- | --- |
| PR review Markdown or HTML | `pr-reviews/` |
| Change-understanding quiz HTML | `quizzes/` |
| Presentation HTML | `decks/` |
| Design proposal Markdown or HTML | `proposals/` |
| Investigation Markdown | `investigations/` |
| Plan Out Markdown or HTML view | `plans/` |
| Published trip HTML | `trips/` |

Plan Context JSON follows the project's selected planning authority or an explicit user destination; this table does not create a competing plan store. Inline-only results stay inline. Create a category directory only when writing a requested file. Check the resolved destination and parent path before writing: reject traversal and unexpected links outside a workspace-derived destination, and validate an explicit destination against its own authorization. Preserve existing files; choose a distinct name or ask before replacing one. Never move existing artifacts as part of routing. Report the actual output path after a successful write. A local file is not published or shared by virtue of its location.

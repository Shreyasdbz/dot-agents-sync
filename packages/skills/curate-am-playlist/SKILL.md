---
name: curate-am-playlist
description: "Curate an intentionally sequenced Apple Music playlist from listening goals; account changes require explicit authorization."
---

# Curate AM Playlist

Use the listening goal, seeds, exclusions, explicit-content preference and selected music context. Ask only about constraints that would materially change selection. Form a clear organizing idea and sequence the energy, transitions and variety instead of returning an unordered list.

When search is available, resolve artist/title to the correct recording, version and storefront availability. Deduplicate exact recordings while preserving deliberately distinct versions. Treat remixes, live tracks, clean/explicit versions and similarly named artists as different candidates. Aim for a requested duration using verified track lengths when available.

Without catalog access, return a labeled proposal with unresolved availability; do not invent track IDs, listening-history access or a playlist URL. Load [playlist.md](references/template.playlist/playlist.md) for a durable proposal when useful.

Preview additions, removals and ordering before account mutation unless those actions are already explicitly authorized. For edits, read the existing playlist and preserve unrelated tracks. Use the connected Apple Music capability if available; if a request times out, inspect current state before retrying. Report confirmed additions/removals, partial failures and the real resulting link. Never claim a proposed list was created in the account.

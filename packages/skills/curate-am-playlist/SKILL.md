---
name: curate-am-playlist
description: "Curate an Apple Music playlist using listening goals, exclusions and sequencing preferences."
---

# Curate AM Playlist

Given a listening goal, mood, activity, seed tracks, exclusions, or other request, curate an Apple Music playlist using available music-preferences context. Explain the organizing idea and make sequencing intentional rather than returning an unordered song list.

- Boundary: preview the proposed playlist and any replacements before mutating an external account unless the invocation explicitly authorizes creation or editing.

- Output: a playlist proposal and, when authorized and supported, the resulting Apple Music playlist.

- Typical dependencies: music-preferences context, curation-quality policy, and Apple Music search or playlist-management capability.

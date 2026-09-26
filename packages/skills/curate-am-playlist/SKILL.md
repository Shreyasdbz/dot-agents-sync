---
name: curate-am-playlist
description: "Curate or update Apple Music playlists, checking album tracks, explicit versions and song IDs when lookup is available."
---

# Curate Apple Music Playlist

Use the listener's occasion, seeds, exclusions, duration, discovery appetite, content preference and any selected music context. Ask only for a missing constraint that would change the selections. A stated clean-only preference takes precedence; otherwise prefer an explicit recording when the same intended track has an explicit and a clean counterpart. An unrated track is not automatically a clean edit.

Choose tracks for a specific listening experience, not just topic matches. Establish a few anchors, then add songs that earn their place through fit, contrast or discovery. Balance familiarity with surprise to suit the request; avoid filler, accidental repeats and long runs of one artist unless the concept calls for them. Sequence for an opening, development and landing, checking neighboring tracks for plausible changes in energy, texture, voice or era. Do not claim exact tempo, key or a seamless transition without listening evidence. Trim weak matches rather than padding to a requested length; use verified durations for a precise runtime.

Use available Apple Music catalog tools or public Apple Music pages to seek an exact song ID for every selected track, including user-supplied seeds. Follow [catalog-selection.md](references/catalog-selection.md) for storefront, recording, release, content-rating and ID checks. A supplied title, ISRC, link or ID is a lead, not proof of the desired catalog item. Keep deliberately requested live, remix, cover or alternate versions distinct.

If no reliable catalog lookup is available, give an ordered proposal and mark IDs, versions, explicit status, availability and duration as unverified where applicable. Do not invent listening-history access, catalog IDs or a playlist URL. Load [playlist.md](references/template.playlist/playlist.md) when a durable proposal is useful.

Preview additions, removals and order before account mutation unless those actions are already authorized. For edits, read the existing playlist and preserve unrelated tracks. After an authorized write, read back the playlist; if a request times out, inspect current state before retrying. Report confirmed changes, partial failures and the resulting link. Never present a proposed list as an account playlist.

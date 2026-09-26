---
name: curate-am-playlist
description: "Curate Apple Music playlists, verify song versions and IDs, and prepare CSVs for Music Transfer when requested."
---

# Curate Apple Music Playlist

Use the listener's occasion, seeds, exclusions, duration, discovery appetite, content preference and any selected music context. Ask only for a missing constraint that would change the selections. A stated clean-only preference takes precedence; otherwise prefer an explicit recording when the same intended track has an explicit and a clean counterpart. An unrated track is not automatically a clean edit.

Choose tracks for a specific listening experience, not just topic matches. Establish a few anchors, then add songs that earn their place through fit, contrast or discovery. Balance familiarity with surprise to suit the request; avoid filler, accidental repeats and long runs of one artist unless the concept calls for them. Sequence for an opening, development and landing, checking neighboring tracks for plausible changes in energy, texture, voice or era. Do not claim exact tempo, key or a seamless transition without listening evidence. Trim weak matches rather than padding to a requested length; use verified durations for a precise runtime.

Use available Apple Music catalog tools or public Apple Music pages to seek an exact song ID for every selected track, including user-supplied seeds. Follow [catalog-selection.md](references/catalog-selection.md) for storefront, recording, release, content-rating and ID checks. A supplied title, ISRC, link or ID is a lead, not proof of the desired catalog item. Keep deliberately requested live, remix, cover or alternate versions distinct.

For this listener’s [Music Transfer](https://pages.shreyassane.com/music-transfer) workflow, deliver a real UTF-8 CSV when a playlist is ready for import. Load [playlist.md](references/template.playlist/playlist.md) for the format and check the app’s live CSV guide before export. Put verified Apple Music catalog song IDs in the CSV; leave unresolved IDs blank and identify those rows for review because the app uses conservative matching. Do not fill a blank ID with a guessed clean edition, album ID or library ID. The app adds to a selected Apple Music destination and does not remove or reorder existing recordings, so do not promise that an import will create a destination or rearrange its contents.

If no reliable catalog lookup is available, still prepare an ordered proposal or CSV when useful, with IDs and unsupported version, rating, availability and duration claims left unverified. Do not invent listening-history access, catalog IDs or a playlist URL.

Preparing a CSV does not import it. Preview the intended destination and rows before an authorized import. For updates, inspect the existing playlist and preserve unrelated tracks. After import, inspect the app’s review or transfer ledger and the destination playlist; reconcile uncertain or partial results before retrying. Report a playlist link only when confirmed. Never present a CSV or proposed list as an account playlist.

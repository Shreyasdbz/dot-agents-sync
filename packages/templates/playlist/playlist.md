# Playlist composition guide

## Listening intent

Audience, occasion, energy arc, preferred duration, language/content constraints and supplied preferences. Do not invent a psychological profile from a short prompt.

## Choose a view

For discovery, group candidates by listening purpose before proposing an order. For a finished preview, show an ordered sequence. For an update, show additions/removals/reordering against the verified existing playlist. A preview does not authorize account changes.

## Track module

| Order | Track / artist | Album or source release | Version / rating | Verified song ID / availability | Role in sequence |
| --- | --- | --- | --- | --- | --- |

Use an unrated or unknown label when song-level explicit status is not established; do not infer it from an album badge. Include the storefront with a verified Apple Music song ID, and link the selected song when available. Add duration only when known. Distinguish studio/live/remaster/cover recordings and the release chosen. Deduplicate by reliable recording identity, not title alone; supplied IDs are not necessarily verified service IDs.

## CSV for Music Transfer

When the listener uses [Music Transfer](https://pages.shreyassane.com/music-transfer), check its live CSV format guide and deliver a UTF-8 comma-separated `.csv` file with one header row. Use these columns in this order:

```csv
position,title_canonical,artist_display_canonical,apple_music_song_id,album,duration_ms,isrc,explicit_flag
```

The first four columns are required. Give every row a unique whole-number `position` in intended playlist order, and use the selected song and artist for the two canonical text columns. `apple_music_song_id` must be the verified catalog song ID for the chosen storefront and version; leave it blank when unresolved. Populate `album`, `duration_ms`, `isrc` and `explicit_flag` only when verified, leaving unknown values empty. Use `true` or `false` for a verified song-level explicit flag; an unrated song is blank. Follow normal CSV quoting for commas, quotes and line breaks in text fields. Do not add Markdown, notes or a totals row to the CSV. List blank-ID rows separately for import review.

The app adds only to a selected Apple Music destination, skips recordings already present and does not reorder existing tracks. Keep `position` for the intended sequence, but do not promise that it will rearrange a populated destination. A CSV file is an import input, not evidence of an account playlist.

## Alternatives and account action

Explain consequential exclusions and substitutions, unresolved availability and unverified transitions. If action is authorized, describe the exact intended change and reconcile uncertain submissions before retrying. Report a playlist URL only after successful service confirmation. Unknown durations do not support an exact total runtime.

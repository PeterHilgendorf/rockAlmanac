# Rock Almanac — data

The dataset. One YAML file per entity, each a list of records conforming
to the definitions in [../schema/](../schema/). Validate with:

```
python3 scripts/validate.py
```

| File | Entity |
|---|---|
| sources.yaml | source |
| people.yaml | person |
| artists.yaml | artist |
| memberships.yaml | membership |
| albums.yaml | album |
| tracks.yaml | track |
| events.yaml | event (hand-entered only — generated types are rejected) |
| tours.yaml | tour |
| venues.yaml | venue |
| relationships.yaml | relationship |

## Status: verified against tertiary sources (2026-07-21)

Every record has been checked against its cited Wikipedia page, with
release dates, IDs, and birth/death dates cross-checked against
MusicBrainz and Discogs (`musicbrainz_id` / `discogs_id` fields carry
the pointers). Where sources disagree — Nicks' departure year, the
Mystery to Me release date — the disagreement is recorded in `notes`
rather than silently resolved, per CONVENTIONS.md.

Known limits:

- All sources are tertiary. Upgrading key facts to primary/secondary
  sources (band memoirs, liner notes, Billboard archives) is the next
  research step.
- Setlist.fm was consulted but is not yet cited: its full 1977 tour
  history sits behind pagination, and bulk access needs an API key.
- Tour leg-level detail for the Rumours Tour is still to be entered.

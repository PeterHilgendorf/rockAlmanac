# Rock Almanac — data

The dataset. One YAML file per entity, each a list of records conforming
to the definitions in [../schema/](../schema/). Validate with:

```
python3 scripts/validate.py
```

Then generate the derived events and the timeline:

```
python3 scripts/build_events.py
```

This reads `albums.yaml` and `tours.yaml` and writes
[../build/](../build/): the `ALBUM_RELEASE` / `TOUR_START` / `TOUR_END`
events (which must never be hand-entered) plus a merged, chronological
`timeline.md`. Run `validate.py` before `build_events.py`.

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
- Setlist.fm (via its API) cross-confirms the Rumours Tour date range
  to the day; its 117 documented shows vs. Wikipedia's 96-show count
  is recorded as a disagreement on the tour record.
- Tour leg-level detail for the Rumours Tour is still to be entered.

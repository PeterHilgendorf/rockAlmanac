# Rock Almanac — build

**Generated output. Do not edit by hand.** Everything here is produced
by `scripts/build_events.py` from the records in [../data/](../data/).
To change it, edit the album or tour records and re-run the script.

| File | What it is |
|---|---|
| events.generated.yaml | `ALBUM_RELEASE` / `TOUR_START` / `TOUR_END` events, derived from album and tour records. These are forbidden in hand-entered `data/events.yaml`. |
| timeline.md | Hand-entered events merged with the generated ones, sorted by date — the reference timeline. |

These files are committed so the result is visible without running the
build, but they are outputs: if they ever disagree with `data/`, `data/`
wins and the fix is to re-run the script.

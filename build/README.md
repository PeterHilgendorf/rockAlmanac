# Rock Almanac — build

**Generated output. Do not edit by hand.** Produced by
`scripts/build_events.py` from the records in [../data/](../data/), one
folder per collection (see [../data/collections.yaml](../data/collections.yaml)).

```
build/
  fleetwood-mac/
  the-runaways/
    events.generated.yaml   ALBUM_RELEASE / TOUR_START / TOUR_END, derived
    timeline.md             hand-entered + generated events, sorted
    timeline.json           the same, plus era colours — feeds the reel
```

To rebuild:

```
python3 scripts/build_events.py                # every collection
python3 scripts/build_events.py the-runaways   # just one
```

`ALBUM_RELEASE` / `TOUR_START` / `TOUR_END` events are forbidden in
hand-entered `data/events.yaml` and generated here instead, so a fact
lives in one place. If these files ever disagree with `data/`, `data/`
wins and the fix is to re-run the script.

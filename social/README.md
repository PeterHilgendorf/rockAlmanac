# Rock Almanac — social

Shareable visuals built from the dataset. Same canonical timeline, new medium.

## The reel

`_reel.template.html` is a data-driven 9:16 "reel" template. For each
collection, `scripts/build_reel.py` fills it from
`build/<collection>/timeline.json` and writes `<collection>-timeline.html`:

```
python3 scripts/build_events.py      # produces build/<id>/timeline.json
python3 scripts/build_reel.py        # fills the template per collection
```

| File | What it is |
|---|---|
| _reel.template.html | The reel, with placeholders for data, eras, title. Not viewed directly. |
| fleetwood-mac-timeline.html | Generated — Fleetwood Mac, 1967–2022. |
| the-runaways-timeline.html | Generated — The Runaways, 1975–1979 and after. |

Each reel works as **one system driving two channels**:

- **TikTok / Reels** — press play; cards auto-advance with an entrance
  animation and a slow vinyl-sheen. Screen-record the 9:16 card.
- **Instagram carousel** — step through with the arrows (or tap a tick on
  the scrubber) and screenshot each card. Clean frame, no UI chrome.

The **All / ★ Majors** toggle is the `significance` field at work. Each
collection's four eras (from `data/collections.yaml`) tint the card,
while the gold-foil accent and Didone typography stay constant across
bands — so Fleetwood Mac reads muted and elegiac while The Runaways runs
crimson-to-magenta-to-gold.

## Design notes

- **Committed dark, single-theme on purpose** — a record sleeve doesn't
  flip to light mode.
- **Type**: a Didone display face (Didot / Bodoni, bundled on the iOS
  devices where this gets posted) against Futura geometric small-caps.
- **Self-contained**: all CSS/JS inline, grain texture as a data URI —
  nothing is fetched, so it renders anywhere.

# Rock Almanac — social

Shareable visuals built from the dataset. Same canonical timeline, new medium.

| File | What it is |
|---|---|
| fleetwood-mac-timeline.html | A 9:16 vertical "reel" of the whole 1967–2022 story — one card per event, era-themed, sourced. |

## The reel

A single self-contained page (no external assets) that reads the events
generated into [../build/timeline.json](../build/timeline.json). It works
as **one system driving two channels**:

- **TikTok / Reels** — press play; cards auto-advance with an entrance
  animation and a slow vinyl-sheen. Screen-record the 9:16 card.
- **Instagram carousel** — step through with the arrows (or tap a tick on
  the scrubber) and screenshot each card. Clean frame, no UI chrome.

The **All / ★ Majors** toggle is the `significance` field at work: All is
the full 50-event deep-scroll; Majors is a tight 21-beat cut. The four
eras (Blues, Transition, Rumours, Legacy) each tint the card while the
gold-foil accent and Didone typography stay constant.

To refresh the data behind it, re-run `python3 scripts/build_events.py`
(which rewrites `build/timeline.json`) and re-paste the `events` array
into the `DATA` constant in the HTML.

## Design notes

- **Committed dark, single-theme on purpose** — a record sleeve doesn't
  flip to light mode.
- **Type**: a Didone display face (Didot / Bodoni, bundled on the iOS
  devices where this gets posted) against Futura geometric small-caps.
- **Self-contained**: all CSS/JS inline, grain texture as a data URI —
  nothing is fetched, so it renders anywhere.

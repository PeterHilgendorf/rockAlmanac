#!/usr/bin/env python3
"""Rock Almanac event generator.

Some events are facts already stored on another record: an album's
release date lives on the album; a tour's start and end live on the
tour. Hand-entering ALBUM_RELEASE / TOUR_START / TOUR_END events would
restate those facts and let them drift. So the schema forbids entering
them by hand (validate.py rejects them in data/events.yaml) and this
script generates them instead — the "events reference, they don't
restate" rule made mechanical.

Reads data/albums.yaml and data/tours.yaml; writes:

  build/events.generated.yaml   the generated events (never hand-edit)
  build/timeline.md             hand-entered + generated events, merged
                                and sorted — the first generated timeline

Each generated event derives its date and precision from the source
record, links back to it by id, and carries that record's source_ids,
so "everything is sourced" stays true. Significance is derived from
chart performance rather than guessed:
  album:  peak #1 -> major, top 40 -> notable, otherwise minor
  tour:   inherits its supporting album's significance (default notable)

Re-running is idempotent: identical inputs produce byte-identical
output.
"""

import datetime
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BUILD_DIR = ROOT / "build"

PRECISIONS = ["year", "month", "day"]
MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
SIG_MARK = {"major": "★", "notable": "•", "minor": "·"}


def load(name):
    doc = yaml.safe_load((DATA_DIR / name).read_text())
    return doc if doc else []


def as_date(value):
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(value)


def iso(value):
    return as_date(value).isoformat()


# ---------------------------------------------------------------- significance

def album_significance(album):
    peak = album.get("peak_position")
    if peak == 1:
        return "major"
    if isinstance(peak, int) and not isinstance(peak, bool) and peak <= 40:
        return "notable"
    return "minor"


# ---------------------------------------------------------------- generation

def generate(albums, tours, artists):
    names = {a["id"]: a["name"] for a in artists}
    albums_by_id = {a["id"]: a for a in albums}
    events = []

    for al in sorted(albums, key=lambda a: iso(a["release_date"])):
        artist = names.get(al["artist_id"], al["artist_id"])
        events.append({
            "id": "album-release-%s" % al["id"],
            "event_type": "ALBUM_RELEASE",
            "date": iso(al["release_date"]),
            "date_precision": al["release_precision"],
            "artist_ids": [al["artist_id"]],
            "album_id": al["id"],
            "headline": "%s release %s" % (artist, al["title"]),
            "significance": album_significance(al),
            "source_ids": list(al.get("source_ids", [])),
        })

    for t in sorted(tours, key=lambda t: t.get("start_date") and iso(t["start_date"]) or ""):
        artist = names.get(t["artist_id"], t["artist_id"])
        supporting = albums_by_id.get(t.get("supporting_album_id"))
        sig = album_significance(supporting) if supporting else "notable"
        if t.get("start_date"):
            events.append({
                "id": "tour-start-%s" % t["id"],
                "event_type": "TOUR_START",
                "date": iso(t["start_date"]),
                "date_precision": t["start_precision"],
                "artist_ids": [t["artist_id"]],
                "tour_id": t["id"],
                "headline": "%s begin the %s" % (artist, t["name"]),
                "significance": sig,
                "source_ids": list(t.get("source_ids", [])),
            })
        if t.get("end_date"):
            events.append({
                "id": "tour-end-%s" % t["id"],
                "event_type": "TOUR_END",
                "date": iso(t["end_date"]),
                "date_precision": t["end_precision"],
                "artist_ids": [t["artist_id"]],
                "tour_id": t["id"],
                "headline": "The %s comes to an end" % t["name"],
                "significance": sig,
                "source_ids": list(t.get("source_ids", [])),
            })

    return events


# ---------------------------------------------------------------- output

def sort_key(ev):
    # by date, then coarse-precision first, then a stable type/id order
    return (iso(ev["date"]), PRECISIONS.index(ev["date_precision"]),
            ev["event_type"], ev["id"])


def format_date(value, precision):
    d = as_date(value)
    if precision == "year":
        return str(d.year)
    if precision == "month":
        return "%s %d" % (MONTHS[d.month], d.year)
    return "%d %s %d" % (d.day, MONTHS[d.month], d.year)


def write_generated(events):
    header = (
        "# Rock Almanac — GENERATED events. DO NOT EDIT.\n"
        "# Produced by scripts/build_events.py from data/albums.yaml and\n"
        "# data/tours.yaml. Edit those records, then re-run the script.\n"
        "# ALBUM_RELEASE / TOUR_START / TOUR_END are derived here on purpose:\n"
        "# their dates live on the album and tour records, not restated by hand.\n\n"
    )
    body = yaml.safe_dump(events, sort_keys=False, allow_unicode=True, default_flow_style=False)
    (BUILD_DIR / "events.generated.yaml").write_text(header + body)


def write_timeline(hand_events, generated):
    combined = sorted(hand_events + generated, key=sort_key)
    lines = [
        "# Fleetwood Mac — Timeline",
        "",
        "*Generated by `scripts/build_events.py`. Hand-entered events from "
        "`data/events.yaml` merged with events generated from album and tour "
        "records, sorted by date.*",
        "",
        "Significance: ★ major · • notable · · minor",
        "",
    ]
    current_year = None
    for ev in combined:
        year = as_date(ev["date"]).year
        if year != current_year:
            current_year = year
            lines.append("")
            lines.append("## %d" % year)
            lines.append("")
        mark = SIG_MARK.get(ev["significance"], " ")
        when = format_date(ev["date"], ev["date_precision"])
        gen = " _(generated)_" if ev["event_type"] in (
            "ALBUM_RELEASE", "TOUR_START", "TOUR_END") else ""
        lines.append("- %s **%s** — %s%s" % (mark, when, ev["headline"], gen))
    lines.append("")
    (BUILD_DIR / "timeline.md").write_text("\n".join(lines))


def main():
    BUILD_DIR.mkdir(exist_ok=True)
    albums = load("albums.yaml")
    tours = load("tours.yaml")
    artists = load("artists.yaml")
    hand_events = load("events.yaml")

    generated = generate(albums, tours, artists)
    write_generated(generated)
    write_timeline(hand_events, generated)

    n_album = sum(1 for e in generated if e["event_type"] == "ALBUM_RELEASE")
    n_tstart = sum(1 for e in generated if e["event_type"] == "TOUR_START")
    n_tend = sum(1 for e in generated if e["event_type"] == "TOUR_END")
    print("Generated %d events: %d ALBUM_RELEASE, %d TOUR_START, %d TOUR_END"
          % (len(generated), n_album, n_tstart, n_tend))
    print("Timeline: %d events total (%d hand-entered + %d generated)"
          % (len(hand_events) + len(generated), len(hand_events), len(generated)))
    print("Wrote build/events.generated.yaml and build/timeline.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

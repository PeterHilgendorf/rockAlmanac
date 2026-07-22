#!/usr/bin/env python3
"""Rock Almanac event generator — per collection.

A collection (data/collections.yaml) is one band's story. For each one
this script:

  - generates the events whose facts already live elsewhere —
    ALBUM_RELEASE (one per album), TOUR_START, TOUR_END — from the album
    and tour records of the collection's artists. These are forbidden in
    hand-entered data (validate.py rejects them) and derived here, so the
    "events reference, they don't restate" rule stays mechanical.
  - gathers the hand-entered events that belong to the collection: any
    event referencing one of its artists, or one of its people (members,
    plus the managers/producers listed in `also_people` — this is how a
    member's later solo milestones and deaths make the timeline).
  - assigns each event an era from the collection's era bands.
  - writes, under build/<collection>/:
      events.generated.yaml   the generated events (never hand-edit)
      timeline.md             hand + generated events, merged and sorted
      timeline.json           the same, plus era colours — feeds the reel

Significance is computed, not guessed: an album inherits it from its
chart peak (#1 major, top 40 notable, otherwise minor); a tour inherits
its supporting album's. Re-running is idempotent.

Usage:
  python3 scripts/build_events.py                 # all collections
  python3 scripts/build_events.py the-runaways    # one collection
"""

import datetime
import json
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
GENERATED_TYPES = ("ALBUM_RELEASE", "TOUR_START", "TOUR_END")

# Same-date ordering: on one date, beginnings come before endings, so a
# tour starts before the band is mobbed on it and before a member leaves
# it. Falls back to this before the alphabetical event_type tiebreak.
EVENT_ORDER = {
    "FORMATION": 0, "NAME_CHANGE": 1, "REUNION": 1,
    "MEMBER_JOIN": 2, "MEMBER_RETURN": 2,
    "LABEL_CHANGE": 3, "RECORDING_SESSION": 3,
    "TOUR_START": 4, "ALBUM_RELEASE": 5, "SINGLE_RELEASE": 5,
    "CONCERT": 6, "CHART_MILESTONE": 6, "AWARD": 6, "TV_APPEARANCE": 6,
    "PRESS_MILESTONE": 6, "FILM": 6, "SIDE_PROJECT": 6, "MARRIAGE": 6,
    "INCIDENT": 6, "ARREST": 6, "PERSONAL_EVENT": 6,
    "HIATUS_START": 7, "TOUR_END": 7, "DIVORCE": 7,
    "MEMBER_EXIT": 8, "BREAKUP": 9, "DEATH": 9,
}


def load(name):
    doc = yaml.safe_load((DATA_DIR / name).read_text())
    return doc if doc else []


def as_date(value):
    return value if isinstance(value, datetime.date) else datetime.date.fromisoformat(value)


def iso(value):
    return as_date(value).isoformat()


def era_for(year, eras):
    for e in eras:
        if e["from"] <= year <= e["to"]:
            return e
    return eras[-1]


def album_significance(album):
    peak = album.get("peak_position")
    if peak == 1:
        return "major"
    if isinstance(peak, int) and not isinstance(peak, bool) and peak <= 40:
        return "notable"
    return "minor"


# ---------------------------------------------------------------- generation

def generate(albums, tours, names, albums_by_id):
    """Generated events for one collection's albums and tours."""
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
                "id": "tour-start-%s" % t["id"], "event_type": "TOUR_START",
                "date": iso(t["start_date"]), "date_precision": t["start_precision"],
                "artist_ids": [t["artist_id"]], "tour_id": t["id"],
                "headline": "%s begin the %s" % (artist, t["name"]),
                "significance": sig, "source_ids": list(t.get("source_ids", [])),
            })
        if t.get("end_date"):
            events.append({
                "id": "tour-end-%s" % t["id"], "event_type": "TOUR_END",
                "date": iso(t["end_date"]), "date_precision": t["end_precision"],
                "artist_ids": [t["artist_id"]], "tour_id": t["id"],
                "headline": "The %s comes to an end" % t["name"],
                "significance": sig, "source_ids": list(t.get("source_ids", [])),
            })
    return events


# ---------------------------------------------------------------- output

def sort_key(ev):
    return (iso(ev["date"]), PRECISIONS.index(ev["date_precision"]),
            EVENT_ORDER.get(ev["event_type"], 6), ev["event_type"], ev["id"])


def format_date(value, precision):
    d = as_date(value)
    if precision == "year":
        return str(d.year)
    if precision == "month":
        return "%s %d" % (MONTHS[d.month], d.year)
    return "%d %s %d" % (d.day, MONTHS[d.month], d.year)


def write_generated(out_dir, events):
    header = (
        "# Rock Almanac — GENERATED events. DO NOT EDIT.\n"
        "# Produced by scripts/build_events.py from album and tour records.\n\n")
    body = yaml.safe_dump(events, sort_keys=False, allow_unicode=True,
                          default_flow_style=False)
    (out_dir / "events.generated.yaml").write_text(header + body)


def write_timeline_md(out_dir, coll, events):
    lines = [
        "# %s — Timeline" % coll["title"], "",
        "*Generated by `scripts/build_events.py`. Hand-entered events merged "
        "with events generated from album and tour records, sorted by date.*",
        "", "Significance: ★ major · • notable · · minor", "",
    ]
    year = None
    for ev in events:
        y = as_date(ev["date"]).year
        if y != year:
            year = y
            lines += ["", "## %d" % y, ""]
        gen = " _(generated)_" if ev["event_type"] in GENERATED_TYPES else ""
        lines.append("- %s **%s** — %s%s" % (
            SIG_MARK.get(ev["significance"], " "),
            format_date(ev["date"], ev["date_precision"]), ev["headline"], gen))
    (out_dir / "timeline.md").write_text("\n".join(lines) + "\n")


def write_timeline_json(out_dir, coll, events):
    rows = []
    for ev in events:
        d = as_date(ev["date"])
        era = era_for(d.year, coll["eras"])
        rows.append({
            "id": ev["id"], "date": d.isoformat(), "year": d.year,
            "when": format_date(ev["date"], ev["date_precision"]),
            "event_type": ev["event_type"], "headline": ev["headline"],
            "significance": ev["significance"],
            "generated": ev["event_type"] in GENERATED_TYPES,
            "era": era["slug"], "era_label": era["label"],
        })
    payload = {
        "collection": coll["id"], "title": coll["title"],
        "subtitle": coll.get("subtitle", ""),
        "generated_at": datetime.date.today().isoformat(),
        "eras": coll["eras"], "events": rows,
    }
    (out_dir / "timeline.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- build

def build_collection(coll, data):
    artist_ids = set(coll["artist_ids"])
    persons = set(coll.get("also_people", []))
    for m in data["membership"]:
        if m.get("artist_id") in artist_ids:
            persons.add(m.get("person_id"))

    names = {a["id"]: a["name"] for a in data["artist"]}
    albums = [a for a in data["album"] if a.get("artist_id") in artist_ids]
    tours = [t for t in data["tour"] if t.get("artist_id") in artist_ids]
    albums_by_id = {a["id"]: a for a in albums}

    generated = generate(albums, tours, names, albums_by_id)

    def belongs(ev):
        return (set(ev.get("artist_ids", [])) & artist_ids
                or set(ev.get("person_ids", [])) & persons)

    hand = [e for e in data["event"] if belongs(e)]
    combined = sorted(hand + generated, key=sort_key)

    out_dir = BUILD_DIR / coll["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    write_generated(out_dir, generated)
    write_timeline_md(out_dir, coll, combined)
    write_timeline_json(out_dir, coll, combined)

    ng = len(generated)
    print("  %-16s %2d events  (%d hand + %d generated)  -> build/%s/"
          % (coll["id"], len(combined), len(combined) - ng, ng, coll["id"]))


def main():
    collections = load("collections.yaml")
    data = {e: load(f) for e, f in {
        "artist": "artists.yaml", "album": "albums.yaml", "tour": "tours.yaml",
        "event": "events.yaml", "membership": "memberships.yaml",
    }.items()}

    wanted = sys.argv[1:] or [c["id"] for c in collections]
    by_id = {c["id"]: c for c in collections}
    BUILD_DIR.mkdir(exist_ok=True)
    for cid in wanted:
        if cid not in by_id:
            sys.exit("Unknown collection: %s (have: %s)"
                     % (cid, ", ".join(by_id)))
        build_collection(by_id[cid], data)
    return 0


if __name__ == "__main__":
    sys.exit(main())

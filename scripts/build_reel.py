#!/usr/bin/env python3
"""Fill the reel template with a collection's data.

Reads social/_reel.template.html and, for each collection, injects that
collection's timeline (build/<id>/timeline.json), era colours, album
titles (for italicising in headlines), and title/subtitle, then writes
social/<id>-timeline.html — the 9:16 reel that plays for TikTok/Reels
and screenshots as an Instagram carousel.

Run build_events.py first (it produces the timeline.json files).

Usage:
  python3 scripts/build_reel.py                 # every built collection
  python3 scripts/build_reel.py the-runaways    # one collection
"""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "social" / "_reel.template.html"
BUILD = ROOT / "build"
DATA = ROOT / "data"
SOCIAL = ROOT / "social"


def entities(s):
    """Make a plain string safe to drop into HTML without a charset."""
    return "".join(c if ord(c) < 127 else "&#%d;" % ord(c) for c in s)


def album_titles(collection_id):
    colls = {c["id"]: c for c in yaml.safe_load((DATA / "collections.yaml").read_text())}
    coll = colls[collection_id]
    artist_ids = set(coll["artist_ids"])
    titles = []
    for a in yaml.safe_load((DATA / "albums.yaml").read_text()):
        if a.get("artist_id") in artist_ids and a["title"] != coll["title"]:
            titles.append(a["title"])
    return sorted(set(titles), key=len, reverse=True)  # longest first for regex


def build(collection_id, template):
    tj = json.loads((BUILD / collection_id / "timeline.json").read_text())
    eras = {e["slug"]: {"label": e["label"], "accent": e["accent"], "ground": e["ground"]}
            for e in tj["eras"]}
    data = [{"y": ev["year"], "w": ev["when"], "h": ev["headline"],
             "s": ev["significance"], "t": ev["event_type"], "e": ev["era"]}
            for ev in tj["events"]]

    html = template
    html = html.replace("__ERAS__", json.dumps(eras, ensure_ascii=True))
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=True, separators=(",", ":")))
    html = html.replace("__ALBUMS__", json.dumps(album_titles(collection_id), ensure_ascii=True))
    html = html.replace("__TITLE__", entities(tj["title"]))
    html = html.replace("__SUBTITLE__", entities(tj["subtitle"]))

    out = SOCIAL / ("%s-timeline.html" % collection_id)
    out.write_text(html, encoding="utf-8")
    print("  %-16s %2d events -> social/%s-timeline.html"
          % (collection_id, len(data), collection_id))


def main():
    template = TEMPLATE.read_text(encoding="utf-8")
    built = [p.name for p in sorted(BUILD.iterdir())
             if (p / "timeline.json").exists()]
    wanted = sys.argv[1:] or built
    for cid in wanted:
        if cid not in built:
            sys.exit("No build/%s/timeline.json — run build_events.py first" % cid)
        build(cid, template)
    return 0


if __name__ == "__main__":
    sys.exit(main())

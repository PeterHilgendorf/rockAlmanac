#!/usr/bin/env python3
"""Fetch album cover thumbnails from the Cover Art Archive.

Keyed to the MusicBrainz release-group IDs already stored on each album,
this downloads a small front-cover image per album into assets/covers/,
downscaled for embedding into the reels. Re-runnable; skips albums that
have no art. Needs curl and sips (macOS).

Usage: python3 scripts/fetch_covers.py [collection-id]
"""

import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
COVERS = ROOT / "assets" / "covers"
UA = "rockAlmanac/0.1 (peter@lakeandpine.io)"
SIZE = 160   # px, long edge


def wanted_artist_ids(collection_id):
    colls = yaml.safe_load((DATA / "collections.yaml").read_text())
    for c in colls:
        if c["id"] == collection_id:
            return set(c["artist_ids"])
    sys.exit("Unknown collection: %s" % collection_id)


def main():
    COVERS.mkdir(parents=True, exist_ok=True)
    albums = yaml.safe_load((DATA / "albums.yaml").read_text())
    if len(sys.argv) > 1:
        keep = wanted_artist_ids(sys.argv[1])
        albums = [a for a in albums if a.get("artist_id") in keep]

    got, missing = [], []
    for a in albums:
        aid, mbid = a["id"], a.get("musicbrainz_id")
        if not mbid:
            missing.append(aid + " (no mbid)")
            continue
        url = "https://coverartarchive.org/release-group/%s/front-250" % mbid
        tmp = "/tmp/cover-%s.img" % aid
        r = subprocess.run(
            ["curl", "-sL", "-A", UA, "-o", tmp, "-w", "%{http_code}", url],
            capture_output=True, text=True)
        code = r.stdout.strip()
        ok = code == "200" and Path(tmp).exists() and Path(tmp).stat().st_size > 1000
        if ok:
            out = COVERS / ("%s.jpg" % aid)
            subprocess.run(
                ["sips", "-Z", str(SIZE), "-s", "format", "jpeg", tmp, "--out", str(out)],
                capture_output=True)
            got.append(aid)
            print("  ok    %s" % aid)
        else:
            missing.append("%s (%s)" % (aid, code))
            print("  none  %s (%s)" % (aid, code))
        Path(tmp).unlink(missing_ok=True)
        time.sleep(1.0)

    print("\n%d covers fetched, %d without art." % (len(got), len(missing)))
    if missing:
        print("Missing:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Turn a raw narration script into an ElevenLabs-ready text file.

One command replaces the manual prep: it strips the non-spoken
production header, unwraps hard-wrapped paragraphs into single lines
(so ElevenLabs Studio chunks them cleanly), and inserts <break> pauses
for the slow, sleepy cadence — 3 seconds after the opening paragraph,
1.5 seconds after each one thereafter. Any <break> tags you place by
hand in the source are preserved and never doubled.

It also prints the spoken word count and an estimated runtime, so you
can see at a glance whether a draft lands in the target window (for the
sleep tracks: over thirty minutes, under an hour).

Usage:
  python3 scripts/prep_narration.py audio/<name>.md
  python3 scripts/prep_narration.py audio/<name>.md --out some/where.txt

Writes <name>.elevenlabs.txt next to the source unless --out is given.
Everything above a line containing "SCRIPT BEGINS" is treated as notes
and dropped; if there is no such line, the whole file is spoken text.
"""

import argparse
import re
import sys
from pathlib import Path


def strip_breaks(text):
    return re.sub(r"<break[^>]*>", " ", text)


def prep(raw):
    if "SCRIPT BEGINS" in raw:
        raw = raw.split("SCRIPT BEGINS", 1)[1].split("\n", 1)[1]
    blocks = [re.sub(r"\s+", " ", b).strip()
              for b in re.split(r"\n\s*\n", raw) if b.strip()]

    out = []
    para_index = 0
    for b in blocks:
        out.append(b)
        # a block that is only break tag(s) rides through untouched
        if re.fullmatch(r"(?:<break[^>]*>\s*)+", b):
            continue
        # don't double a break the author already placed at the end
        if re.search(r"<break[^>]*>\s*$", b):
            para_index += 1
            continue
        out.append('<break time="%s" />' % ("3.0s" if para_index == 0 else "1.5s"))
        para_index += 1

    return "\n\n".join(out) + "\n"


def report(text):
    words = len(strip_breaks(text).split())
    chars = len(text)
    breaks = text.count("<break")
    print("Spoken words : %d" % words)
    print("Break pauses : %d" % breaks)
    print("Characters   : %d   (~%d ElevenLabs credits)" % (chars, chars))
    print("Est. runtime  (slower-than-average narration):")
    for wpm in (90, 110, 130):
        m = words / wpm
        print("   %3d wpm : %d min %02d sec" % (wpm, int(m), int((m % 1) * 60)))
    lo, hi = words / 130, words / 90
    flag = "" if (lo >= 30 and hi <= 60) else "   <-- outside 30-60 min at some paces"
    print("   window   : %.0f-%.0f min%s" % (lo, hi, flag))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="raw narration .md")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = Path(args.script)
    if not src.exists():
        sys.exit("No such file: %s" % src)
    out = Path(args.out) if args.out else src.with_suffix(".elevenlabs.txt")

    text = prep(src.read_text(encoding="utf-8"))
    out.write_text(text, encoding="utf-8")

    print("Wrote %s" % out)
    report(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

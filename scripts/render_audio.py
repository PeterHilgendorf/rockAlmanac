#!/usr/bin/env python3
"""Render the ElevenLabs-ready sleep script to a single MP3 via the API.

Reads the API key from .secrets/elevenlabs.key (untracked) and the
prepped narration from audio/fleetwood-mac-sleep-history.elevenlabs.txt,
splits it into request-sized chunks at paragraph boundaries (keeping the
<break> tags intact), sends each to the text-to-speech endpoint with the
sleep-tuned voice settings, and concatenates the returned audio into one
MP3. Adjacent chunks are given previous_text / next_text so prosody stays
continuous across the seams.

Usage:
  python3 scripts/render_audio.py --list-voices              # account voices
  python3 scripts/render_audio.py audio/<name>.elevenlabs.txt --dry-run
  python3 scripts/render_audio.py audio/<name>.elevenlabs.txt --test
  python3 scripts/render_audio.py audio/<name>.elevenlabs.txt   # full -> MP3
  python3 scripts/render_audio.py audio/<name>.elevenlabs.txt --voice <id>

The script path is optional and defaults to the Fleetwood Mac story.
The MP3 is written next to the script unless --out is given.
Only stdlib is used. Nothing here prints the API key.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY_FILE = ROOT / ".secrets" / "elevenlabs.key"
DEFAULT_SCRIPT = ROOT / "audio" / "fleetwood-mac-sleep-history.elevenlabs.txt"

API = "https://api.elevenlabs.io/v1"

# "George" — deep, warm, British; a good boring-history-at-bedtime voice.
DEFAULT_VOICE = "JBFqnCBsd6RMkjVDRZzb"
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
VOICE_SETTINGS = {
    "stability": 0.80,        # high = even, monotone
    "similarity_boost": 0.75,
    "style": 0.0,             # flat, unexaggerated
    "use_speaker_boost": True,
    "speed": 0.80,            # slower than average
}
MAX_CHARS = 2500              # well under the per-request limit
PAUSE_BETWEEN_CALLS = 0.5     # be gentle with rate limits


def load_key():
    if not KEY_FILE.exists():
        sys.exit("No API key at %s" % KEY_FILE)
    key = KEY_FILE.read_text().strip()
    if not key:
        sys.exit("API key file is empty")
    return key


def api_request(url, key, data=None, method="GET"):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("xi-api-key", key)
    req.add_header("accept", "application/json")
    if body is not None:
        req.add_header("content-type", "application/json")
    return urllib.request.urlopen(req)


def list_voices(key):
    with api_request(API + "/voices", key) as r:
        voices = json.load(r).get("voices", [])
    print("%-26s  %s" % ("VOICE ID", "NAME"))
    for v in voices:
        print("%-26s  %s" % (v.get("voice_id"), v.get("name")))
    print("\n%d voices. Pass one with --voice <id>." % len(voices))


def strip_breaks(text):
    return re.sub(r"<break[^>]*>", " ", text).strip()


def chunk_paragraphs(text, max_chars=MAX_CHARS):
    """Group blank-line-separated blocks into chunks under max_chars.
    Break-tag blocks are tiny and ride along with the preceding text."""
    blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    chunks, cur = [], ""
    for b in blocks:
        candidate = (cur + "\n\n" + b) if cur else b
        if len(candidate) > max_chars and cur:
            chunks.append(cur)
            cur = b
        else:
            cur = candidate
    if cur:
        chunks.append(cur)
    return chunks


def tts(key, text, voice, prev_text, next_text):
    url = "%s/text-to-speech/%s?output_format=%s" % (API, voice, OUTPUT_FORMAT)
    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS,
    }
    if prev_text:
        payload["previous_text"] = prev_text[-500:]
    if next_text:
        payload["next_text"] = next_text[:500]
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST")
    req.add_header("xi-api-key", key)
    req.add_header("content-type", "application/json")
    req.add_header("accept", "audio/mpeg")
    with urllib.request.urlopen(req) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?", default=str(DEFAULT_SCRIPT),
                    help="ElevenLabs-ready .txt (default: Fleetwood Mac)")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="chunk + cost only")
    ap.add_argument("--test", action="store_true", help="render only the first chunk")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    key = load_key()

    if args.list_voices:
        list_voices(key)
        return 0

    script_path = Path(args.script)
    if not script_path.exists():
        sys.exit("No such script: %s" % script_path)
    text = script_path.read_text(encoding="utf-8")
    chunks = chunk_paragraphs(text)
    total_chars = sum(len(c) for c in chunks)

    print("Script : %s" % script_path.name)
    print("Chunks : %d  (max %d chars each)" % (len(chunks), MAX_CHARS))
    print("Credits: ~%d characters" % total_chars)
    print("Voice  : %s   Model: %s   Speed: %s   Stability: %s"
          % (args.voice, MODEL_ID, VOICE_SETTINGS["speed"], VOICE_SETTINGS["stability"]))

    if args.dry_run:
        for i, c in enumerate(chunks, 1):
            print("  chunk %2d: %4d chars  | %s..." % (i, len(c), strip_breaks(c)[:60]))
        return 0

    out = Path(args.out) if args.out else script_path.with_suffix(".mp3")
    render = chunks[:1] if args.test else chunks
    if args.test:
        out = out.with_suffix(".test.mp3")
        print("\nTEST MODE — rendering chunk 1 only -> %s\n" % out.name)

    audio = bytearray()
    for i, c in enumerate(render):
        prev_text = strip_breaks(chunks[i - 1]) if i > 0 else ""
        next_text = strip_breaks(chunks[i + 1]) if i + 1 < len(chunks) else ""
        try:
            data = tts(key, c, args.voice, prev_text, next_text)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            sys.exit("\nHTTP %s on chunk %d:\n%s" % (e.code, i + 1, detail))
        audio.extend(data)
        print("  chunk %2d/%d  ok  (%d KB)" % (i + 1, len(render), len(data) // 1024))
        if i + 1 < len(render):
            time.sleep(PAUSE_BETWEEN_CALLS)

    out.write_bytes(audio)
    mb = len(audio) / (1024 * 1024)
    print("\nWrote %s  (%.1f MB)" % (out, mb))
    if args.test:
        print("Listen, then run without --test for the full render.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

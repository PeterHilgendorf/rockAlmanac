# Rendering the sleep track on ElevenLabs

Everything you need to turn [fleetwood-mac-sleep-history.md](fleetwood-mac-sleep-history.md)
into a finished audio file. The paste-ready version, with pauses already
inserted, is **[fleetwood-mac-sleep-history.elevenlabs.txt](fleetwood-mac-sleep-history.elevenlabs.txt)**.

## The short version

1. Open **Studio** on elevenlabs.io (the long-form tool — not the quick
   "Text to Speech" box).
2. Create a new project and paste in the `.elevenlabs.txt` file.
3. Model: **Eleven Multilingual v2**. Voice: a low, calm, mature
   narrator (see below).
4. Set the voice settings for a flat, slow, sleepy read (see below).
5. Generate one paragraph first as a test; fix any mispronounced names.
6. Generate the whole project and export as MP3.

Budget: the script is **~24,200 characters**, so it costs about **24,200
credits** — roughly a quarter of a Creator-plan month, leaving plenty for
re-tests. Confirm your plan grants **commercial rights** if you'll post
it publicly.

## Why this file, not the raw script

- The non-spoken production header is **removed** — the file starts on
  the first spoken word.
- Each paragraph is unwrapped to a single line, so Studio chunks it
  cleanly.
- A **`<break time="1.5s" />`** sits after every paragraph (3 seconds
  after the opening, and longer gaps between the closing "good nights")
  to enforce the slow, spacious, sleepy cadence. ElevenLabs honors
  `<break>` on Multilingual v2; it ignores most other SSML.
- Numbers are already spelled out as words, so the voice won't race
  through dates or misread them.

If any single paragraph ever sounds glitchy, it's almost always too many
breaks in one chunk — but at one break per paragraph you're well within
the safe range.

## Voice

Browse the Voice Library for something **deep, warm, unhurried, and
mature** — filter for "narration," "calm," or "meditation." For this
British-history-at-bedtime tone, the built-in voices **George** (warm
British) or **Daniel** (deep British) are strong, stable choices; **Brian**
is a good deep American option. Avoid bright, young, or energetic voices —
they fight the genre.

Use **Eleven Multilingual v2**, not the v3 (alpha) model. v3 is more
expressive and less predictable, which is the opposite of what a monotone
sleep read wants.

## Settings for a slow, monotone read

In the voice settings panel:

| Setting | Value | Why |
|---|---|---|
| **Speed** | ~0.80 | Slower than normal. Don't go below ~0.75 or it can slur. |
| **Stability** | ~0.80 (high) | Even, consistent, unemotional — the monotone you want. |
| **Similarity** | ~0.75 | Keeps the voice steady across 40 minutes. |
| **Style** | 0 | No expressive exaggeration. Flat is the goal here. |
| **Speaker Boost** | On | A touch more clarity; optional. |

These combine with the built-in `<break>` pauses to give the drawn-out,
low-energy cadence the genre lives on.

## Pronunciation

ElevenLabs is good with most of these, but a few proper nouns are worth
checking on your test render. Fixes use the **alias** method (plain
phonetic respelling) in Studio's **Pronunciations** panel — aliases work
on Multilingual v2, whereas IPA/phoneme entries do not.

A starter dictionary for the three likeliest misreads is in
[pronunciations.pls](pronunciations.pls):

| Name | Say it like | In the dictionary? |
|---|---|---|
| McVie | "Mick-VEE" | yes |
| Hartlepool | "HART-luh-pool" | yes |
| Sausalito | "saw-suh-LEE-toe" | yes |
| Kirwan | "KUR-wun" | listen first, add if wrong |
| Caillat | (Ken Caillat — **confirm** the family's own pronunciation before setting) | no — verify |
| Dashut | (Richard Dashut — **confirm** before setting) | no — verify |

Test a render of the Rumours paragraph (it contains Sausalito, Caillat,
and Dashut) and the early-life paragraphs (Hartlepool, McVie) before
committing to the full generation.

## Export

Export as **MP3**; 192 kbps is more than enough for spoken word. Higher
tiers offer WAV/PCM if you want a lossless master to edit. Many sleep
tracks then add a very quiet ambient bed (rain, low drone) underneath in
a separate editor — optional, and done outside ElevenLabs.

## Prefer to automate it?

`scripts/render_audio.py` sends any `.elevenlabs.txt` to the ElevenLabs
API with the settings above and writes the MP3 in one command. It reads
the key from `.secrets/elevenlabs.key`.

```
python3 scripts/render_audio.py --list-voices                  # pick a voice
python3 scripts/render_audio.py audio/<name>.elevenlabs.txt --dry-run
python3 scripts/render_audio.py audio/<name>.elevenlabs.txt --test   # 1 chunk
python3 scripts/render_audio.py audio/<name>.elevenlabs.txt          # full MP3
```

It splits the script into request-sized chunks at paragraph boundaries,
keeps prosody continuous across the seams (`previous_text`/`next_text`),
and stitches the audio into one file. Change the voice with `--voice <id>`;
the sleep-tuned settings (Multilingual v2, speed 0.8, high stability,
style 0) live at the top of the script.

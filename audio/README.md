# Rock Almanac — audio

Narration scripts drawn from the dataset, for spoken-word audio, plus
the tooling to turn them into finished MP3s.

## Making the next story

The pipeline is repeatable. To produce a new "boring history for sleep"
episode about a different artist:

1. **Copy the template** to a new file:
   `cp audio/TEMPLATE.sleep-story.md audio/<artist>-sleep-history.md`
2. **Write the narration**, replacing the bracketed prompts. Follow the
   genre rules in the template (even, unhurried, numbers spelled out,
   sensitive moments kept gentle). Draw facts from the dataset in
   `../data/` where possible; run `python3 scripts/validate.py` if you
   add records there.
3. **Prep it for ElevenLabs** — strips the header, unwraps paragraphs,
   inserts `<break>` pauses, and reports the runtime:
   `python3 scripts/prep_narration.py audio/<artist>-sleep-history.md`
   Aim for the **thirty-to-sixty-minute window** (~4,000–4,600 words).
4. **Render the audio**, either way:
   - In ElevenLabs Studio by hand — see [ELEVENLABS.md](ELEVENLABS.md).
   - Or one command: `python3 scripts/render_audio.py audio/<artist>-sleep-history.elevenlabs.txt`
     (dry-run and single-chunk `--test` modes available; needs the API
     key in `../.secrets/elevenlabs.key`).

## Files

| File | What it is |
|---|---|
| TEMPLATE.sleep-story.md | Copy-to-start skeleton: genre rules + the structural beats that worked. |
| ELEVENLABS.md | Playbook for rendering on ElevenLabs: voice, settings, pronunciation, export. |
| pronunciations.pls | ElevenLabs pronunciation dictionary (alias method) — extend per artist. |
| fleetwood-mac-sleep-history.md | The first episode: Fleetwood Mac, 1967–2022. The master script. |
| fleetwood-mac-sleep-history.elevenlabs.txt | The Fleetwood Mac script, prepped for ElevenLabs. |

Rendered `*.mp3` files are git-ignored — they are large and regenerable.

## The genre, briefly

An unhurried, even, monotone read — slower than average, about ninety to
one hundred and twenty words per minute. The dullness is the feature: it
is what lets a listener fall asleep. Numbers are spelled out as words so
the voice stays slow and never misreads a date, and every script opens
with a short production note above a `SCRIPT BEGINS` marker — the voice
reads only what is below it.

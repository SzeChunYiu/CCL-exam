# Source audio: generation and hosting

Vercel serves the application; Supabase Storage serves the audio. Each CCL source
segment is an individual public MP3.

- Supabase project: `ccl-exam` (`dmoputkgxuaeoypmdfhm`, EU North / Stockholm)
- Public bucket: `ccl-audio`
- Object path: `<prefix>/<dialogue-id>/S<segment>.mp3`, e.g. `v4/D001/S01.mp3`
- The browser reads the base URL from `data/audio_remote.json`. **That file is
  the single source of truth for which version is live** — do not restate the
  voices or rates anywhere else, including in this document.

## Calibration

Delivery pace is calibrated against the six official NAATI CCL practice
recordings, not chosen by taste. Those recordings were silence-segmented, each
speech block aligned to its PDF transcript, and per-segment speed measured:

| | reference median | measured spread |
|---|---|---|
| English | **168.0 words/min** | n=42, p25 147.5, p75 189.9 |
| Cantonese | **4.07 Han chars/sec** | n=38, p25 3.75, p75 4.24 |

Measured over 70 randomly sampled v3 objects, the previous bank delivered
166.67 wpm English (within 1% — fine) and 3.30 Han/sec Cantonese (19% slow).
v4 therefore re-times Cantonese and leaves English alone.

Rates are **per voice**, because the voices differ enormously at the same
nominal rate. Live values live in `VOICE_RATES` in `scripts/generate_v4_audio.py`
and are echoed into `data/audio_remote.json` at upload time.

## Voices

Both genders on both sides, assigned per dialogue, as the official materials do —
each reference dialogue declares the gender of the English speaker and of the
LOTE speaker independently. The two axes advance at different periods so all four
pairings occur across the bank.

v3 used exactly two voices for all 1,412 segments (every professional the same
man, every client the same woman). That uniformity was itself a realism defect.

`zh-HK-HiuGaaiNeural` was dropped from the pool on a native listener's judgement.
It is also the slowest zh-HK voice by a wide margin.

## Text shaping

The synthesiser receives a shaped copy of each segment; the learner-facing text
in `data/dialogues.json` is never modified. Currently that means promoting a
mid-sentence comma to a full stop when both halves can stand alone, which buys a
real pause (measured ≈1.15s versus ≈0.31s for a comma).

Two engine facts worth knowing before editing the pipeline:

- **SSML is not supported.** Tags are read aloud as words — feeding
  `<break time="800ms"/>` makes the listener hear the markup. Pausing can only be
  controlled with punctuation.
- **Some Cantonese glyphs are silently dropped.** 嚹 囖 嗻 啝 𠺝 𠿪 𡃉 唩 㖑 produce
  no audio at all. `scripts/qa_cantonese.py` fails any script containing them.

## Publishing

    source ~/.ccl_supabase_env                  # SUPABASE_URL + service-role key
    python3 scripts/generate_v4_audio.py        # -> build/audio-v4/
    python3 scripts/upload_v4_segments.py       # -> bucket, then rewrites config

`generate_v4_audio.py` is resumable (it skips existing files) and **fails loudly**
if measured delivery drifts more than 5% from the reference — a silent pacing
regression is the exact defect v4 exists to remove.

`upload_v4_segments.py` publishes to a **new prefix** and only rewrites
`data/audio_remote.json` after verifying objects over the public URL. Two reasons
this matters: the switch is atomic for learners, and the public CDN caches
objects, so overwriting a live path would serve stale audio for an unknown
period. Rollback is reverting one config file; the previous base URL is preserved
in it as `previousBaseUrl`.

`scripts/upload_audio_to_supabase.py` is the **legacy v1 bundle uploader**. It
pushes four monolithic `.bin` files and overwrites `data/audio_remote.json` with a
bundle-shaped config that has no `mode` field. Running it against the current site
breaks the segment player. It is kept only for historical recovery.

## Fallback order in the player

1. Supabase per-segment MP3
2. checked-in legacy bundled MP3
3. an eligible Australian-English or Hong Kong Cantonese device voice

A missing object silently degrades to device speech, which sounds markedly worse.
That is why the generator retries on failure rather than skipping a segment.

## Provenance

This is synthetic neural practice material, not official NAATI audio and not
human voice acting. The dialogues are original; the pacing and register targets
are derived from measurements of the official practice recordings.

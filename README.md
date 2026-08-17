# CCL Exam Lab — English ⇄ Cantonese

A Vercel-ready English–Cantonese CCL-style training workspace built from **100 original Australian community-interpreting dialogues**.

## Six-part training system

1. **Dashboard** — progress, entry points and audio status.
2. **Mock Exam** — 50 two-dialogue mocks, 20-minute practice clock, hidden scripts, calibrated 1.0× MP3 audio, repeat tracking, optional recording and end-only review. Every mock pairs two different topic areas.
3. **Topic Practice + Quick Drill** — choose topic/difficulty/direction, reveal-and-compare, error tagging and adjustable training speed.
4. **Performance & History** — browser-side attempt summaries, weak segments, repeat usage, common error tags and topic exposure.
5. **100-dialogue Library** — search/filter by topic, difficulty, completion and favourites.
6. **Study & Vocabulary** — 198 Australian English ⇄ Cantonese terms, study guide, number/note-taking drills, self-review, references and audio-calibration notes.

## Final content build

The site, answer key and audio are generated from one deterministic source pipeline:

```bash
python3 scripts/build_all_content.py
python3 scripts/build_audio_bundles.py
```

Current generated bank:

- **100 dialogues**
- **1,394 alternating source segments**
- **50 cross-topic mock exams**
- **12 topic areas**
- **12–16 segments per dialogue**
- **267–327 English-equivalent words per dialogue**
- **35-word maximum source segment**

## Audio calibration

The independent synthetic MP3 source audio at **1.0×** is calibrated against the average speaking pace measured from NAATI's downloadable Cantonese practice materials. On the complete generated bank the current build measures about **160.16 English words/minute** and **180.13 Cantonese English-equivalent words/minute**, against reference targets of roughly **160 / 179**.

Mock mode locks playback to 1.0×. Training modes allow 0.9×, 1.0× and 1.08×. Browser speech synthesis remains an emergency fallback only and its exact pace depends on the device/voice.

No NAATI audio is redistributed. See `materials/AUDIO_CALIBRATION.md`.

## Generated audio design

Each dialogue is encoded as MP3 and stored inside one of four compact binary bundles. `data/audio_manifest.json` stores byte ranges and per-segment timing windows, so the site can play one source segment plus its chime without shipping 1,394 separate files.

The GitHub Action rebuilds content, validates the bank, compiles the Cantonese eSpeak dictionary, generates the MP3 bundles and commits deterministic generated assets.

## Local development

```bash
python3 -m pip install mistune
python3 scripts/build_all_content.py
python3 -m http.server 8000
```

For audio generation, install eSpeak/ffmpeg and compile the Cantonese pronunciation dictionary as shown in the workflow.

## Important

This repository contains independent study material, not official, copied, live or leaked NAATI test content. Practice ratings in the app are self-assessment metrics, not official NAATI marks. Australian procedures and CCL rules can change; use the official references in `materials/OFFICIAL_REFERENCE_NOTES.md` for current information.

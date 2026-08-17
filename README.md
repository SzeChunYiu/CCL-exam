# CCL Exam — English ⇄ Cantonese Practice Pack

A 100-dialogue NAATI CCL-style English–Cantonese practice collection focused on Australian community interpreting contexts.

## What is included

- **100 original practice dialogues** / **1,200 alternating interpretation segments**
- **50 mock-test pairings** (two dialogues per mock)
- Coverage of the 12 broad CCL topic areas: business, consumer affairs, employment, health, immigration & settlement, legal, community, education, financial, housing, insurance, and social services
- Australian terminology and scenarios (for example ABN, GST, BAS, Fair Work, Medicare, PBS, myGov, Centrelink, VEVO, HECS-HELP, NDIS, AFCA and state tenancy processes)
- Source scripts, model interpretations, glossary, note-taking drills, self-review sheet and study guide
- Reproducible Australian-English + Cantonese synthetic MP3 generation with a two-tone interpretation chime after every segment

## Start here

1. Read [`practice_pack/README_FIRST.md`](practice_pack/README_FIRST.md).
2. Use [`practice_pack/MOCK_TEST_PAIRINGS.md`](practice_pack/MOCK_TEST_PAIRINGS.md) to choose a mock test.
3. Practise blind from generated audio; only review [`practice_pack/SOURCE_SCRIPTS.md`](practice_pack/SOURCE_SCRIPTS.md) and [`practice_pack/MODEL_ANSWERS.md`](practice_pack/MODEL_ANSWERS.md) afterwards.
4. Record errors with [`practice_pack/SELF_REVIEW_SHEET.md`](practice_pack/SELF_REVIEW_SHEET.md).

## Generate the audio

The repository intentionally does **not** version the generated MP3 binaries. They are reproducible from `practice_pack/dialogues_metadata.json`.

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y espeak ffmpeg python3-pip
python3 -m pip install numpy
cd resources/espeak-cantonese
sudo espeak --compile=zhy
cd ../..
python3 scripts/generate_audio.py
```

This creates `practice_pack/audio/*.mp3` and a ZIP under `dist/`.

GitHub Actions also contains an audio-build workflow. A successful run publishes the generated MP3 set as a downloadable workflow artifact.

## About the voices

The recordings are **synthetic practice audio**, not official NAATI recordings or leaked examination content. English uses Australian eSpeak voices. Cantonese uses the eSpeak `zh-yue` voice with the included Cantonese dictionary source.

The dictionary source includes its upstream attribution and is distributed under the licensing terms stated in its header (CC BY-SA 3.0).

## Important exam/reference note

This is independently created study material. Exam rules and government-service procedures change. Check the official sources listed in [`practice_pack/OFFICIAL_REFERENCE_NOTES.md`](practice_pack/OFFICIAL_REFERENCE_NOTES.md) before relying on any procedural detail.

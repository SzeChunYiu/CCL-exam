# CCL Exam Lab — English ⇄ Cantonese

A Vercel-ready English–Cantonese CCL-style training workspace built from **100 original Australian community-interpreting dialogues**.

## Six-part training system

1. **Dashboard** — progress, entry points and audio status.
2. **Mock Exam** — 50 two-dialogue mocks, 20-minute practice clock, hidden scripts, 1.0× neural source audio, repeat tracking, optional recording and end-only review.
3. **Topic Practice + Quick Drill** — choose topic/difficulty/direction, reveal-and-compare, error tagging and adjustable training speed.
4. **Performance & History** — browser-side attempt summaries, weak segments, repeat usage, common error tags and topic exposure.
5. **100-dialogue Library** — search/filter by topic, difficulty, completion and favourites.
6. **Study & Vocabulary** — 198 Australian English ⇄ Cantonese terms, question-design analysis, study guide, number/note-taking drills, self-review, references and audio-calibration notes.

## V3 dialogue bank

The final bank was rewritten and QA-checked against characteristics observed in the supplied Cantonese CCL practice samples:

- **100 dialogues**
- **1,412 alternating source segments**
- **50 cross-topic mock exams**
- **12 broad topic areas**
- **12–16 segments per dialogue**
- **272–324 English-equivalent words per dialogue** (mean about 295)
- **35-word maximum source segment**
- no learner-facing “remember this term / key expression” language inside exam dialogue
- no generic appeal/review ending repeated across every topic
- no exact full turn repeated more than **four times** across the bank

See `materials/QUESTION_DESIGN_ANALYSIS.md` and `materials/QA_REPORT.md`.

## Neural audio

V3 serves **individual MP3 source segments from Supabase Storage** rather than relying on the old eSpeak dialogue bundles.

Speaker-role voices:

- Australian English provider: `en-AU-WilliamNeural`
- Australian English client: `en-AU-NatashaNeural`
- Hong Kong Cantonese provider: `zh-HK-WanLungNeural`
- Hong Kong Cantonese client: `zh-HK-HiuGaaiNeural`

The supplied practice recordings were used as a pacing benchmark. Measured reference speech was approximately **160 English words/minute** and about **4.0 Cantonese characters/second**, with natural segment-to-segment variation. V3 uses normal neural speed for Australian English and a small +5% Cantonese adjustment. A two-tone interpretation cue is generated after each source segment in the browser.

Mock mode uses 1.0×. Training modes allow 0.9×, 1.0× and 1.08×. The checked-in legacy bundles and a suitable device voice are fallbacks only.

These are **synthetic neural practice voices**, not official NAATI recordings or human actors. No supplied/NAATI audio is redistributed.

## Architecture

- **Vercel:** static exam application and study UI
- **GitHub:** versioned dialogue bank, answer keys, study resources and QA/build scripts
- **Supabase:** public `ccl-audio` object storage plus public-read dialogue/audio metadata tables; write access stays server-side
- **Browser local storage:** practice history, favourites and weak-segment flags

The public app needs no Supabase service-role key. It constructs public MP3 URLs from `data/audio_remote.json`. Generator functions are temporary deployment tooling and are locked after the audio migration is complete.

## Local development

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000`. The app can use the public Supabase neural MP3s; if those are unavailable it falls back to the legacy checked-in audio and then to a suitable browser voice.

## Important

This repository contains independent study material, not official, copied, live or leaked NAATI test content. Practice ratings in the app are self-assessment metrics, not official NAATI marks. Australian procedures and CCL rules can change; use the official references in `materials/OFFICIAL_REFERENCE_NOTES.md` for current information.

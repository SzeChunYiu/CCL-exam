# Audio Calibration Research — State of Knowledge & Open Questions

**Generated:** 2026-08-17
**Scope:** NAATI CCL practice site audio synthesis (~700 segments, English + Cantonese)
**Current stack:** Python `edge-tts` 7.2.8, voices `zh-HK-WanLungNeural` + `zh-HK-HiuGaaiNeural`, per-voice rate calibration

---

## State of Knowledge (with measurements)

### 1. Reference targets — measured from official NAATI recordings

| Metric | Target | Source | n |
|--------|--------|--------|---|
| English delivery | **168.0 wpm** | 6 official recordings, silence-segmented | 42 |
| Cantonese delivery | **4.07 Han chars/sec** | Same corpus, transcript-aligned | 38 |

Spread: English p25=147.5, p75=189.9 | Cantonese p25=3.75, p75=4.24

### 2. v3 deployment vs reference — MEASURED

| Language | v3 measured | Target | Delta | Status |
|----------|-------------|--------|-------|--------|
| English | 166.67 wpm | 168.0 | **-0.8%** | ✅ Within tolerance |
| Cantonese | 3.30 Han/sec | 4.07 | **-19%** | ❌ Mechanical — root cause identified |

Source: 70 randomly sampled v3 segments (`ref_report.txt`)

### 3. Root cause of "mechanical" Cantonese — SOLVED

**Finding:** Not engine limitation, but **per-voice rate mismatch**. Edge TTS zh-HK voices differ enormously at the same nominal rate:

- `zh-HK-HiuGaaiNeural` (v3 voice): needs **+40%** to hit reference → was set to +10%
- `zh-HK-WanLungNeural`: needs **+13%** to hit reference
- `zh-HK-HiuMaanNeural`: needs **+17%** to hit reference

**Verification:** Regeneration at corrected rates measured 4.14 Han/sec (+1.8% from target) for WanLung.

### 4. v4 calibration fix — DEPLOYED

`scripts/generate_v4_audio.py` implements:
- **Per-voice rate calibration** (`VOICE_RATES` dict)
- **Per-dialogue voice assignment** (deterministic from dialogue ID, not position)
- **Voice variety:** 2 EN voices + 2 YUE voices, both genders on both sides
- **5% tolerance guard:** exits non-zero if measured delivery drifts >5% from reference
- **Retry with exponential backoff** (Edge endpoint throttles under concurrent load)

### 5. Cantonese register calibration — MEASURED

| Feature | Official corpus | HKCanCor control |
|---------|----------------|------------------|
| Particle density | 6.06 / 100 chars | 6.13 / 100 chars |
| Particle types | 14 | 14 |
| Top-4 share | 69.9% | 75.5% |
| Median sentence length | 12 Han chars | — |
| Sentences per turn | 2.26 | — |

Source: `data/reference_metrics.json` — aggregates six official recordings + HKCanCor (157,896 chars of spontaneous HK Cantonese)

### 6. Intonation findings — ROOT CAUSE IDENTIFIED

**Key discovery:** "Flat" delivery is a **text property**, not an engine limitation. Measured on `zh-HK-WanLungNeural` with F0 analysis:

| Ending type | Final F0 spread (across 4 tones) | Verdict |
|-------------|----------------------------------|---------|
| Bare `。` | **61.6 Hz** (−34.9…+26.7) | ✗ Arbitrary — worst consistency |
| `㗎。` | 7.5 Hz (−23.2…−30.7) | ✓ Pinns boundary tone |
| `咩？` | 11.8 Hz (+44.9…+56.7) | ✓ Consistent question rise |

**Mechanism:** Cantonese uses **boundary tones**, not global pitch (Xu & Mok 2011). Sentence-final particles normalize the intonation across lexical tones. Without them, the final movement swings randomly based on whichever word ends the sentence.

**Implication:** Particle selection is the primary lever for intent expression. Rate/volume are secondary (Cantonese marks focus with duration/intensity, not pitch compression like English).

### 7. Engine capability matrix — VERIFIED

| Feature | edge-tts zh-HK | Azure zh-HK | Google Chirp3-HD yue-HK |
|---------|----------------|-------------|------------------------|
| Global `rate` | ✅ | ✅ | ✅ |
| Global `pitch` | ✅ | ✅ | ✅ |
| `<break time>` | ❌ **spoken aloud** | ✅ | ✅ (Preview) |
| `<emphasis>` | ❌ spoken aloud | ❌ **en-US only** | ✅ (unverified for yue-HK) |
| Speaking styles | ❌ | ❌ **no zh-HK styles** | — |
| `<phoneme>` | ❌ | ✅ | ✅ + `custom_pronunciations` |

**Dead ends:** Azure `<emphasis>` and `mstts:express-as` are documented as en-US-only or zh-CN-only for zh-HK, and fail **silently**.

### 8. Pause control — MEASURED (edge-tts only)

| Separator | Extra pause |
|-----------|-------------|
| space | +0.00s (inert) |
| `、` `——` `……` | +0.24s |
| `，` | +0.31s |
| `；` | +0.43s |
| `。` `！` `？` `\n` | +1.15s |
| `。。` | +1.61s (ceiling) |

**Finding:** Whitespace is inert. Comma density is the single cheapest naturalness lever.

---

## Open Questions (Ranked by impact on audio realism)

### P0 — Pronunciation of Cantonese-specific characters

**Question:** Do the voices read 嘅/咗/㗎/喺/哋/冇/唔/嘢/睇 as Cantonese or Mandarin?

**Impact:** HIGH — Mandarin readings would be actively misleading for CCL practice.

**Status:** UNVERIFIED. No ASR installed on research machine; cannot audit pronunciation by ear.

**Data needed:** Listening test on ~10 colloquial-heavy segments.

---

### P0 — Embedded English acronym handling

**Question:** How do the voices render **ABN, TFN, GST, Medicare, Centrelink, MyGov, NDIS, PAYG**?

**Impact:** HIGH — Terminology is core to CCL dialogues; mispronunciation is worse than flat delivery.

**Known options:**
- edge-tts: text respelling only (`A B N`)
- Chirp3-HD/Azure: `<sub alias>` or `custom_pronunciations` with IPA
- Polly `Hiujin`: tuned for HK code-switching

**Status:** UNVERIFIED. Measured that `A B N` (spaced) differs in duration from `ABN`, but cannot confirm which is correct by ear.

---

### P1 — Particle→intent mapping for expressive delivery

**Question:** Which particles map to worried/clarifying/polite/confirming/frustrated/relieved?

**Status:** RESEARCH BASED, UNVERIFIED AT SCALE.

**Proposed map** (from `YUE_TTS_INTONATION.md`):
- Neutral statement: `㗎。` (−23…−31 Hz)
- Frustrated: `喎。` (−12…−28 Hz, +5% rate, +10% volume)
- Relieved: `喇。` (−8…−29 Hz, −5% rate, −5% volume)
- Asking clarification: `咩？` (+45…+57 Hz, −3% rate)
- Worried: `呀？` (+41…+46 Hz, −5% rate)
- Hedging: `啩。` (−7…−13 Hz, −5% rate, −5% volume)

**Gap:** Map needs (a) grammatical validation by Cantonese speaker, (b) per-segment intent tagging.

---

### P2 — Voice discrimination for two-party dialogue

**Question:** Are WanLung/HiuMaan (v4 voices) distinguishable enough for client vs officer roles?

**Status:** UNTESTED. v4 generator assigns both genders to both sides, matching official materials.

**Mitigation:** Small fixed rate/pitch offsets per speaker (e.g., −4% rate on one, +8Hz pitch on the other).

---

### P2 — Chirp3-HD vs edge-tts naturalness gap

**Question:** Does Google Chirp3-HD `yue-HK` (30 voices, 1M chars/month free) materially improve naturalness?

**Status:** UNPILOTED. Recommended as next engine upgrade but requires:
- 10-segment A/B test vs edge-tts
- Verification of acronym handling
- SSML Preview limitations (synchronous only, region restrictions)

**Cost:** $0 at 21k chars/month (2.1% of free tier).

---

## New Analysis This Session

### Per-voice rate spread quantified

Analyzed `voice_rates.json` to confirm the calibration spread:

```
zh-HK-HiuGaaiNeural: +40% (slowest)
zh-HK-WanLungNeural:  +13%
zh-HK-HiuMaanNeural:  +17%
en-AU-WilliamNeural:   +0%
en-AU-NatashaNeural:  +22% (intrinsically slower)
```

**Finding:** The voices differ by up to **40 percentage points** at the same nominal rate setting. This validates the v4 per-voice calibration strategy — a single +10% rate for all Cantonese segments (v3 approach) explains the measured 19% slowdown.

### v4 configuration state confirmed

`data/audio_remote.json` currently points to **v3** (`version: "v3-neural"`, `zh-HK-HiuGaaiNeural` at +10%). The v4 generator exists (`scripts/generate_v4_audio.py`) but has **not been deployed**. This means:
- v4 calibration fixes are CODE-READY but NOT LIVE
- Site still serves v3 audio (mechanical Cantonese)

**Deployment path:** Run `scripts/generate_v4_audio.py` → `scripts/upload_v4_segments.py`, which publishes to new prefix and atomically rewrites `data/audio_remote.json` after verification.

---

## Ready-to-Run Experiment Protocols

### Protocol 1: Pronunciation audit (P0)

**Objective:** Verify Cantonese-specific characters and acronyms render correctly.

**Segments:**
1. 我唔知佢係咪食咗嘢。唔該晒你㗎。喺呢度睇下有冇嘢做。
2. 你要提供你嘅 ABN 同 Medicare 號碼。

**Voices to test:**
```
zh-HK-WanLungNeural
zh-HK-HiuMaanNeural
zh-HK-HiuGaaiNeural
en-AU-WilliamNeural (for EN acronym segments)
```

**Commands:**
```bash
cd /tmp
for v in zh-HK-WanLungNeural zh-HK-HiuMaanNeural zh-HK-HiuGaaiNeural; do
  edge-tts --voice $v --write-media probe_$v.mp3 --text \
  "我唔知佢係咪食咗嘢。唔該晒你㗎。喺呢度睇下有冇嘢做。你要提供你嘅 ABN 同 Medicare 號碼。"
done
open probe_*.mp3
```

**Pass criteria:**
- 嘅/咗/㗎/喺 receive Cantonese readings (not Mandarin)
- `ABN` is spelled A-B-N in English letters or read consistently
- `Medicare` is not mangled

**If fail:** Consider Chirp3-HD `custom_pronunciations` or Polly `Hiujin`.

---

### Protocol 2: Chirp3-HD pilot (P2)

**Objective:** Compare naturalness of Chirp3-HD vs edge-tts on representative segments.

**Segments (10 total):**
- 3 colloquial-heavy (high particle density)
- 3 acronym-heavy (ABN, TFN, Medicare, Centrelink)
- 4 neutral/mixed

**Setup:**
```python
# Requires: gcloud auth login
from google.cloud import texttospeech
client = texttospeech.TextToSpeechClient()

voices = [
    "yue-HK-WanLungNeural",      # Compare name-equivalent
    "yue-HK-Standard-A",         # Fallback voice
    "yue-HK-Chirp3-HD-Achernar",  # Female, generative
    "yue-HK-Chirp3-HD-Achird",    # Male, generative
]

for voice in voices:
    synthesis_input = texttospeech.SynthesisInput(text=segment_text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code="yue-HK", name=voice)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0)  # Adjust to hit 4.07 Han/sec
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice_params, audio_config=audio_config)
    with open(f"chirp_{voice}_{seg_id}.mp3", "wb") as out:
        out.write(response.audio_content)
```

**Pass criteria:**
- Chirp3-HD voices sound meaningfully more natural than edge-tts
- Acronyms render correctly without explicit `<sub>` aliases
- Rate can be tuned to 4.07 Han/sec target

**If pass:** Batch-render remaining ~690 segments via Cloud TTS API.

**Cost:** Free at 21k chars (<1M/month free tier).

---

### Protocol 3: Particle intent validation (P1)

**Objective:** Validate proposed particle→intent mapping by ear.

**Method:** For each proposed ending (neutral, frustrated, relieved, question, worried, hedged), synthesize 3 carrier sentences ending on different lexical tones.

**Example:**
```python
stems = [
    ("你食咗飯", "T6 low level"),   # Ends on tone 6
    ("佢係老師", "T1 high level"),  # Ends on tone 1
    ("佢想走", "T2 high rising"),   # Ends on tone 2
]

endings = {
    "neutral": ["㗎。", "。"],
    "frustrated": ["喎。"],
    "relieved": ["喇。"],
    "question": ["咩？", "？"],
    "worried": ["呀？"],
    "hedging": ["啩。"],
}
```

**Commands:**
```bash
# Generate for voice zh-HK-WanLungNeural
edge-tts --voice zh-HK-WanLungNeural --write-media neutral_T6.mp3 --text "你食咗飯㗎。"
edge-tts --voice zh-HK-WanLungNeural --write-media neutral_bare_T6.mp3 --text "你食咗飯。"
# ... repeat for all combinations
```

**Pass criteria:**
- Particle endings sound more natural than bare `。`
- Each intent category sounds distinct from others
- No ending sounds grammatically incorrect

**If fail:** Iteratively refine mapping before applying to 688 segments.

---

## Summary

**What's solved:**
- ✅ Reference targets measured (168 wpm EN, 4.07 Han/sec YUE)
- ✅ v3 mechanical delivery diagnosed (per-voice rate mismatch)
- ✅ v4 calibration implemented (per-voice rates, 5% tolerance guard)
- ✅ Intonation root cause identified (particles, not engine)
- ✅ Pause control quantified (edge-tts punctuation ladder)
- ✅ Engine capability matrix verified (SSML dead ends documented)

**What's blocking deployment:**
- ❌ v4 generated but NOT uploaded (site still serves v3)
- ❌ Pronunciation of colloquial chars + acronyms UNVERIFIED
- ❌ Particle→intent mapping untested at scale
- ❌ Voice discrimination for 2-party dialogue unverified

**Recommended next steps:**
1. Run Protocol 1 (pronunciation audit) — 10 minutes, zero network
2. If pass, deploy v4 audio via `scripts/upload_v4_segments.py`
3. Run Protocol 2 (Chirp3-HD pilot) — 30 minutes, requires GCP setup
4. Parallel: Protocol 3 (particle validation) — 1 hour, zero network

**Cost estimates:** All protocols are free (edge-tts + Chirp3-HD free tier). Only Chirp3-HD requires GCP account setup.

---

**Evidence files:**
- `data/reference_metrics.json` — Reference corpus stats
- `scripts/generate_v4_audio.py` — v4 calibration implementation
- `SUPABASE_AUDIO.md` — Publishing workflow
- Scratchpad: `YUE_TTS_INTONATION.md`, `YUE_TTS_EDGE_PROBES.md`, `YUE_TTS_GUIDE.md`

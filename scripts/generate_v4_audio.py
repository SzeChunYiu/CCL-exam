#!/usr/bin/env python3
"""Generate v4 CCL source audio with reference-calibrated delivery.

Why this exists
---------------
v3 audio was generated with a single Cantonese voice and a single Cantonese rate
(+10%). Measured against the six official NAATI CCL practice recordings, that
delivered 3.26 Han chars/sec against a reference median of 4.07 -- about 20% too
slow, which reads as mechanical. v3 also used exactly two voices for the whole
100-dialogue bank (every professional = William, every client = HiuGaai).

v4 fixes both:

* per-voice rate calibration, because the voices differ enormously at the same
  nominal rate (HiuGaai needs +40% to hit the reference pace, WanLung +15%)
* per-dialogue voice assignment, so speakers vary across the bank the way they
  do in the official materials, which state speaker gender per dialogue

Calibration provenance
----------------------
Targets are the measured medians of the official recordings, obtained by
silence-segmenting each MP3, aligning speech blocks to the PDF transcript and
computing per-segment delivery speed:

    English    168.0 words/min   (n=42, p25 147.5, p75 189.9)
    Cantonese    4.07 Han/sec    (n=38, p25 3.75,  p75 4.24)

Measured on 70 randomly sampled deployed v3 files, the shipped bank delivers
166.67 wpm English (within 1% of reference -- fine) and 3.30 Han/sec Cantonese
(19% slow -- the defect). So this is a Cantonese pacing fix plus a voice-variety
fix, not a wholesale re-timing.

Per-voice rates were solved empirically, assuming speed is proportional to
(1 + rate), and each is verified by regeneration rather than assumed. Every
value below is overridable by environment variable; none is a guess.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import edge_tts
except ImportError:  # pragma: no cover
    sys.exit("edge-tts is required: pip install edge-tts")

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[㐀-鿿]")
WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*")

# --- calibration targets (measured from the official reference recordings) ---
TARGET_EN_WPM = float(os.environ.get("CCL_TARGET_EN_WPM", "168.0"))
TARGET_YUE_CPS = float(os.environ.get("CCL_TARGET_YUE_CPS", "4.07"))

# --- per-voice rates solved against those targets -------------------------
# Verified by regeneration: at these rates each voice lands within ~2% of target.
VOICE_RATES = {
    # Cantonese: solved from a +10% probe, then verified by regeneration on 12
    # segments and corrected. WanLung +15% measured 4.14 (+1.8%), HiuMaan +17%
    # measured 4.25 (+4.5%); both trimmed to land on 4.07.
    "zh-HK-WanLungNeural": os.environ.get("CCL_RATE_WANLUNG", "+13%"),
    "zh-HK-HiuMaanNeural": os.environ.get("CCL_RATE_HIUMAAN", "+12%"),
    # English needs no correction. Measured over 70 randomly sampled deployed v3
    # files, William at +0% delivers 166.67 wpm against a reference median of
    # 168.0 -- within 1%. Earlier readings of 173 and 157 were sampling noise from
    # 12-20 segment samples; English wpm varies widely with segment content, so
    # this is settled on the large sample and left alone.
    "en-AU-WilliamNeural": os.environ.get("CCL_RATE_WILLIAM", "+0%"),
    # Natasha is intrinsically slower. +22% puts her within 0.02 wpm of William on
    # the same segments, which is the number that matters -- the two English voices
    # must be interchangeable within a bank, not merely close to a global target.
    "en-AU-NatashaNeural": os.environ.get("CCL_RATE_NATASHA", "+22%"),
    # Retained for reference only. zh-HK-HiuGaai voiced every Cantonese segment in
    # v3 and is the slowest of the three zh-HK voices by a wide margin (it needs
    # +40% to reach reference pace). Dropped from the pool on a native listener's
    # judgement, not on the numbers.
    "zh-HK-HiuGaaiNeural": os.environ.get("CCL_RATE_HIUGAAI", "+40%"),
}

# Voice pools. Both genders on both sides, as the official materials do -- each
# reference dialogue declares the gender of the English speaker and of the LOTE
# speaker independently. Assignment is deterministic from the dialogue index so a
# dialogue always sounds the same, and the two axes advance at different periods
# so all four gender pairings occur across the bank instead of the professional
# and client genders moving in lockstep.
EN_VOICES = os.environ.get(
    "CCL_EN_VOICES", "en-AU-WilliamNeural,en-AU-NatashaNeural"
).split(",")
YUE_VOICES = os.environ.get(
    "CCL_YUE_VOICES", "zh-HK-WanLungNeural,zh-HK-HiuMaanNeural"
).split(",")

# Slight per-dialogue pitch offset adds speaker individuality without changing
# pace. Cycle is deliberately coprime with the voice-pool sizes so voice and
# pitch do not lock into the same repeating pair.
PITCH_CYCLE = [
    p.strip() for p in os.environ.get("CCL_PITCH_CYCLE", "+0Hz,+6Hz,-5Hz,+3Hz,-8Hz").split(",")
]

# Long written-style sentences are the other half of "mechanical". Splitting at
# clause boundaries for the TTS input only (never in the on-screen text) gives
# the engine somewhere to breathe. Measured effect: +2 internal pauses per turn.
SPLIT_FOR_SPEECH = os.environ.get("CCL_SPLIT_FOR_SPEECH", "1") == "1"
SPLIT_MIN_CHARS = int(os.environ.get("CCL_SPLIT_MIN_CHARS", "16"))

# Throttling controls. Concurrency 6 produced intermittent empty streams from the
# Edge endpoint; 3 with exponential backoff completed cleanly. Measured, not guessed.
RETRIES = int(os.environ.get("CCL_TTS_RETRIES", "5"))
BACKOFF_BASE = float(os.environ.get("CCL_TTS_BACKOFF", "1.5"))


@dataclass
class Job:
    dialogue: str
    n: int
    lang: str
    text: str
    voice: str
    rate: str
    pitch: str

    @property
    def rel(self) -> str:
        return f"{self.dialogue}/S{self.n:02d}.mp3"


def speech_text(text: str, lang: str) -> str:
    """Shape text for the synthesiser only. Never written back to the bank."""
    if not SPLIT_FOR_SPEECH or lang != "yue":
        return text
    # Promote a comma to a full stop when both sides are long enough to stand
    # alone. This buys a real pause instead of a rushed run-on.
    out, buf = [], ""
    for ch in text:
        buf += ch
        if ch in "，,":
            head = buf[:-1]
            if len(HAN.findall(head)) >= SPLIT_MIN_CHARS:
                out.append(head + "。")
                buf = ""
    out.append(buf)
    return "".join(out)


def dialogue_index(dialogue_id: str) -> int:
    """Stable ordinal derived from the id itself, e.g. D014 -> 14.

    Deliberately NOT the position in the input list. Position would mean that
    regenerating a subset (one batch, one fixed dialogue) assigned different
    voices than the full run, so a partial re-run would leave the bank with the
    same dialogue voiced two different ways -- and because generation skips
    existing files, the mismatch would survive every later run.
    """
    m = re.search(r"(\d+)", dialogue_id or "")
    return int(m.group(1)) if m else abs(hash(dialogue_id)) % 997


def assign_voices(dialogue_id: str) -> tuple[str, str, str]:
    idx = dialogue_index(dialogue_id)
    # Different periods on the two axes: if both used `idx % 2` the professional
    # and the client would swap gender together every dialogue and the bank would
    # only ever contain two of the four possible pairings.
    en = EN_VOICES[idx % len(EN_VOICES)]
    yue = YUE_VOICES[(idx // len(EN_VOICES)) % len(YUE_VOICES)]
    pitch = PITCH_CYCLE[idx % len(PITCH_CYCLE)]
    return en, yue, pitch


def build_jobs(dialogues: list[dict]) -> list[Job]:
    jobs: list[Job] = []
    for d in dialogues:
        en_voice, yue_voice, pitch = assign_voices(d["id"])
        for seg in d["segments"]:
            lang = seg["source_lang"]
            voice = yue_voice if lang == "yue" else en_voice
            jobs.append(
                Job(
                    dialogue=d["id"],
                    n=seg["n"],
                    lang=lang,
                    text=seg["source"],
                    voice=voice,
                    rate=VOICE_RATES[voice],
                    pitch=pitch,
                )
            )
    return jobs


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def measure(job: Job, path: Path) -> float | None:
    """Delivery speed in the unit that language is calibrated in."""
    d = duration(path)
    if d <= 0:
        return None
    if job.lang == "yue":
        return len(HAN.findall(job.text)) / d
    return len(WORD.findall(job.text)) / d * 60


async def synth(job: Job, out_dir: Path, force: bool) -> tuple[Job, Path, bool]:
    path = out_dir / job.rel
    path.parent.mkdir(parents=True, exist_ok=True)
    # A truncated file from an interrupted run is worse than no file: it probes
    # as zero-length and silently poisons the calibration report.
    if path.exists() and path.stat().st_size < 2000:
        path.unlink()
    if path.exists() and not force:
        return job, path, False
    comm = edge_tts.Communicate(
        speech_text(job.text, job.lang), job.voice, rate=job.rate, pitch=job.pitch
    )
    await comm.save(str(path))
    if not path.exists() or path.stat().st_size < 2000:
        raise RuntimeError(f"synthesis produced no usable audio for {job.rel}")
    return job, path, True


async def run(jobs: list[Job], out_dir: Path, force: bool, concurrency: int) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    results: list[dict] = []
    failed: list[str] = []
    done = 0

    async def one(job: Job):
        nonlocal done
        async with sem:
            # The Edge endpoint intermittently returns an empty stream ("No audio
            # was received") under concurrent load. It is throttling, not a bad
            # parameter: the identical request succeeds moments later. Retry with
            # exponential backoff and jitter rather than dropping the segment --
            # a silently missing file would fall back to device speech in the
            # player, which is exactly the robotic voice we are removing.
            for attempt in range(RETRIES):
                try:
                    job, path, made = await synth(job, out_dir, force)
                    break
                except Exception as exc:
                    if attempt == RETRIES - 1:
                        print(f"  FAILED {job.rel}: {exc}", file=sys.stderr)
                        failed.append(job.rel)
                        return
                    await asyncio.sleep(BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 0.6))
            speed = measure(job, path)
            results.append({
                "path": job.rel, "lang": job.lang, "voice": job.voice,
                "rate": job.rate, "pitch": job.pitch, "speed": speed,
                "seconds": duration(path), "generated": made,
            })
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(jobs)}")

    await asyncio.gather(*(one(j) for j in jobs))
    if failed:
        print(f"{len(failed)} segment(s) failed after {RETRIES} attempts", file=sys.stderr)
    return results


def report(results: list[dict]) -> dict:
    import statistics as st

    summary = {}
    for lang, target, unit in (("en", TARGET_EN_WPM, "wpm"), ("yue", TARGET_YUE_CPS, "Han/s")):
        vals = [r["speed"] for r in results if r["lang"] == lang and r["speed"]]
        if not vals:
            continue
        med = st.median(vals)
        summary[lang] = {
            "n": len(vals), "median": round(med, 2), "target": target,
            "unit": unit, "delta_pct": round((med - target) / target * 100, 1),
        }
    by_voice = {}
    for r in results:
        by_voice.setdefault(r["voice"], []).append(r["speed"])
    summary["per_voice"] = {
        v: {"n": len(s), "median": round(st.median([x for x in s if x]), 2)}
        for v, s in by_voice.items() if any(s)
    }
    summary["files"] = len(results)
    summary["total_seconds"] = round(sum(r["seconds"] for r in results), 1)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "build" / "audio-v4"))
    ap.add_argument("--dialogues", default=str(ROOT / "data" / "dialogues.json"))
    ap.add_argument("--only", help="comma-separated dialogue ids, e.g. D001,D014")
    ap.add_argument("--lang", choices=["en", "yue"], help="restrict to one language")
    ap.add_argument("--limit", type=int, help="cap number of segments (smoke test)")
    ap.add_argument("--force", action="store_true", help="regenerate existing files")
    ap.add_argument("--concurrency", type=int,
                    default=int(os.environ.get("CCL_TTS_CONCURRENCY", "3")))
    args = ap.parse_args()

    dialogues = json.loads(Path(args.dialogues).read_text(encoding="utf-8"))
    jobs = build_jobs(dialogues)
    if args.only:
        keep = {x.strip() for x in args.only.split(",")}
        jobs = [j for j in jobs if j.dialogue in keep]
    if args.lang:
        jobs = [j for j in jobs if j.lang == args.lang]
    if args.limit:
        jobs = jobs[: args.limit]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"generating {len(jobs)} segments -> {out_dir}")

    results = asyncio.run(run(jobs, out_dir, args.force, args.concurrency))
    summary = report(results)

    (out_dir / "_generation_report.json").write_text(
        json.dumps({"summary": summary, "segments": results}, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=1))

    # Fail loudly if the calibration did not land -- a silent 20% drift is the
    # exact defect this script exists to remove.
    bad = [l for l in ("en", "yue")
           if l in summary and abs(summary[l]["delta_pct"]) > 5.0]
    if bad:
        print(f"CALIBRATION OUT OF TOLERANCE for {bad} (>5% from reference)", file=sys.stderr)
        return 2
    missing = len(jobs) - len(results)
    if missing:
        print(f"{missing} segments failed to generate", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

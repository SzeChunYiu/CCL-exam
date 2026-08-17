#!/usr/bin/env python3
"""Quality gate for the Cantonese side of the CCL dialogue bank.

Calibrated against the six official NAATI CCL practice dialogues, not against
taste. The reference corpus (39 client turns, 1,204 Han characters) is the
control: this gate must PASS it and must FAIL the pre-rewrite bank. Both
controls are asserted by ``--self-test`` so the gate cannot silently rot into
something that approves everything.

Reference measurements driving the thresholds
---------------------------------------------
    particle density      6.23 per 100 Han chars
    particle variety      15 distinct types in 1,204 chars
    median sentence       12 Han chars
    sentences per turn    2.26
    repeated 10-grams     0.0%
    duplicate sentences   0.0%
    A-not-A               0.66 per 100 chars

Usage
-----
    python3 scripts/qa_cantonese.py --self-test
    python3 scripts/qa_cantonese.py data/dialogues.json
    python3 scripts/qa_cantonese.py build/rewrite/batch-01.json --per-dialogue
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[㐀-鿿]")

# --- rule inputs ---------------------------------------------------------
# Longest-first so 架啦 counts once as a cluster, not as 架 + 啦 + 架啦.
PARTICLES = sorted(
    {"架啦", "架咋", "㗎啦", "㗎喇", "嘅啫", "架喇", "㗎", "架", "啦", "喇", "咋",
     "啫", "囉", "呀", "嘞", "添", "喔", "咩", "呢", "吖", "嘛", "喎", "啩", "嘅"},
    key=len, reverse=True,
)
PARTICLE_RE = re.compile("|".join(map(re.escape, PARTICLES)))

# Written-Chinese function words that should not survive in a spoken turn.
WRITTEN_CHINESE = ["的", "是", "不", "沒有", "在", "他", "她", "我們", "你們", "他們",
                   "這", "那", "什麼", "怎麼", "很", "也", "還", "吧"]
# Compounds in which the same character is ordinary spoken Cantonese and must not
# be counted. Without these, the gate flags 的確 / 不過 / 其他 in the official
# corpus -- a false positive that would have condemned authentic material.
NOT_WRITTEN = {
    "的": ["的確", "目的", "的士"],
    "不": ["不過", "不如", "不便", "不同", "不特止", "不錯", "不失為", "不嬲"],
    "他": ["其他", "他日"],
    "是": ["但是", "於是", "就是", "是但", "總是"],
    "在": ["實在", "現在", "存在", "在座"],
    "也": ["也許"],
    "還": ["還原", "還神"],
    "那": ["那陣"],
}
# Written connectives that have spoken equivalents. These are NOT banned: both
# authentic corpora contain them at low rates (然後 0.018/100字 in HKCanCor,
# 0.083 in the NAATI corpus), so the gate caps their rate rather than zeroing it.
WRITTEN_CONNECTIVES = ["然後", "但是", "而且", "因此", "接著", "並且", "由於", "所以說"]
# Literary vocabulary observed in the templated bank, absent from the reference.
LITERARY = ["憂心", "申報", "狀況", "確保", "實體", "予以", "加以", "方可", "應當", "事宜"]
# Glyphs the TTS engine silently drops (measured on zh-HK voices, edge-tts 7.2.8).
DROPPED_GLYPHS = ["嚹", "囖", "嗻", "啝", "𠺝", "𠿪", "𡃉", "唩", "㖑", "𡀔", "𠻹", "𡁜"]
# Calques from the English source text.
CALQUES = ["更新", "呢個詞", "我嘅情況", "對我嘅情況", "下一步", "我唔肯定", "細節",
           "確認", "處理好"]
# Particles that read as challenging or sneering when a client addresses an
# official. Not banned outright -- 喎 is fine when reporting a third party --
# so these are reported as warnings with counts, not hard failures.
RISKY_TO_OFFICIAL = ["咩", "喎", "咯"]

A_NOT_A = re.compile(r"使唔使|可唔可以|會唔會|有冇|係唔係|得唔得|好唔好|喺唔喺|明唔明|收唔收|要唔要")

# Spoken connectives. Density measured across two independent authentic corpora:
#   HKCanCor (157,896 chars, spontaneous conversation)  3.24 per 100 Han chars
#   NAATI CCL reference (1,204 chars, service register)  1.40
#   pre-rewrite bank                                     0.54
# Service register sits below casual conversation, so the floor is anchored on
# the NAATI figure rather than the conversational one.
SPOKEN_CONNECTIVES = ["即係", "但係", "咁", "其實", "因為", "跟住", "所以", "譬如",
                      "不過", "一係", "總之", "點知", "結果", "反而", "同埋", "仲有"]

THRESHOLDS = {
    "particle_per100_min": 4.5,
    "particle_variety_min": 8,
    "median_sentence_max": 14,
    "sentences_per_seg_min": 2.0,
    "boilerplate_pct_max": 8.0,
    "dup_sentence_pct_max": 5.0,
    # Rates, not bans. Ceilings sit ~2x the highest authentic-corpus rate so real
    # Cantonese passes while a document read aloud does not.
    "written_chinese_per100_max": 0.10,
    "written_connective_per100_max": 0.20,
    "literary_max": 2,
    "dropped_glyphs_max": 0,
    "calque_per100_max": 0.35,
    "connective_per100_min": 1.20,
    "connective_variety_min": 5,
    # Natural Cantonese is a few workhorse particles plus a long tail, not an even
    # spread. Measured top-4 share: NAATI 68.0%, HKCanCor 75.5%, pre-rewrite bank
    # 88.8% (only 7 types). Both directions are defects -- over-concentration is a
    # tic, and a perfectly even spread is a different kind of unnatural produced by
    # writing to satisfy a variety counter.
    "top4_share_min": 60.0,
    "top4_share_max": 82.0,
    # Ceiling as well as floor. The reference averages 2.26 sentences per turn;
    # chopping every turn into many short sentences drives the median length down
    # and the duplication rate to zero while sounding clipped. A floor alone
    # cannot catch overshoot -- the same mistake the particle-variety check would
    # have made without top4_share.
    "sentences_per_seg_max": 3.2,
}


def han_len(t: str) -> int:
    return len(HAN.findall(t))


def count_all(corpus: list[str], needles: list[str], exclude: dict | None = None) -> Counter:
    """Count needles, optionally masking compounds in which the needle is not the
    written form at all (的確 is not 的; 不過 is not 不)."""
    c = Counter()
    for t in corpus:
        for n in needles:
            s = t
            for comp in (exclude or {}).get(n, []):
                s = s.replace(comp, "")
            k = s.count(n)
            if k:
                c[n] += k
    return c


def measure(corpus: list[str]) -> dict:
    total = sum(han_len(t) for t in corpus) or 1
    parts = [m.group(0) for t in corpus for m in PARTICLE_RE.finditer(t)]
    sents = [han_len(c) for t in corpus for c in re.split(r"[。！？]", t) if han_len(c)]
    grams = Counter()
    for t in corpus:
        h = "".join(HAN.findall(t))
        for i in range(len(h) - 9):
            grams[h[i:i + 10]] += 1
    gram_total = sum(grams.values()) or 1
    sent_texts = [c for t in corpus for c in re.split(r"[。！？]", t) if han_len(c) >= 6]
    dup = sum(v for v in Counter(sent_texts).values() if v > 1)
    calq = sum(count_all(corpus, CALQUES).values())
    conn = count_all(corpus, SPOKEN_CONNECTIVES)
    return {
        "segments": len(corpus),
        "chars": total,
        "particle_per100": round(len(parts) / total * 100, 2),
        "particle_variety": len(set(parts)),
        "top4_share": round(
            sum(v for _, v in Counter(parts).most_common(4)) / max(len(parts), 1) * 100, 1),
        "median_sentence": st.median(sents) if sents else 0,
        "sentences_per_seg": round(len(sents) / max(len(corpus), 1), 2),
        "boilerplate_pct": round(sum(v for v in grams.values() if v > 1) / gram_total * 100, 1),
        "dup_sentence_pct": round(dup / max(len(sent_texts), 1) * 100, 1),
        "written_chinese_per100": round(
            sum(count_all(corpus, WRITTEN_CHINESE, NOT_WRITTEN).values()) / total * 100, 3),
        "written_connective_per100": round(
            sum(count_all(corpus, WRITTEN_CONNECTIVES).values()) / total * 100, 3),
        "literary": sum(count_all(corpus, LITERARY).values()),
        "dropped_glyphs": sum(count_all(corpus, DROPPED_GLYPHS).values()),
        "calque_per100": round(calq / total * 100, 2),
        "connective_per100": round(sum(conn.values()) / total * 100, 2),
        "connective_variety": len(conn),
        "a_not_a_per100": round(sum(len(A_NOT_A.findall(t)) for t in corpus) / total * 100, 2),
    }


def judge(m: dict) -> list[str]:
    T = THRESHOLDS
    f = []
    if m["particle_per100"] < T["particle_per100_min"]:
        f.append(f"particle density {m['particle_per100']} < {T['particle_per100_min']} (reference 6.23)")
    if m["particle_variety"] < T["particle_variety_min"]:
        f.append(f"particle variety {m['particle_variety']} < {T['particle_variety_min']} (reference 15)")
    if m["median_sentence"] > T["median_sentence_max"]:
        f.append(f"median sentence {m['median_sentence']} > {T['median_sentence_max']} Han chars (reference 12)")
    if m["sentences_per_seg"] > T["sentences_per_seg_max"]:
        f.append(f"sentences/turn {m['sentences_per_seg']} > {T['sentences_per_seg_max']} "
                 f"(reference 2.26) — turns chopped too fine")
    if m["sentences_per_seg"] < T["sentences_per_seg_min"]:
        f.append(f"sentences/turn {m['sentences_per_seg']} < {T['sentences_per_seg_min']} (reference 2.26)")
    if m["boilerplate_pct"] > T["boilerplate_pct_max"]:
        f.append(f"repeated 10-grams {m['boilerplate_pct']}% > {T['boilerplate_pct_max']}% (reference 0.0)")
    if m["dup_sentence_pct"] > T["dup_sentence_pct_max"]:
        f.append(f"duplicate sentences {m['dup_sentence_pct']}% > {T['dup_sentence_pct_max']}% (reference 0.0)")
    if m["written_chinese_per100"] > T["written_chinese_per100_max"]:
        f.append(f"written-Chinese function words {m['written_chinese_per100']}/100字 > "
                 f"{T['written_chinese_per100_max']}")
    if m["written_connective_per100"] > T["written_connective_per100_max"]:
        f.append(f"written connectives {m['written_connective_per100']}/100字 > "
                 f"{T['written_connective_per100_max']}")
    if m["literary"] > T["literary_max"]:
        f.append(f"literary vocabulary: {m['literary']}")
    if m["dropped_glyphs"] > T["dropped_glyphs_max"]:
        f.append(f"glyphs the TTS drops silently: {m['dropped_glyphs']}")
    if m["calque_per100"] > T["calque_per100_max"]:
        f.append(f"English calques {m['calque_per100']}/100字 > {T['calque_per100_max']} (reference 0.17)")
    if m["connective_per100"] < T["connective_per100_min"]:
        f.append(f"spoken connectives {m['connective_per100']}/100字 < {T['connective_per100_min']} "
                 f"(NAATI 1.40, HKCanCor 3.24)")
    if m["connective_variety"] < T["connective_variety_min"]:
        f.append(f"connective variety {m['connective_variety']} < {T['connective_variety_min']}")
    if m["top4_share"] > T["top4_share_max"]:
        f.append(f"top-4 particle share {m['top4_share']}% > {T['top4_share_max']}% "
                 f"— over-reliance on a few particles (NAATI 68.0, HKCanCor 75.5)")
    if m["top4_share"] < T["top4_share_min"]:
        f.append(f"top-4 particle share {m['top4_share']}% < {T['top4_share_min']}% "
                 f"— unnaturally even spread, likely written to satisfy the variety counter")
    return f


def cantonese_turns(dialogues: list[dict]) -> list[str]:
    """Cantonese the CLIENT speaks aloud. Register-calibrated against the corpus."""
    return [s["source"] for d in dialogues for s in d["segments"]
            if s.get("source_lang") == "yue"]


def cantonese_models(dialogues: list[dict]) -> list[str]:
    """Cantonese MODEL ANSWERS for English segments.

    Easy to forget, and it was: half the Cantonese in the bank lives here. These
    are what a learner compares their own interpretation against, so calques and
    written-Chinese matter just as much. They are NOT held to the client-turn
    particle and connective densities -- this is a professional's register
    rendered into Cantonese, and the reference corpus contains no such turns to
    calibrate against, so imposing the client floor would be inventing a target.
    """
    return [s.get("model", "") for d in dialogues for s in d["segments"]
            if s.get("source_lang") == "en" and (s.get("model") or "").strip()]


# Applied to model answers: purity rules only, no density floors.
MODEL_THRESHOLDS = {
    "written_chinese_per100_max": 0.10,
    "written_connective_per100_max": 0.20,
    "literary_max": 2,
    "dropped_glyphs_max": 0,
    "calque_per100_max": 0.35,
}


def judge_model(m: dict) -> list[str]:
    T = MODEL_THRESHOLDS
    f = []
    if m["written_chinese_per100"] > T["written_chinese_per100_max"]:
        f.append(f"model answers: written-Chinese {m['written_chinese_per100']}/100字")
    if m["written_connective_per100"] > T["written_connective_per100_max"]:
        f.append(f"model answers: written connectives {m['written_connective_per100']}/100字")
    if m["literary"] > T["literary_max"]:
        f.append(f"model answers: literary vocabulary {m['literary']}")
    if m["dropped_glyphs"] > T["dropped_glyphs_max"]:
        f.append(f"model answers: glyphs the TTS drops {m['dropped_glyphs']}")
    if m["calque_per100"] > T["calque_per100_max"]:
        f.append(f"model answers: English calques {m['calque_per100']}/100字 "
                 f"> {T['calque_per100_max']}")
    return f


def detail(corpus: list[str]) -> dict:
    return {
        "written_chinese": dict(count_all(corpus, WRITTEN_CHINESE, NOT_WRITTEN).most_common(10)),
        "written_connectives": dict(count_all(corpus, WRITTEN_CONNECTIVES)),
        "literary": dict(count_all(corpus, LITERARY)),
        "dropped_glyphs": dict(count_all(corpus, DROPPED_GLYPHS)),
        "calques": dict(count_all(corpus, CALQUES).most_common(10)),
        "risky_to_official": dict(count_all(corpus, RISKY_TO_OFFICIAL)),
        "particles": dict(Counter(
            m.group(0) for t in corpus for m in PARTICLE_RE.finditer(t)).most_common(20)),
    }


def load_reference() -> list[str] | None:
    for p in (ROOT / "data" / "reference_yue.json",
              Path("/private/tmp/claude-501/-Users-billy/12da37c4-a84a-42d3-b9e1-c103aed15723/scratchpad/ref_yue.json")):
        if p.exists():
            return [x["yue"] for x in json.loads(p.read_text(encoding="utf-8"))]
    return None


def self_test() -> int:
    """The gate is only trustworthy if both controls behave."""
    ref = load_reference()
    if ref is None:
        print("SELF-TEST INCONCLUSIVE: reference corpus not found -- cannot verify "
              "the gate. This is not a pass.", file=sys.stderr)
        return 4
    ref_fail = judge(measure(ref))
    bank = cantonese_turns(json.loads((ROOT / "data" / "dialogues.json").read_text(encoding="utf-8")))
    bank_fail = judge(measure(bank))
    ok = True
    if ref_fail:
        print(f"SELF-TEST FAIL: official reference should PASS but failed: {ref_fail}")
        ok = False
    else:
        print("self-test: official reference PASSES (control 1 ok)")
    if not bank_fail:
        print("SELF-TEST FAIL: a known-templated bank should FAIL but passed -- "
              "the gate is not discriminating.")
        ok = False
    else:
        print(f"self-test: templated control FAILS on {len(bank_fail)} rule(s) (control 2 ok)")
    return 0 if ok else 5


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=str(ROOT / "data" / "dialogues.json"))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--per-dialogue", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    dialogues = json.loads(Path(args.path).read_text(encoding="utf-8"))
    corpus = cantonese_turns(dialogues)
    if not corpus:
        print("no Cantonese turns found", file=sys.stderr)
        return 1
    m = measure(corpus)
    fails = judge(m)
    models = cantonese_models(dialogues)
    mm = measure(models) if models else None
    if mm:
        fails += judge_model(mm)

    if args.json:
        print(json.dumps({"metrics": m, "failures": fails, "detail": detail(corpus)},
                         ensure_ascii=False, indent=1))
        return 0 if not fails else 1

    print(f"== {args.path}")
    for k, v in m.items():
        print(f"   {k:22s} {v}")
    if args.per_dialogue:
        print("\n   per-dialogue failures:")
        for d in dialogues:
            turns = [s["source"] for s in d["segments"] if s.get("source_lang") == "yue"]
            if not turns:
                continue
            df = judge(measure(turns))
            if df:
                print(f"     {d['id']}: {'; '.join(df)}")
    d = detail(corpus)
    for key in ("written_chinese", "written_connectives", "dropped_glyphs", "calques", "risky_to_official"):
        if d[key]:
            print(f"\n   {key}: {d[key]}")
    print(f"\n   particles: {d['particles']}")
    if mm:
        print(f"\n   -- Cantonese MODEL ANSWERS ({mm['segments']} turns, {mm['chars']} chars) --")
        for k in ("calque_per100", "literary", "written_chinese_per100",
                  "written_connective_per100", "dropped_glyphs"):
            print(f"      {k:26s} {mm[k]}")
        md = detail(models)
        for key in ("calques", "literary", "written_chinese", "dropped_glyphs"):
            if md[key]:
                print(f"      {key}: {md[key]}")
    print("\n   VERDICT: " + ("PASS" if not fails else "FAIL"))
    for f in fails:
        print(f"     - {f}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())

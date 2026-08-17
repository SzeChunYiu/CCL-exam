#!/usr/bin/env python3
"""Independent whole-dialogue naturalness/template audit.

Existing release gates are intentionally strongest on Cantonese *client source*
turns.  This audit closes the remaining blind spots by testing three additional
surfaces separately:

* officer English source speech;
* officer Cantonese model interpretations;
* English model interpretations of Cantonese client speech.

It rejects exact substantive reuse, high masked sentence similarity, repeated
long n-grams, obvious generator grammar, and internal authoring-stage labels.
Thresholds are fixed before examining final6 results and are not relaxed by the
builder.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[㐀-鿿]")
WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)?|\d+(?:[.:,/\-]\d+)*")

EN_SENT = re.compile(r"(?<=[.!?])\s+")
Y_SENT = re.compile(r"[。！？]+")

STAGE_LABELS = re.compile(
    r"\b(?:initial enquiry|document check|deadline check|outcome review)\b",
    re.I,
)
MALFORMED_EN = [
    re.compile(r"\bthe\s+(?:a|an)\b", re.I),
    re.compile(r"\ba\s+an\b", re.I),
    re.compile(r"\ban\s+a\b", re.I),
    re.compile(r"\b(the|and|to|of|for|with|about)\s+\1\b", re.I),
]
WRITTEN_YUE = ["因此", "然而", "此外", "予以", "該項", "此項", "上述", "下列", "倘若", "務必"]

LIMITS = {
    "officer_en_near": 25,
    "officer_yue_near": 25,
    "client_en_near": 25,
    "officer_en_repeated_8gram_pct": 8.0,
    "officer_yue_repeated_10gram_pct": 8.0,
    "client_en_repeated_8gram_pct": 8.0,
    "officer_yue_written_per1000": 2.0,
}


def en_sentences(text: str):
    return [s.strip() for s in EN_SENT.split(text.strip()) if len(WORD.findall(s)) >= 8]


def y_sentences(text: str):
    return [s.strip() for s in Y_SENT.split(text.strip()) if len(HAN.findall(s)) >= 8]


def norm_en(text: str) -> str:
    x = text.lower()
    x = re.sub(r"\b\d+(?:[.:,/\-]\d+)*\b", "#", x)
    x = re.sub(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", "DAY", x)
    x = re.sub(r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b", "MONTH", x)
    x = re.sub(r"[^a-z#]+", "", x)
    return x


def norm_y(text: str) -> str:
    x = re.sub(r"[零〇一二三四五六七八九十百千萬億兩]+", "#", text)
    return "".join(c for c in x if HAN.match(c) or c == "#")


def exact_reuse(records, sentence_fn):
    seen = {}
    dup = []
    for tag, text in records:
        for s in sentence_fn(text):
            key = s.lower() if sentence_fn is en_sentences else s
            if key in seen and seen[key] != tag:
                dup.append({"a": seen[key], "b": tag, "sentence": s})
            else:
                seen[key] = tag
    return dup


def _multiset_match_upper(a_count: Counter, b_count: Counter) -> int:
    """Maximum possible number of character matches for any alignment.

    SequenceMatcher's ratio is 2*M/(len(a)+len(b)), where M is the total length
    of its non-overlapping matching blocks. M can never exceed the multiset
    intersection of the two strings. Therefore this bound can safely discard a
    pair only when even a perfect ordering of all shared characters cannot reach
    the release threshold. It changes runtime, not the logical audit result.
    """
    # Iterate over the smaller alphabet for speed.
    if len(a_count) > len(b_count):
        a_count, b_count = b_count, a_count
    return sum(min(n, b_count.get(ch, 0)) for ch, n in a_count.items())


def near_pairs(records, sentence_fn, norm_fn, threshold: float, max_examples: int = 30):
    items = []
    for tag, text in records:
        for s in sentence_fn(text):
            n = norm_fn(s)
            if len(n) >= 12:
                items.append((tag, s, n, Counter(n)))
    hits = []
    count = 0
    compared = 0
    pruned = 0
    for i in range(len(items)):
        ta, sa, a, ca = items[i]
        la = len(a)
        for j in range(i + 1, len(items)):
            tb, sb, b, cb = items[j]
            if ta == tb:
                continue
            lb = len(b)
            # Exact SequenceMatcher ratio can never exceed this simple length
            # bound, so this is also lossless.
            if (2.0 * min(la, lb) / (la + lb)) < threshold:
                pruned += 1
                continue
            max_m = _multiset_match_upper(ca, cb)
            if (2.0 * max_m / (la + lb)) < threshold:
                pruned += 1
                continue
            compared += 1
            r = SequenceMatcher(None, a, b, autojunk=False).ratio()
            if r >= threshold:
                count += 1
                if len(hits) < max_examples:
                    hits.append({"a": ta, "b": tb, "ratio": round(r, 3), "sentence_a": sa, "sentence_b": sb})
    return count, hits, {"sentences": len(items), "sequence_matcher_pairs": compared, "safely_pruned_pairs": pruned}


def repeated_word_ngram(records, n: int):
    grams = Counter()
    total = 0
    for _tag, text in records:
        toks = [t.lower() for t in WORD.findall(text)]
        for i in range(max(0, len(toks) - n + 1)):
            g = tuple(toks[i:i+n])
            grams[g] += 1
            total += 1
    repeated_occ = sum(c for c in grams.values() if c > 1)
    pct = 100.0 * repeated_occ / max(1, total)
    top = [(" ".join(g), c) for g, c in grams.most_common(30) if c > 1]
    return round(pct, 2), top


def repeated_han_ngram(records, n: int):
    grams = Counter()
    total = 0
    for _tag, text in records:
        h = "".join(HAN.findall(text))
        for i in range(max(0, len(h) - n + 1)):
            g = h[i:i+n]
            grams[g] += 1
            total += 1
    repeated_occ = sum(c for c in grams.values() if c > 1)
    pct = 100.0 * repeated_occ / max(1, total)
    top = [(g, c) for g, c in grams.most_common(30) if c > 1]
    return round(pct, 2), top


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bank", nargs="?", default=str(ROOT / "data" / "dialogues.json"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    data = json.loads(Path(args.bank).read_text(encoding="utf-8"))
    officer_en = []
    officer_yue = []
    client_en = []
    malformed = []
    stage_hits = []
    written_hits = []
    y_chars = 0

    for d in data:
        for s in d.get("segments", []):
            tag = f"{d['id']}:S{s['n']}"
            en = str(s.get("en", ""))
            yue = str(s.get("yue", ""))
            if s.get("role") == "P":
                officer_en.append((tag, en))
                officer_yue.append((tag, yue))
                y_chars += len(HAN.findall(yue))
                for w in WRITTEN_YUE:
                    if w in yue:
                        written_hits.append({"tag": tag, "word": w, "text": yue})
                if STAGE_LABELS.search(en):
                    stage_hits.append({"tag": tag, "text": en})
            else:
                client_en.append((tag, en))
            for pat in MALFORMED_EN:
                if pat.search(en):
                    malformed.append({"tag": tag, "text": en, "pattern": pat.pattern})

    exact_off_en = exact_reuse(officer_en, en_sentences)
    exact_off_y = exact_reuse(officer_yue, y_sentences)
    exact_cli_en = exact_reuse(client_en, en_sentences)

    near_off_en, ex_near_off_en, perf_off_en = near_pairs(officer_en, en_sentences, norm_en, 0.88)
    near_off_y, ex_near_off_y, perf_off_y = near_pairs(officer_yue, y_sentences, norm_y, 0.84)
    near_cli_en, ex_near_cli_en, perf_cli_en = near_pairs(client_en, en_sentences, norm_en, 0.88)

    en8, top_en8 = repeated_word_ngram(officer_en, 8)
    y10, top_y10 = repeated_han_ngram(officer_yue, 10)
    cli8, top_cli8 = repeated_word_ngram(client_en, 8)
    written_rate = round(1000 * len(written_hits) / max(1, y_chars), 3)

    failures = []
    if exact_off_en: failures.append(f"officer English exact substantive reuse: {len(exact_off_en)}")
    if exact_off_y: failures.append(f"officer Cantonese exact substantive reuse: {len(exact_off_y)}")
    if exact_cli_en: failures.append(f"client English-model exact substantive reuse: {len(exact_cli_en)}")
    if near_off_en > LIMITS["officer_en_near"]: failures.append(f"officer English near pairs {near_off_en} > {LIMITS['officer_en_near']}")
    if near_off_y > LIMITS["officer_yue_near"]: failures.append(f"officer Cantonese near pairs {near_off_y} > {LIMITS['officer_yue_near']}")
    if near_cli_en > LIMITS["client_en_near"]: failures.append(f"client English-model near pairs {near_cli_en} > {LIMITS['client_en_near']}")
    if en8 > LIMITS["officer_en_repeated_8gram_pct"]: failures.append(f"officer English repeated 8-grams {en8}% > {LIMITS['officer_en_repeated_8gram_pct']}%")
    if y10 > LIMITS["officer_yue_repeated_10gram_pct"]: failures.append(f"officer Cantonese repeated 10-grams {y10}% > {LIMITS['officer_yue_repeated_10gram_pct']}%")
    if cli8 > LIMITS["client_en_repeated_8gram_pct"]: failures.append(f"client English-model repeated 8-grams {cli8}% > {LIMITS['client_en_repeated_8gram_pct']}%")
    if written_rate > LIMITS["officer_yue_written_per1000"]: failures.append(f"officer Cantonese written-marker rate {written_rate}/1000 > {LIMITS['officer_yue_written_per1000']}")
    if malformed: failures.append(f"malformed English patterns: {len(malformed)}")
    if stage_hits: failures.append(f"internal stage labels spoken aloud: {len(stage_hits)}")

    report = {
        "dialogues": len(data),
        "officer_turns": len(officer_en),
        "client_english_model_turns": len(client_en),
        "thresholds": LIMITS,
        "metrics": {
            "officer_en_exact": len(exact_off_en),
            "officer_yue_exact": len(exact_off_y),
            "client_en_exact": len(exact_cli_en),
            "officer_en_near": near_off_en,
            "officer_yue_near": near_off_y,
            "client_en_near": near_cli_en,
            "officer_en_repeated_8gram_pct": en8,
            "officer_yue_repeated_10gram_pct": y10,
            "client_en_repeated_8gram_pct": cli8,
            "officer_yue_written_per1000": written_rate,
            "malformed_english": len(malformed),
            "stage_label_hits": len(stage_hits),
        },
        "audit_performance": {
            "officer_en": perf_off_en,
            "officer_yue": perf_off_y,
            "client_en": perf_cli_en,
        },
        "examples": {
            "officer_en_exact": exact_off_en[:20],
            "officer_yue_exact": exact_off_y[:20],
            "client_en_exact": exact_cli_en[:20],
            "officer_en_near": ex_near_off_en,
            "officer_yue_near": ex_near_off_y,
            "client_en_near": ex_near_cli_en,
            "malformed": malformed[:30],
            "stage_labels": stage_hits[:30],
            "written_yue": written_hits[:30],
            "officer_en_top_8grams": top_en8,
            "officer_yue_top_10grams": top_y10,
            "client_en_top_8grams": top_cli8,
        },
        "failures": failures,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for f in failures: print("FAIL", f)
        print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

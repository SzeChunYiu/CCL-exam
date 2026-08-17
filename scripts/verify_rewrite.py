#!/usr/bin/env python3
"""Structural verifier for a rewritten batch of CCL dialogues.

Complements ``qa_cantonese.py``. That gate judges the *register* of the
Cantonese; this one judges everything a rewrite can silently break而 the register
gate would still pass:

  * the fields the site depends on (``id``/``topic``/``title``/``difficulty``,
    segment count, ``n``, ``role``, ``source_lang``) are unchanged
  * ``source``/``model`` still mirror ``en``/``yue`` per ``source_lang``
  * ``wc`` equals the English word count
  * TTS-hostile glyphs are absent from BOTH sides (the register gate reads only
    role-C ``source``, so a dropped glyph in a professional turn is invisible to it)
  * every scoreable item -- numbers, dates, money, proper nouns -- survives into
    the *same segment's* other language
  * no sentence is reused across dialogues

Scoreable items are DERIVED from the text, not listed in a table. A table would
have to be hand-written per dialogue and would therefore only ever cover the
batch someone remembered to extend it for; deriving them means dialogue 87
written by someone else is checked to the same standard as dialogue 1.

Usage
-----
    python3 scripts/verify_rewrite.py build/rewrite/pilot.json
    python3 scripts/verify_rewrite.py data/dialogues.json --baseline data/dialogues.json
    python3 scripts/verify_rewrite.py build/rewrite/batch-02.json --json

Exit 0 = clean. 1 = violations. 4 = could not check (never conflate with clean).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[㐀-鿿]")

FROZEN_TOP = ["id", "topic", "title", "difficulty"]
FROZEN_SEG = ["n", "role", "source_lang"]

# Measured on zh-HK voices, edge-tts 7.2.8: these produce no audio at all.
DROPPED_GLYPHS = "嚹囖嗻啝𠺝𠿪𡃉唩㖑𡀔𠻹𡁜"

# Australian institutions and programmes with no Chinese equivalent a client
# would actually say. Everything else must be rendered into Chinese: the standing
# rule is Chinese wherever a Chinese term exists, English only for an irreducible
# proper noun. "award" is the instructive near-miss -- it looks like a term of art
# but it is a common noun (an industrial award) with a Chinese rendering.
PROPER_NOUNS = ["Centrelink", "Medicare", "myGov", "ImmiAccount", "VEVO", "ABN",
                "TFN", "NDIS", "Fair Work", "MyAgedCare", "PBS", "ATO"]
LATIN_TOKEN = re.compile(r"[A-Za-z][A-Za-z]*(?: [A-Z][A-Za-z]*)*")

# Three irreducible-Latin classes the code-switch scan must NOT flag. Each was
# found as a false positive on real batch text (D031/D035), not hypothesised:
#   1. X光 -- the established Chinese word for "X-ray"; spacing varies. Writing
#      愛克斯光 instead would be absurd, so the X is Han vocabulary.
#   2. A designator letter bound to a Chinese numeral, as in 七B (ward 7B).
#      Dropping the letter loses a scoreable part of the item, so the letter
#      must stay and the scan must tolerate it.
#   3. A street address -- "Barkly Street" has no Chinese name a client would
#      recognise; the English name is what the client actually says aloud.
# The masks are narrow on purpose: a bare capital letter anywhere else, or any
# other Latin word, still fires.
X_RAY = re.compile(r"X\s*光")
NUM_DESIGNATOR = re.compile(r"([零一二三四五六七八九十百千兩]\s*)([A-Z])(?![A-Za-z])")
STREET_NAME = re.compile(
    r"[A-Z][a-z]+ (?:Street|St|Rd|Road|Ave|Avenue|Drive|Dr|Parade|Pde|Court|"
    r"Ct|Place|Pl|Lane|Ln|Tce|Terrace|Crescent|Blvd|Boulevard)\b")

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
# Only cardinals bound to a time unit are checked. Bare "one"/"two" in English is
# far too polysemous -- "one more thing", "the one that's missing" -- and checking
# it produced false positives on real text, which is worse than a miss: a checker
# that cries wolf on its first real run gets switched off.
CARDINALS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
TIME_UNITS = r"(?:business day|working day|day|week|fortnight|month|year|hour|minute)s?"
CARDINAL_UNIT = re.compile(rf"\b({'|'.join(CARDINALS)})\s+{TIME_UNITS}\b", re.I)
DIGITS_IN_EN = re.compile(r"\d[\d,]*(?:\.\d+)?")

_D = "零一二三四五六七八九"


def han_int(n: int) -> str:
    """Render a non-negative integer in standard Chinese numerals."""
    if n < 10:
        return _D[n]
    if n < 20:                      # 十一, not 一十一
        return "十" + (_D[n % 10] if n % 10 else "")
    out, units = "", [(10000, "萬"), (1000, "千"), (100, "百"), (10, "十")]
    rest, zero = n, False
    for value, name in units:
        q, rest = divmod(rest, value)
        if q:
            if zero:
                out += "零"
                zero = False
            out += han_int(q) + name if value == 10000 else _D[q] + name
        elif out:
            zero = True
    if rest:
        if zero:
            out += "零"
        out += _D[rest]
    return out


def han_forms(n: int) -> set[str]:
    """Every rendering a natural writer might choose for this number.

    Not one canonical string: 2 is 二 counting but 兩 before a classifier (兩個星期,
    never 二個星期), and a year is spoken digit by digit (二零二六) rather than as a
    cardinal. Accepting only one form would fail correct text.
    """
    forms = {han_int(n), str(n)}
    if n == 2:
        forms.add("兩")
    if 1900 <= n <= 2100:
        forms.add("".join(_D[int(c)] for c in str(n)))
    return forms


def scoreables(en: str) -> list[tuple[str, set[str]]]:
    """(label, acceptable Cantonese forms) for each scoreable item in the English."""
    items: list[tuple[str, set[str]]] = []
    for raw in DIGITS_IN_EN.findall(en):
        # 25.40 -> check the dollars; the cents are rendered as 四毫/四十仙 and the
        # variation is wider than the value of checking it.
        whole = raw.replace(",", "").split(".")[0]
        if whole.isdigit():
            items.append((raw, han_forms(int(whole))))
    for word in CARDINAL_UNIT.findall(en):
        items.append((word.lower(), han_forms(CARDINALS[word.lower()])))
    for i, month in enumerate(MONTHS, start=1):
        if re.search(rf"\b{month}\b", en):
            items.append((month, {han_int(i) + "月"}))
    return items


def check(dialogues: list[dict], baseline: dict[str, dict] | None) -> list[str]:
    bad: list[str] = []
    for d in dialogues:
        did = d.get("id", "?")
        old = (baseline or {}).get(did)
        if baseline is not None:
            if old is None:
                bad.append(f"{did}: not present in the baseline bank")
            else:
                for k in FROZEN_TOP:
                    if d.get(k) != old.get(k):
                        bad.append(f"{did}.{k}: {old.get(k)!r} -> {d.get(k)!r} (must be preserved)")
                if len(d["segments"]) != len(old["segments"]):
                    bad.append(f"{did}: {len(old['segments'])} segments -> {len(d['segments'])}")
                    old = None

        for i, s in enumerate(d["segments"]):
            tag = f"{did} seg{s.get('n')}"
            if old is not None:
                o = old["segments"][i]
                for k in FROZEN_SEG:
                    if s.get(k) != o.get(k):
                        bad.append(f"{tag}.{k}: {o.get(k)!r} -> {s.get(k)!r} (must be preserved)")

            en, yue, lang = s.get("en", ""), s.get("yue", ""), s.get("source_lang")
            want_src, want_mod = (en, yue) if lang == "en" else (yue, en)
            if s.get("source") != want_src:
                bad.append(f"{tag}: source does not mirror source_lang={lang}")
            if s.get("model") != want_mod:
                bad.append(f"{tag}: model does not mirror source_lang={lang}")
            if s.get("wc") != len(en.split()):
                bad.append(f"{tag}: wc {s.get('wc')} != {len(en.split())} English words")
            for field, text in (("en", en), ("yue", yue)):
                hit = [g for g in DROPPED_GLYPHS if g in text]
                if hit:
                    bad.append(f"{tag}.{field}: TTS-dropped glyph {hit}")
            if "'" in en:
                bad.append(f"{tag}: straight apostrophe -- the bank uses the curly form")

            for label, forms in scoreables(en):
                if not any(f in yue for f in forms):
                    bad.append(f"{tag}: scoreable {label!r} lost in the Cantonese "
                               f"(expected one of {sorted(forms)})")

            # A term's Cantonese gloss may legitimately name an entity its English
            # does not: "bulk billing" is 直接向 Medicare 收費, because bulk billing
            # *is* the Medicare direct-billing arrangement. Without this mask the
            # check fires on correct text. Masking only the sanctioned gloss keeps
            # a stray entity anywhere else in the turn catchable.
            outside_gloss = yue.replace(d.get("term_yue", "\0"), "")
            for noun in PROPER_NOUNS:
                if noun in en and noun not in yue:
                    bad.append(f"{tag}: proper noun {noun!r} in English but not in Cantonese")
                if noun in outside_gloss and noun not in en:
                    bad.append(f"{tag}: proper noun {noun!r} in Cantonese but not in English")
            scan = X_RAY.sub(" ", NUM_DESIGNATOR.sub(r"\1", outside_gloss))
            for tok in LATIN_TOKEN.findall(scan):
                if tok not in PROPER_NOUNS and not STREET_NAME.fullmatch(tok):
                    bad.append(f"{tag}: code-switching leak -- {tok!r} in Cantonese has a "
                               f"Chinese equivalent and must be rendered")

    seen: dict[str, str] = {}
    for d in dialogues:
        for s in d["segments"]:
            for piece in re.split(r"[。！？]", s.get("yue", "")):
                piece = piece.strip()
                if len(HAN.findall(piece)) >= 6:
                    if piece in seen and seen[piece] != d["id"]:
                        bad.append(f"sentence reused across {seen[piece]} and {d['id']}: {piece}")
                    seen[piece] = d["id"]
    return bad


def self_test() -> int:
    """A verifier nobody has seen fail is not evidence of anything.

    Each control mutates a known-good batch in one way and asserts the specific
    rule fires. The last two are the false-positive controls: correct text that an
    over-eager version of this checker would condemn.
    """
    good = [{
        "id": "T001", "topic": "Health", "title": "t", "difficulty": "Easy",
        "term": "bulk billing", "term_yue": "直接向 Medicare 收費",
        "segments": [
            {"n": 1, "role": "P", "source_lang": "en", "wc": 8,
             "en": "The clinic charges $78 and bills Medicare directly.",
             "yue": "診所收七十八蚊，可以直接向 Medicare 收費。",
             "source": "The clinic charges $78 and bills Medicare directly.",
             "model": "診所收七十八蚊，可以直接向 Medicare 收費。"},
            {"n": 2, "role": "C", "source_lang": "yue", "wc": 8,
             "en": "Allow two weeks, and $1,899 is at stake.",
             "yue": "等兩個星期啦，一千八百九十九蚊喎。",
             "source": "等兩個星期啦，一千八百九十九蚊喎。",
             "model": "Allow two weeks, and $1,899 is at stake."},
        ],
    }]
    base = {d["id"]: json.loads(json.dumps(d)) for d in good}
    cases = []

    def mutate(label: str, fn, expect: str):
        b = json.loads(json.dumps(good))
        fn(b)
        hits = check(b, base)
        cases.append((label, expect, any(expect in h for h in hits), hits))

    if check(json.loads(json.dumps(good)), base):
        print("SELF-TEST FAIL: known-good batch does not pass:",
              check(json.loads(json.dumps(good)), base))
        return 5
    print("self-test: known-good batch PASSES (control 0 ok)")

    mutate("wrong wc", lambda b: b[0]["segments"][0].update(wc=99), "wc 99")
    mutate("broken mirror", lambda b: b[0]["segments"][0].update(model="x"), "model does not mirror")
    mutate("changed difficulty", lambda b: b[0].update(difficulty="Hard"), "difficulty")
    mutate("dropped glyph", lambda b: b[0]["segments"][1].update(
        yue=b[0]["segments"][1]["yue"] + "嚹"), "TTS-dropped glyph")
    mutate("money lost from Cantonese", lambda b: b[0]["segments"][0].update(
        yue="診所收錢，可以直接向 Medicare 收費。"), "scoreable '78'")
    mutate("duration lost from Cantonese", lambda b: b[0]["segments"][1].update(
        yue="等一排啦，一千八百九十九蚊喎。"), "scoreable 'two'")
    mutate("entity lost from Cantonese", lambda b: b[0]["segments"][0].update(
        yue="診所收七十八蚊，可以直接向醫保收費。"), "proper noun 'Medicare'")
    mutate("code-switching leak", lambda b: b[0]["segments"][1].update(
        yue="等兩個星期啦，一千八百九十九蚊 insurance 喎。"), "code-switching leak")
    mutate("bare capital letter leaks", lambda b: b[0]["segments"][1].update(
        yue="等兩個星期啦，X 一千八百九十九蚊喎。"), "code-switching leak")
    mutate("straight apostrophe", lambda b: b[0]["segments"][0].update(
        en="The clinic charges $78 and it's bulk billed.", wc=8), "straight apostrophe")

    ok = True
    for label, expect, fired, hits in cases:
        if not fired:
            print(f"SELF-TEST FAIL: '{label}' should have raised {expect!r}; got {hits}")
            ok = False
    if ok:
        print(f"self-test: {len(cases)} negative controls all FAIL correctly")
    # False-positive controls: correct text an over-eager checker would condemn.
    fp = [
        ("term gloss names Medicare on the Cantonese side only", lambda b: None),
        ("2 written 兩 before a classifier", lambda b: None),
        ("X光 is Chinese vocabulary, not a leak", lambda b: b[0]["segments"][1].update(
            yue="等兩個星期啦，醫生叫我照 X 光，一千八百九十九蚊喎。",
            source="等兩個星期啦，醫生叫我照 X 光，一千八百九十九蚊喎。")),
        ("ward designator letter 七B stays", lambda b: b[0]["segments"][1].update(
            yue="等兩個星期啦，住七B病房，一千八百九十九蚊喎。",
            source="等兩個星期啦，住七B病房，一千八百九十九蚊喎。")),
        ("street name has no Chinese form", lambda b: b[0]["segments"][1].update(
            yue="等兩個星期啦，去 Barkly Street 辦，一千八百九十九蚊喎。",
            source="等兩個星期啦，去 Barkly Street 辦，一千八百九十九蚊喎。")),
    ]
    for label, fn in fp:
        b = json.loads(json.dumps(good))
        fn(b)
        if check(b, base):
            print(f"SELF-TEST FAIL: false positive on {label}")
            ok = False
    if ok:
        print(f"self-test: {len(fp)} false-positive controls stay silent")
    return 0 if ok else 5


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", help="batch JSON to verify")
    ap.add_argument("--baseline", default=str(ROOT / "data" / "dialogues.json"),
                    help="bank the frozen fields are compared against")
    ap.add_argument("--no-baseline", action="store_true",
                    help="skip the frozen-field comparison (for a bank with no predecessor)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.path:
        ap.error("path is required unless --self-test")

    target = Path(args.path)
    if not target.exists():
        print(f"VERIFY INCONCLUSIVE: {target} does not exist -- nothing was checked.",
              file=sys.stderr)
        return 4
    dialogues = json.loads(target.read_text(encoding="utf-8"))

    baseline = None
    if not args.no_baseline:
        bp = Path(args.baseline)
        if not bp.exists():
            print(f"VERIFY INCONCLUSIVE: baseline {bp} not found. Pass --no-baseline "
                  f"to check the rest deliberately; do not read this as a pass.",
                  file=sys.stderr)
            return 4
        baseline = {d["id"]: d for d in json.loads(bp.read_text(encoding="utf-8"))}

    bad = check(dialogues, baseline)
    segs = sum(len(d["segments"]) for d in dialogues)
    if args.json:
        print(json.dumps({"dialogues": len(dialogues), "segments": segs,
                          "violations": bad}, ensure_ascii=False, indent=1))
        return 0 if not bad else 1
    for b in bad:
        print("  FAIL " + b)
    print(f"\nVERIFY: {'PASS' if not bad else f'FAIL ({len(bad)} violation(s))'} "
          f"-- {len(dialogues)} dialogues, {segs} segments"
          + ("" if baseline else "  [frozen-field comparison SKIPPED]"))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())

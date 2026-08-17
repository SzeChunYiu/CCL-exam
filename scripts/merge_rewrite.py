#!/usr/bin/env python3
"""Merge rewritten dialogue batches into a single bank, refusing anything unsafe.

Batches are written independently by different writers, so this is where the
whole-bank invariants get checked -- the ones no single batch can see:

* every original dialogue is present exactly once, with its structure intact
* no batch has quietly dropped or renumbered a segment
* scoreable items (numbers, dates, acronyms) survive from source into model
* the batches do not rhyme with each other

That last one is the reason the rewrite exists. A writer can produce twelve
internally-varied dialogues that happen to share a sentence frame with another
writer's twelve, and only a cross-batch check catches it.

    python3 scripts/merge_rewrite.py --check          # validate, write nothing
    python3 scripts/merge_rewrite.py --apply          # write data/dialogues.json
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[㐀-鿿]")
ACRONYM = re.compile(r"\b[A-Z]{2,}\b")
NUMBER = re.compile(r"\d[\d,.]*")

# Number words the model answer may legitimately use instead of digits.
SPELLED = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
    "11": "eleven", "12": "twelve",
}
# Acronyms with an accepted Chinese rendering -- their absence as Latin text in
# the model answer is correct, not a dropped entity.
TRANSLATABLE = {"ID", "GP", "GST", "ABN", "TFN", "NDIS", "ATO", "VEVO", "PDF", "BSB"}


def load_batches(d: Path) -> list[dict]:
    out, seen = [], {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"{p.name}: invalid JSON ({e})")
        if not isinstance(data, list):
            sys.exit(f"{p.name}: expected a JSON array of dialogues")
        for dlg in data:
            did = dlg.get("id")
            if did in seen:
                sys.exit(f"{did} appears in both {seen[did]} and {p.name}")
            seen[did] = p.name
            out.append(dlg)
    return out


def structural_errors(new: dict, old: dict) -> list[str]:
    errs = []
    for field in ("id", "topic", "title", "difficulty"):
        if field in old and new.get(field) != old.get(field):
            errs.append(f"{field} changed: {old.get(field)!r} -> {new.get(field)!r}")
    if len(new.get("segments", [])) != len(old["segments"]):
        errs.append(f"segment count {len(old['segments'])} -> {len(new.get('segments', []))}")
        return errs
    for ns, os_ in zip(new["segments"], old["segments"]):
        if ns.get("n") != os_["n"]:
            errs.append(f"segment n {os_['n']} -> {ns.get('n')}")
        if ns.get("role") != os_["role"]:
            errs.append(f"S{os_['n']} role changed")
        if ns.get("source_lang") != os_["source_lang"]:
            errs.append(f"S{os_['n']} source_lang changed")
        if not (ns.get("source") or "").strip():
            errs.append(f"S{os_['n']} empty source")
        if not (ns.get("model") or "").strip():
            errs.append(f"S{os_['n']} empty model")
    return errs


def entity_warnings(dlg: dict) -> list[str]:
    warn = []
    for s in dlg.get("segments", []):
        src, mod = s.get("source", ""), s.get("model", "")
        for num in set(NUMBER.findall(src)):
            bare = num.rstrip(".,")
            if not bare:
                continue
            if bare in mod:
                continue
            if SPELLED.get(bare, "\0").lower() in mod.lower():
                continue
            # digits may be written out in Chinese
            if any(c in mod for c in "零一二三四五六七八九十百千萬"):
                continue
            warn.append(f"{dlg['id']} S{s['n']}: number {bare} missing from model")
        for ac in set(ACRONYM.findall(src)) - TRANSLATABLE:
            if ac not in mod:
                warn.append(f"{dlg['id']} S{s['n']}: acronym {ac} missing from model")
    return warn


def cross_batch_repetition(dialogues: list[dict]) -> dict:
    """Sentences and 10-grams shared ACROSS dialogues -- the template signature."""
    def sentences(lang):
        out = []
        for d in dialogues:
            for s in d["segments"]:
                if s["source_lang"] != lang:
                    continue
                sep = r"[。！？]" if lang == "yue" else r"(?<=[.!?])\s+"
                for c in re.split(sep, s["source"]):
                    c = c.strip()
                    if lang == "yue" and len(HAN.findall(c)) >= 6:
                        out.append((d["id"], c))
                    elif lang == "en" and len(c.split()) >= 5:
                        out.append((d["id"], re.sub(r"\s+", " ", c)))
        return out

    report = {}
    for lang in ("yue", "en"):
        pairs = sentences(lang)
        counts = Counter(t for _, t in pairs)
        # only count a repeat if it spans more than one dialogue
        spread = {}
        for did, t in pairs:
            spread.setdefault(t, set()).add(did)
        offenders = {t: sorted(ids) for t, ids in spread.items()
                     if counts[t] > 1 and len(ids) > 1}
        report[lang] = {
            "sentences": len(pairs),
            "cross_dialogue_repeats": len(offenders),
            "pct": round(len(offenders) / max(len(set(t for _, t in pairs)), 1) * 100, 2),
            "worst": sorted(offenders.items(), key=lambda kv: -len(kv[1]))[:6],
        }
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=str(ROOT / "build" / "rewrite"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--max-cross-repeat-pct", type=float, default=2.0)
    args = ap.parse_args()

    original = json.loads((ROOT / "data" / "dialogues.json").read_text(encoding="utf-8"))
    by_id = {d["id"]: d for d in original}
    merged = load_batches(Path(args.dir))
    got = {d["id"] for d in merged}

    print(f"batches supply {len(merged)} dialogues; bank has {len(original)}")
    missing = sorted(set(by_id) - got)
    extra = sorted(got - set(by_id))
    if extra:
        print(f"UNKNOWN ids: {extra}", file=sys.stderr)
    if missing:
        print(f"still missing ({len(missing)}): {', '.join(missing)}")

    hard = []
    for d in merged:
        if d["id"] not in by_id:
            continue
        for e in structural_errors(d, by_id[d["id"]]):
            hard.append(f"{d['id']}: {e}")
    warns = [w for d in merged if d["id"] in by_id for w in entity_warnings(d)]

    rep = cross_batch_repetition(merged)
    print(f"\ncross-dialogue repeated sentences:")
    for lang in ("yue", "en"):
        r = rep[lang]
        print(f"   {lang}: {r['cross_dialogue_repeats']} of {r['sentences']} "
              f"({r['pct']}%)")
        for t, ids in r["worst"][:3]:
            print(f"      shared by {len(ids)} dialogues: {t[:58]}")

    if hard:
        print(f"\n{len(hard)} STRUCTURAL ERROR(S):", file=sys.stderr)
        for e in hard[:25]:
            print(f"   {e}", file=sys.stderr)
    if warns:
        print(f"\n{len(warns)} entity warning(s) (check these by hand):")
        for w in warns[:15]:
            print(f"   {w}")

    blocked = bool(hard) or bool(missing) or bool(extra)
    over = [l for l in ("yue", "en") if rep[l]["pct"] > args.max_cross_repeat_pct]
    if over:
        print(f"\ncross-dialogue repetition over {args.max_cross_repeat_pct}% for {over}",
              file=sys.stderr)
        blocked = True

    if not args.apply:
        print("\n(check only — nothing written)")
        return 1 if blocked else 0

    if blocked:
        print("\nREFUSING to apply: fix the errors above first.", file=sys.stderr)
        return 2

    target = ROOT / "data" / "dialogues.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / "data" / f"dialogues.pre-rewrite.{stamp}.json"
    shutil.copy2(target, backup)
    ordered = [next(d for d in merged if d["id"] == o["id"]) for o in original]
    target.write_text(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {target} ({len(ordered)} dialogues)")
    print(f"previous bank saved to {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

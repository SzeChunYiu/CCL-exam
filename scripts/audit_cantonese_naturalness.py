#!/usr/bin/env python3
"""Soft, corpus-level Cantonese naturalness audit for the CCL dialogue bank.

This script intentionally reports warnings rather than enforcing a simplistic
"natural Cantonese score". Its purpose is to surface translatedese, repetitive
turn design, missing interactional features, and code-switching/particle
patterns that deserve human review.

Usage:
    python3 scripts/audit_cantonese_naturalness.py
    python3 scripts/audit_cantonese_naturalness.py --json
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"

# Strong indicators of Standard Written Chinese when they occur repeatedly in
# otherwise conversational client speech. These are NOT individually illegal:
# quotation of a form/letter/policy can legitimately contain them.
SWC_MARKERS = (
    "現在", "沒有", "這個", "那個", "這些", "那些", "什麼", "哪裡",
    "是否", "但是", "因此", "此外", "然而", "如何", "應如何",
)

# Common spoken-HK-Cantonese features. No single turn needs any one item; the
# dialogue-level absence of almost all of them is what is suspicious.
COLLOQUIAL_MARKERS = (
    "而家", "冇", "呢個", "嗰個", "呢啲", "嗰啲", "乜嘢", "邊度",
    "係咪", "點樣", "點搞", "點算", "喺", "畀", "佢", "佢哋",
    "我哋", "咁", "即係", "其實", "但係", "同埋", "仲有", "跟住",
    "原來", "唔該", "多謝", "麻煩", "唔好意思",
)

# Orthographic approximations only; particle semantics are context-dependent.
SFP_CHARS = set("呀啊啦喎啫㗎嘛咩囉呢喇嘅噃㖭")

REPAIR_MARKERS = (
    "即係你意思", "我意思係", "唔係，我", "唔係呀", "等陣",
    "我想確認", "想確認", "頭先", "定係", "係咪", "聽唔清楚",
    "唔係好明", "搞唔清", "講緊", "先啱",
)

DISCOURSE_MARKERS = (
    "其實", "咁", "即係", "但係", "不過", "同埋", "仲有", "所以",
    "跟住", "原來", "咁樣",
)

ENGLISH_TOKEN_RE = re.compile(r"(?<![A-Za-z])[A-Za-z][A-Za-z0-9.+&/-]*(?:\s+[A-Za-z][A-Za-z0-9.+&/-]*)*")


def client_turns(dialogue: dict) -> list[dict]:
    return [s for s in dialogue.get("segments", []) if s.get("role") == "C"]


def source_text(seg: dict) -> str:
    return str(seg.get("source", ""))


def starts_with_signature(text: str) -> str:
    text = re.sub(r"^[\s，。！？、…—-]+", "", text)
    for marker in ("其實", "咁", "即係", "唔好意思", "我想", "我而家", "但係", "不過"):
        if text.startswith(marker):
            return marker
    # First 4 Han/ASCII characters as a weak fallback for template detection.
    return text[:4]


def audit_dialogue(dialogue: dict) -> dict:
    turns = client_turns(dialogue)
    texts = [source_text(s) for s in turns]
    joined = "\n".join(texts)

    swc = {m: joined.count(m) for m in SWC_MARKERS if m in joined}
    colloquial = {m: joined.count(m) for m in COLLOQUIAL_MARKERS if m in joined}
    discourse = {m: joined.count(m) for m in DISCOURSE_MARKERS if m in joined}
    repairs = [m for m in REPAIR_MARKERS if m in joined]
    particles = sum(1 for t in texts if t.rstrip("。！？!?… ") and t.rstrip("。！？!?… ")[-1] in SFP_CHARS)
    code_switch_turns = sum(bool(ENGLISH_TOKEN_RE.search(t)) for t in texts)
    qingwen = joined.count("請問")
    opener_counts = collections.Counter(starts_with_signature(t) for t in texts if t.strip())
    repeated_opener = opener_counts.most_common(1)[0] if opener_counts else ("", 0)
    lengths = [len(re.sub(r"\s+", "", t)) for t in texts]

    warnings: list[str] = []
    if turns and sum(swc.values()) >= 3:
        warnings.append(f"SWC-heavy client speech: {sum(swc.values())} high-risk markers")
    if turns and len(colloquial) < 3:
        warnings.append("very low diversity of colloquial Hong Kong Cantonese markers")
    if len(turns) >= 5 and particles == 0:
        warnings.append("no client turn ends in a recognised Cantonese particle; inspect for translatedese")
    if qingwen >= 2:
        warnings.append(f"請問 occurs {qingwen} times; inspect for over-formal request templating")
    if repeated_opener[1] >= 3 and repeated_opener[0]:
        warnings.append(f"same client-turn opener repeated {repeated_opener[1]}×: {repeated_opener[0]!r}")
    if len(turns) >= 6 and not repairs:
        warnings.append("no obvious repair/confirmation marker; acceptable, but inspect if dialogue is too linear")
    if lengths and min(lengths) > 18:
        warnings.append("all Cantonese client turns are relatively long; consider short acknowledgements/repairs")
    if lengths and max(lengths) > 80:
        warnings.append("at least one Cantonese turn is very long; inspect breath-group/read-aloud naturalness")
    if code_switch_turns > max(3, len(turns) // 2 + 1):
        warnings.append("English/code-switching appears in many client turns; inspect for gratuitous mixing")

    return {
        "id": dialogue.get("id"),
        "title": dialogue.get("title"),
        "client_turns": len(turns),
        "sfp_ending_turns": particles,
        "repair_markers": repairs,
        "discourse_markers": discourse,
        "colloquial_markers": colloquial,
        "swc_markers": swc,
        "code_switch_turns": code_switch_turns,
        "qingwen_count": qingwen,
        "client_char_range": [min(lengths) if lengths else 0, max(lengths) if lengths else 0],
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    bank = json.loads(BANK.read_text(encoding="utf-8"))
    results = [audit_dialogue(d) for d in bank]

    # Structural role-language policy remains a hard invariant because it is not
    # a subjective naturalness judgement.
    policy_errors = []
    for d in bank:
        for s in d.get("segments", []):
            expected = "en" if s.get("role") == "P" else "yue"
            if s.get("source_lang") != expected:
                policy_errors.append(f"{d.get('id')} S{s.get('n')}: {s.get('role')} -> {s.get('source_lang')} (expected {expected})")

    summary = {
        "dialogues": len(bank),
        "client_turns": sum(r["client_turns"] for r in results),
        "dialogues_with_warnings": sum(bool(r["warnings"]) for r in results),
        "total_warnings": sum(len(r["warnings"]) for r in results),
        "role_language_policy_errors": policy_errors,
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("Cantonese naturalness audit (soft review, not a score)")
        print(f"dialogues: {summary['dialogues']}")
        print(f"client turns: {summary['client_turns']}")
        print(f"dialogues with review warnings: {summary['dialogues_with_warnings']}")
        print(f"total review warnings: {summary['total_warnings']}")
        if policy_errors:
            print("\nHARD role/language policy errors:")
            for e in policy_errors:
                print(f"  - {e}")
        print("\nDialogue warnings:")
        for r in results:
            if r["warnings"]:
                print(f"  {r['id']} {r['title']}")
                for w in r["warnings"]:
                    print(f"    - {w}")

    return 1 if policy_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

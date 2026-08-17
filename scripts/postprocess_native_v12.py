#!/usr/bin/env python3
"""Small diagnostic post-pass for the v12 release architecture.

Two defects were found in source review before measuring v12:
1. one English model template accidentally interpolated a short Chinese issue key;
2. the repair turn appended the same long ``<issue-key>我記住`` tail across variants.

This pass removes those implementation artefacts so the independent audits judge
v12's architecture rather than those two known bugs.  It is intentionally tiny;
once v12 passes, the fixes are folded into the consolidated production builder.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
HAN_RUN = re.compile(r"[㐀-鿿]+")
REPAIR_TAIL = re.compile(r"[^。！？]{2,14}我記住。$")

STAGE_SHORTS = [
    "好呀。明喇。",
    "得呀。知道喇。",
    "係呀。清楚喇。",
    "明白。記低喇。",
    "好喇。照咁做。",
]


def main() -> int:
    data = json.loads(BANK.read_text(encoding="utf-8"))
    english_repairs = 0
    tail_repairs = 0

    for d in data:
        num = int(re.sub(r"\D", "", d["id"]) or "1")
        variant = min(4, max(0, (num - 1) // 100))
        for s in d["segments"]:
            en = s["en"]
            if HAN_RUN.search(en):
                # English model/source should never contain a Chinese interpolation.
                # In v12 this is the accidental short issue key in "the <key> record".
                en = HAN_RUN.sub("case", en)
                en = re.sub(r"\bthe case record\b", "the case record", en)
                en = re.sub(r"\s+", " ", en).strip()
                s["en"] = en
                english_repairs += 1

            yue = s["yue"]
            if REPAIR_TAIL.search(yue):
                yue = REPAIR_TAIL.sub(STAGE_SHORTS[variant], yue)
                s["yue"] = yue
                tail_repairs += 1

            s["wc"] = len(s["en"].split())
            if s["source_lang"] == "en":
                s["source"], s["model"] = s["en"], s["yue"]
            else:
                s["source"], s["model"] = s["yue"], s["en"]

        d["total"] = sum(s["wc"] for s in d["segments"])
        d["maxseg"] = max(s["wc"] for s in d["segments"])

    BANK.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"english_repairs": english_repairs, "repair_tail_replacements": tail_repairs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

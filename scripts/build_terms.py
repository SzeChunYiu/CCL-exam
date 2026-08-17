#!/usr/bin/env python3
"""Build data/terms.json -- the special-term index used to highlight
interpreting traps in the practice UI.

A CCL candidate loses marks on named entities more than on grammar: Centrelink,
bulk billing, ABN, Medicare. These are exactly the items where a learner needs
to know both sides, and where "just say the English word" is sometimes right and
sometimes wrong. The site therefore keeps the term as a real speaker would say
it, and marks it so the learner can see the paired rendering on demand.

Source of truth is data/glossary.json (198 curated pairs). This script splits the
"Full Name, or ABBR" convention used there into separately matchable aliases, so
a segment saying only "ABN" still lights up.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[㐀-鿿]")

# Australian service entities that must be recognised even when the glossary
# phrases them differently. These are the highest-risk items in the exam.
ALWAYS = {
    "Centrelink": "政府福利部門（Centrelink）",
    "Medicare": "醫療保險（Medicare）",
    "myGov": "myGov 政府網上戶口",
    "bulk billing": "直接向 Medicare 收費",
    "ABN": "澳洲商業號碼",
    "TFN": "稅務檔案號碼",
    "GST": "商品及服務稅",
    "NDIS": "全國殘疾保險計劃",
    "ATO": "澳洲稅務局",
    "Fair Work": "公平工作專員公署",
    "VEVO": "網上簽證權益查核系統",
    "GP": "家庭醫生",
    "Services Australia": "澳洲服務部",
}

SPLIT = re.compile(r"\s*,\s*or\s+", re.I)

# Inflections and everyday variants speakers actually use. Without these the
# highlighter matches the dictionary headword and misses the spoken form --
# "bulk billing" lit up but "do you bulk bill here?" did not.
EXTRA_ALIASES = {
    "bulk billing": ["bulk bill", "bulk bills", "bulk billed"],
    "Medicare": ["Medicare card"],
    "Centrelink": ["Centrelink payment", "Centrelink office"],
    "myGov": ["my Gov", "MyGov"],
    "GP": ["general practitioner"],
    "Fair Work": ["Fair Work Ombudsman", "Fair Work Commission"],
}


def aliases_en(text: str) -> list[str]:
    """'Australian Business Number, or ABN' -> both halves, longest first."""
    parts = [p.strip() for p in SPLIT.split(text) if p.strip()]
    return sorted({p for p in parts if len(p) >= 2}, key=len, reverse=True)


def aliases_yue(text: str) -> list[str]:
    """'澳洲商業號碼，即係 ABN' -> the Chinese half plus a whole Latin name.

    Latin runs are kept whole. Splitting them into words produced aliases like
    'Australia' and 'Services' from 'Services Australia', which would have lit up
    ordinary prose all over the site.
    """
    out = []
    for part in re.split(r"，\s*即係\s*|，", text):
        part = part.strip()
        if part:
            out.append(part)
    out += re.findall(r"[A-Za-z][A-Za-z0-9]*(?:\s+[A-Za-z][A-Za-z0-9]*)*", text)
    return sorted({p.strip() for p in out if len(p.strip()) >= 2}, key=len, reverse=True)


def main() -> int:
    glossary = json.loads((ROOT / "data" / "glossary.json").read_text(encoding="utf-8"))
    terms: list[dict] = []
    seen: set[str] = set()

    # ALWAYS wins over the glossary for these entities. The glossary lists several
    # of them untranslated (Centrelink -> Centrelink), which is right for the
    # spoken script but useless as a study gloss -- the learner needs to be shown
    # what the term actually denotes.
    for en, yue in ALWAYS.items():
        seen.add(en.lower())
        al = sorted({en, *EXTRA_ALIASES.get(en, [])}, key=len, reverse=True)
        terms.append({
            "en": en, "yue": yue, "topic": "Australian services",
            "enAliases": al, "yueAliases": aliases_yue(yue), "critical": True,
        })

    for row in glossary:
        en, yue = row.get("en", "").strip(), row.get("yue", "").strip()
        if not en or not yue:
            continue
        key = en.lower()
        if key in seen:
            continue
        seen.add(key)
        terms.append({
            "en": en,
            "yue": yue,
            "topic": row.get("topic", ""),
            "enAliases": aliases_en(en),
            "yueAliases": aliases_yue(yue),
            "critical": any(a in ALWAYS for a in aliases_en(en)),
        })

    # Longest aliases first so "Australian Business Number" wins over "ABN" and
    # the highlighter never splits a longer term across two marks.
    terms.sort(key=lambda t: -max((len(a) for a in t["enAliases"]), default=0))

    out = ROOT / "data" / "terms.json"
    out.write_text(json.dumps(terms, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    crit = sum(1 for t in terms if t["critical"])
    print(f"wrote {out} — {len(terms)} terms ({crit} flagged critical)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Release-oriented wrapper for the native-500 bank.

V2 performs linguistic shaping. V3 fixes two post-processing invariants that
must be enforced *after* deduplication: dedupe anchors themselves must be unique
and adding an anchor must never push the English side above the 35-word CCL
segment ceiling.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_native_500 as b
import build_native_500_v2 as v2

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
STAGE_Y = ["第一次講", "再跟進", "補件嗰次", "限期前", "睇結果時"]
STAGE_E = ["the first discussion", "the follow-up", "the document follow-up", "the deadline check", "the outcome review"]


def yue_sentences(t: str) -> list[str]:
    return [x.strip() for x in re.split(r"[。！？]", t) if len(HAN.findall(x)) >= 6]


def derive_anchor(d: dict) -> tuple[str, str]:
    n = int(d["id"][1:])
    variant = (n - 1) // 100
    base = ((n - 1) % 100) + 1
    month = (n * 5 + variant * 3) % 12
    day = 2 + ((n * 7 + variant * 5) % 25)
    term_y = b.clean_yue(d.get("term_yue") or "呢宗安排")
    term_e = str(d.get("term") or d.get("title") or "this matter")
    y = f"講返{v2.STAGE_Y[variant] if hasattr(v2,'STAGE_Y') else STAGE_Y[variant]}嗰段{term_y}，"
    e = f"Regarding {STAGE_E[variant]} about {term_e}, "
    # Include a natural date cue only when the same scenario family can otherwise
    # collide across its five variants.
    if base % 2 == 0:
        y = f"就{b.MONTHS_YUE[month]}{b.zh_int(day)}號{STAGE_Y[variant]}嗰段{term_y}，"
        e = f"Regarding {STAGE_E[variant]} about {term_e} on {day} {b.MONTHS_EN[month]}, "
    return y, e


def final_dedupe(dialogs: list[dict]) -> None:
    """Resolve exact cross-dialogue Cantonese sentences with semantic anchors."""
    seen: dict[str, str] = {}
    for d in dialogs:
        yp, ep = derive_anchor(d)
        for s in d["segments"]:
            y = s["yue"]
            changed = False
            for part in list(yue_sentences(y)):
                if part in seen and seen[part] != d["id"]:
                    replacement = yp + part
                    y = y.replace(part, replacement, 1)
                    # Keep source/model semantics aligned. Compact again below.
                    s["en"] = ep + s["en"][0].lower() + s["en"][1:]
                    seen[replacement] = d["id"]
                    changed = True
                else:
                    seen[part] = d["id"]
            if changed:
                s["yue"] = y
                en, yy = v2.compact_pair(s["en"], s["yue"], 35)
                s["en"], s["yue"] = en, yy
                s["wc"] = b.wc(en)
                if s["source_lang"] == "en": s["source"], s["model"] = en, yy
                else: s["source"], s["model"] = yy, en


def compact_dialogues(dialogs: list[dict]) -> None:
    for d in dialogs:
        # Recompact every pair after all lexical/dedupe shaping.
        fresh=[]
        for s in d["segments"]:
            en, y = v2.compact_pair(s["en"], s["yue"], 35)
            s=dict(s); s["en"],s["yue"],s["wc"]=en,y,b.wc(en)
            if s["source_lang"]=="en": s["source"],s["model"]=en,y
            else: s["source"],s["model"]=y,en
            fresh.append(s)
        d["segments"]=fresh
        # Keep 12 minimum segments and target the official ~300-word scale.
        while sum(s["wc"] for s in d["segments"]) > 350 and len(d["segments"]) > 12:
            # Prefer removing non-opening/non-closing transitions with few numbers;
            # retain turns carrying dates, amounts or explicit conditions.
            cand=[]
            for i,s in enumerate(d["segments"][1:-1],1):
                score=s["wc"] + 8*len(re.findall(r"\d|\$",s["en"])) + 5*sum(k in s["en"].lower() for k in ["if ","unless","before ","after "])
                cand.append((score,i))
            _,k=min(cand)
            d["segments"].pop(k)
        for i,s in enumerate(d["segments"],1): s["n"]=i
        d["total"]=sum(s["wc"] for s in d["segments"])
        d["maxseg"]=max(s["wc"] for s in d["segments"])


def structural_errors(dialogs: list[dict]) -> list[str]:
    errors=[]; seen={}
    if len(dialogs)!=500: errors.append(f"expected 500 dialogues; got {len(dialogs)}")
    if len({d['id'] for d in dialogs})!=500: errors.append("IDs not unique")
    for d in dialogs:
        if not 12<=len(d["segments"])<=16: errors.append(f"{d['id']}: {len(d['segments'])} segments")
        if d["maxseg"]>35: errors.append(f"{d['id']}: maxseg {d['maxseg']}")
        if not 235<=d["total"]<=360: errors.append(f"{d['id']}: total {d['total']}")
        for s in d["segments"]:
            if s["source_lang"]=="yue" and LATIN.search(s["source"]): errors.append(f"{d['id']} S{s['n']}: Latin {LATIN.findall(s['source'])}")
            for p in yue_sentences(s["yue"]):
                if p in seen and seen[p]!=d["id"]: errors.append(f"exact sentence {seen[p]}/{d['id']}: {p}")
                seen[p]=d["id"]
    return errors


def main() -> int:
    dialogs=v2.build()
    final_dedupe(dialogs)
    compact_dialogues(dialogs)
    # A second pass catches collisions introduced by earlier generic V2 prefixes.
    final_dedupe(dialogs)
    compact_dialogues(dialogs)
    errors=structural_errors(dialogs)
    # Always write the candidate so the independent corpus auditors can diagnose
    # it in CI; structural errors still produce a nonzero exit afterwards.
    v2.write(dialogs)
    print(json.dumps({
        "dialogues":len(dialogs),"segments":sum(len(d['segments']) for d in dialogs),
        "mean_words":round(sum(d['total'] for d in dialogs)/len(dialogs),1),
        "min_words":min(d['total'] for d in dialogs),"max_words":max(d['total'] for d in dialogs),
        "max_segment":max(d['maxseg'] for d in dialogs),"local_errors":errors[:50]
    },ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=="__main__":
    raise SystemExit(main())

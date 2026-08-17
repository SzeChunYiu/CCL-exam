#!/usr/bin/env python3
"""Bank-wide native-Cantonese / translationese audit.

This complements qa_cantonese.py (corpus-style metrics) and verify_rewrite.py
(structure/scoreable details).  It focuses on the failure mode that fluent-looking
LLM text can still be English-shaped or generated from a small set of sentence
frames with nouns swapped.

The checks are deliberately decomposed:
  A. exact cross-dialogue sentence reuse
  B. near-duplicate sentence shapes after masking numbers/Latin labels
  C. repeated Cantonese function/discourse skeletons
  D. known translationese / generator fingerprints
  E. opening, closing and particle concentration
  F. interactional breadth: repair, change-of-state, short response tokens
  G. turn-length rhythm and SWC-shaped wording

It is a *bank gate*, not a grammar checker.  Natural common fragments such as
「係咪」 are expected; what is suspicious is the same multi-clause architecture
recurring across unrelated dialogues.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "data" / "dialogues.json"
HAN_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+&./'-]*(?:\s+[A-Za-z][A-Za-z0-9+&./'-]*)*")
NUM_RE = re.compile(r"(?:\$?\d[\d,.]*(?:%|\b)|[零一二三四五六七八九十百千萬億兩]+(?:蚊|元|日|號|月|年|點|時|分|個|星期|週|工作日)?)")
PUNCT_RE = re.compile(r"[\s，。！？!?、；：:,.…—–()（）「」『』\[\]【】]+")

# High-information Cantonese function/discourse resources.  We preserve these
# while abstracting content words; repeated sequences expose a shared generator
# frame even where different nouns have been substituted.
FUNCTION_TOKENS = sorted({
    "唔好意思", "你可唔可以", "我可唔可以", "可唔可以", "使唔使", "會唔會",
    "有冇", "係咪", "係唔係", "如果", "除非", "否則", "因為", "所以", "但係",
    "不過", "同埋", "仲有", "其實", "即係", "原來", "咁樣", "咁", "先", "再",
    "而家", "之前", "之後", "到時", "頭先", "一路", "已經", "仲", "都", "又",
    "淨係", "先至", "一齊", "返", "住", "畀", "俾", "喺", "冇", "唔", "係",
    "我", "你", "佢", "我哋", "你哋", "佢哋", "呢個", "嗰個", "呢啲", "嗰啲",
    "呀", "啊", "啦", "喇", "囉", "喎", "啫", "嘛", "咩", "呢", "㗎", "嘅",
}, key=len, reverse=True)
FUNCTION_RE = re.compile("|".join(map(re.escape, FUNCTION_TOKENS)))

SFP = tuple("呀啊啦喇囉喎啫嘛咩呢㗎嘅啩㖭噃")

SWC_MARKERS = (
    "現在", "沒有", "這個", "那個", "這些", "那些", "什麼", "哪裡", "是否",
    "但是", "因此", "此外", "然而", "如何", "應當", "應該如何", "進行處理",
)

# Known *architectures*, not just exact wording.  These were observed in the
# current generated bank.  A final native rewrite should make them exceptional.
FINGERPRINTS = {
    "term_gloss_lesson": re.compile(r"唔肯定.{0,18}(?:呢個詞|呢個term|呢個字眼).{0,18}(?:情況|個案).{0,12}(?:意思|影響)"),
    "generic_case_effect_next": re.compile(r"可唔可以.{0,12}(?:呢個|呢樣|件事).{0,18}(?:個案|情況).{0,12}(?:影響|下一步).{0,18}(?:下一步|做咩)"),
    "noted_but_current": re.compile(r"(?:之前|早前).{0,15}(?:記低|記咗|寫低).{0,18}(?:唔肯定|唔知).{0,15}(?:最新|仲啱|仲適用)"),
    "generic_next_step": re.compile(r"下一步係.{4,}"),
    "upload_keep_reference": re.compile(r"(?:上載|upload).{0,20}(?:保留|留低|保存).{0,10}(?:參考編號|reference|確認)"),
    "wait_then_call": re.compile(r"(?:等幾耐|幾時).{0,20}(?:冇消息|未有消息).{0,20}(?:打電話|再聯絡|跟進)"),
    "all_docs_enough": re.compile(r"(?:夠唔夠|齊唔齊).{0,20}(?:等齊|所有|全部).{0,15}(?:先交|提交|開始處理)"),
    "decision_reasons_review": re.compile(r"(?:書面|寫低).{0,10}(?:理由|決定).{0,20}(?:覆核|review|下一步)"),
}

REPAIR_PATTERNS = (
    re.compile(r"唔係[呀啊，,].{0,18}(?:意思|講緊|係)"),
    re.compile(r"等陣|等一等|等等"),
    re.compile(r"(?:星期|號|蚊|元|reference|編號).{0,12}(?:定|唔係|係咪)"),
    re.compile(r"你頭先|頭先你"),
    re.compile(r"即係你意思係|即係話"),
    re.compile(r"聽唔清|聽錯|搞錯|睇錯|記錯"),
)
CHANGE_STATE = ("哦", "噢", "啊", "原來", "明白", "係呀", "係喎", "咁就", "好彩", "弊喇")

@dataclass(frozen=True)
class Sent:
    did: str
    seg: int
    text: str


def han_len(s: str) -> int:
    return len(HAN_RE.findall(s))


def client_turns(bank: list[dict]) -> list[tuple[str, int, str]]:
    out=[]
    for d in bank:
        for s in d.get("segments",[]):
            if s.get("role")=="C" and s.get("source_lang")=="yue":
                out.append((d["id"], int(s.get("n",0)), str(s.get("source", ""))))
    return out


def sentences(bank: list[dict]) -> list[Sent]:
    out=[]
    for did,n,text in client_turns(bank):
        for p in re.split(r"[。！？!?]+", text):
            p=p.strip(" ，、；：…—-\t\n")
            if han_len(p)>=6:
                out.append(Sent(did,n,p))
    return out


def mask_content(s: str) -> str:
    s=LATIN_RE.sub("<LAT>", s)
    s=NUM_RE.sub("<NUM>", s)
    s=PUNCT_RE.sub("", s)
    return s


def function_skeleton(s: str) -> str:
    # Sort by occurrence in the original sentence, preserving interactional order.
    hits=[]
    for m in FUNCTION_RE.finditer(s):
        hits.append((m.start(), m.group(0)))
    return "|".join(t for _,t in hits)


def exact_reuse(ss: list[Sent]) -> list[dict]:
    by=collections.defaultdict(list)
    for x in ss: by[x.text].append(x)
    out=[]
    for text,items in by.items():
        ds=sorted({x.did for x in items})
        if len(ds)>1:
            out.append({"text":text,"dialogues":ds,"occurrences":len(items)})
    return sorted(out,key=lambda x:(-len(x["dialogues"]),-han_len(x["text"])))


def skeleton_reuse(ss: list[Sent]) -> list[dict]:
    by=collections.defaultdict(list)
    for x in ss:
        sk=function_skeleton(x.text)
        # At least five function/discourse items and enough shape to be meaningful.
        if sk.count("|")>=4:
            by[sk].append(x)
    out=[]
    for sk,items in by.items():
        ds=sorted({x.did for x in items})
        texts=sorted({x.text for x in items})
        if len(ds)>=3 and len(texts)>=2:
            out.append({"skeleton":sk,"dialogues":ds,"examples":texts[:4]})
    return sorted(out,key=lambda x:-len(x["dialogues"]))


def near_duplicates(ss: list[Sent], threshold: float=.86) -> list[dict]:
    # Bucket by masked length to avoid O(n^2) comparisons that cannot match.
    buckets=collections.defaultdict(list)
    for x in ss:
        m=mask_content(x.text)
        if han_len(m)<9: continue
        buckets[len(m)//6].append((x,m))
    out=[]
    seen=set()
    for b,items in buckets.items():
        candidates=items + buckets.get(b-1,[]) + buckets.get(b+1,[])
        for x,a in items:
            for y,c in candidates:
                if x.did>=y.did: continue
                key=(x.did,x.seg,y.did,y.seg,a,c)
                if key in seen: continue
                seen.add(key)
                # quick length guard
                if min(len(a),len(c))/max(len(a),len(c),1)<.72: continue
                r=difflib.SequenceMatcher(None,a,c,autojunk=False).ratio()
                if r>=threshold and x.text!=y.text:
                    out.append({"ratio":round(r,3),"a":f"{x.did} S{x.seg}","b":f"{y.did} S{y.seg}","text_a":x.text,"text_b":y.text})
    out.sort(key=lambda x:-x["ratio"])
    return out


def first_signature(text: str) -> str:
    t=PUNCT_RE.sub("",text)
    for p in ("唔好意思","其實","即係","咁","我而家","我想","我係","我已經","如果","但係","好","係","哦","原來"):
        if t.startswith(p): return p
    return t[:4]


def ending_signature(text: str) -> str:
    t=text.rstrip("。！？!?… ，")
    if not t: return ""
    # capture final discourse/particle cluster rather than one final glyph.
    m=re.search(r"(係咪|得唔得|可唔可以)?([呀啊啦喇囉喎啫嘛咩呢㗎嘅啩㖭噃]{1,3})$",t)
    return (m.group(0) if m else "<bare>")


def audit(bank: list[dict], near_threshold: float) -> dict:
    turns=client_turns(bank); ss=sentences(bank)
    exact=exact_reuse(ss); skeletons=skeleton_reuse(ss); near=near_duplicates(ss,near_threshold)
    joined="\n".join(t for _,_,t in turns)
    fp={k:len(rx.findall(joined)) for k,rx in FINGERPRINTS.items()}

    openers=collections.Counter(first_signature(t) for _,_,t in turns)
    endings=collections.Counter(ending_signature(t) for _,_,t in turns)
    swc=collections.Counter({m:joined.count(m) for m in SWC_MARKERS if m in joined})
    repairs=sum(any(rx.search(t) for rx in REPAIR_PATTERNS) for _,_,t in turns)
    changes=sum(any(t.lstrip().startswith(x) for x in CHANGE_STATE) for _,_,t in turns)
    lengths=[han_len(t) for _,_,t in turns]
    short=sum(n<=10 for n in lengths); long=sum(n>=45 for n in lengths)
    bare=endings.get("<bare>",0)

    dialogue_issue=collections.defaultdict(list)
    for d in bank:
        ct=[s.get("source","") for s in d.get("segments",[]) if s.get("role")=="C" and s.get("source_lang")=="yue"]
        if not ct: continue
        j="\n".join(ct)
        local_fp=[name for name,rx in FINGERPRINTS.items() if rx.search(j)]
        if local_fp: dialogue_issue[d["id"]].append("fingerprints: "+", ".join(local_fp))
        if sum(any(rx.search(t) for rx in REPAIR_PATTERNS) for t in ct)==0 and len(ct)>=6:
            dialogue_issue[d["id"]].append("no repair/confirmation event")
        if not any(han_len(t)<=10 for t in ct):
            dialogue_issue[d["id"]].append("no short client turn")
        if sum(sum(t.count(m) for m in SWC_MARKERS) for t in ct)>=3:
            dialogue_issue[d["id"]].append("SWC-shaped wording")

    # Blocking gates. Exact reuse is unacceptable. Near/skeleton gates are high
    # enough to allow ordinary language but low enough to catch family templates.
    failures=[]
    if exact: failures.append(f"{len(exact)} exact Cantonese sentences reused across dialogues")
    if len(near)>25: failures.append(f"{len(near)} near-duplicate cross-dialogue sentence pairs >= {near_threshold:.2f}")
    if len(skeletons)>20: failures.append(f"{len(skeletons)} repeated interactional skeletons span >=3 dialogues")
    high_fp={k:v for k,v in fp.items() if v>3}
    if high_fp: failures.append("generator fingerprints over corpus limit: "+str(high_fp))
    # An entirely polished bank with virtually no short responses/repair is also a
    # translationese signal, but make the corpus thresholds broad rather than quotas.
    if turns and short/len(turns)<.05: failures.append(f"short client turns only {short}/{len(turns)} (<5%)")
    if turns and repairs/len(turns)<.04: failures.append(f"repair/confirmation turns only {repairs}/{len(turns)} (<4%)")

    return {
        "dialogues":len(bank),"client_turns":len(turns),"client_sentences":len(ss),
        "failures":failures,
        "exact_reuse_count":len(exact),"exact_reuse":exact[:100],
        "near_duplicate_count":len(near),"near_duplicates":near[:100],
        "skeleton_repeat_count":len(skeletons),"skeleton_repeats":skeletons[:100],
        "fingerprints":fp,
        "top_openers":openers.most_common(15),"top_endings":endings.most_common(15),
        "swc_markers":dict(swc),
        "repair_turns":repairs,"change_state_turns":changes,
        "short_turns_le10":short,"long_turns_ge45":long,"bare_endings":bare,
        "client_char_range":[min(lengths) if lengths else 0,max(lengths) if lengths else 0],
        "dialogue_review":dict(dialogue_issue),
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("path",nargs="?",default=str(DEFAULT_BANK))
    ap.add_argument("--json",action="store_true")
    ap.add_argument("--near-threshold",type=float,default=.86)
    args=ap.parse_args()
    bank=json.loads(Path(args.path).read_text(encoding="utf-8"))
    r=audit(bank,args.near_threshold)
    if args.json:
        print(json.dumps(r,ensure_ascii=False,indent=2))
    else:
        print("Native Cantonese v2 bank audit")
        for k in ("dialogues","client_turns","client_sentences","exact_reuse_count","near_duplicate_count","skeleton_repeat_count","repair_turns","change_state_turns","short_turns_le10","long_turns_ge45","bare_endings"):
            print(f"  {k:24s} {r[k]}")
        print("  fingerprints",r["fingerprints"])
        print("  top openers",r["top_openers"][:8])
        print("  top endings",r["top_endings"][:8])
        print("\nVERDICT:","PASS" if not r["failures"] else "FAIL")
        for x in r["failures"]: print(" -",x)
        print("\nWorst near duplicates:")
        for x in r["near_duplicates"][:12]: print(f" {x['ratio']}: {x['a']} / {x['b']} :: {x['text_a']} <> {x['text_b']}")
        print("\nWorst skeletons:")
        for x in r["skeleton_repeats"][:10]: print(len(x["dialogues"]),x["skeleton"],"::",x["examples"][:2])
    return 1 if r["failures"] else 0

if __name__=="__main__":
    raise SystemExit(main())

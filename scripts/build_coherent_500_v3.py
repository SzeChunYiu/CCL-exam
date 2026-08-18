#!/usr/bin/env python3
"""Compact surface layer for the coherent v2 dialogue planner.

Keeps the causal/scenario-grounded v2 turns, but makes the process-answer slot
short enough for the <=35 English-word CCL cap and removes article-doubling when
a scenario label already starts with a/an/the.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import build_coherent_500 as base

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUT=ROOT/"build"/"coherent500.json"
ACTION={
 "Business":("lodge or correct the business record","提交或者更正商業紀錄"),
 "Consumer":("write to the trader for a remedy","書面搵商戶要求補救"),
 "Employment":("ask payroll or the employer to review it","叫出糧部門或者僱主覆核"),
 "Health":("ask the provider to confirm the care","叫醫療提供者確認安排"),
 "Immigration":("use the official migration process","用正式移民程序處理"),
 "Education":("ask the provider to confirm the record","叫教育機構確認紀錄"),
 "Housing":("write to the agent or landlord","書面搵代理或者業主"),
 "Insurance":("use the insurer complaint process","用保險公司投訴程序"),
 "Social services":("use the service review process","用相關服務覆核程序"),
}

def tidy_articles(text:str)->str:
    # Scenario labels such as "a new sole-trader registration" already carry an
    # article. Frames are deliberately article-neutral, but keep this guard too.
    text=re.sub(r"\bThe a\s+", "A ", text)
    text=re.sub(r"\bThe an\s+", "An ", text)
    text=re.sub(r"\bthe a\s+", "a ", text)
    text=re.sub(r"\bthe an\s+", "an ", text)
    return text

def compact_process(ns:dict,s:dict,i:int,v:int)->tuple[str,str,str]:
    _,_,portal_en,portal_yu=base.service_pair(ns,s)
    act_en,act_yu=ACTION[s["topic"]]
    issue,iy=s["issue_en"],s["issue_yue"]; docs,dcy=s["doc_en"],s["doc_yue"]; term,ty=s["term_en"],s["term_yue"]
    en_opts=[
      f"For {issue}, {act_en}. Use {portal_en}; keep {docs} ready.",
      f"The practical step for {issue} is to {act_en}. Keep {docs}; use {portal_en} for the record.",
      f"To move {issue} forward, {act_en}. Keep {docs} together and use {portal_en}.",
      f"For this {term} matter, {act_en}. Use {portal_en} for {issue}, with {docs} ready.",
      f"On {issue}, {act_en}. Put {docs} through {portal_en} if the service asks for them.",
    ]
    yu_opts=[
      f"處理{iy}，要{act_yu}。用{portal_yu}跟進，{dcy}就準備好先。",
      f"{iy}實際要做嘅係{act_yu}。{dcy}留好，用{portal_yu}跟紀錄。",
      f"想推進{iy}，就{act_yu}。{dcy}放埋一齊，再用{portal_yu}處理。",
      f"講返{ty}呢單{iy}，要{act_yu}。{dcy}準備好，再用{portal_yu}跟。",
      f"就{iy}嚟講，先{act_yu}。服務機構要資料時，就經{portal_yu}交{dcy}。",
    ]
    return "P",en_opts[(i+v)%5],base.clean_yue(yu_opts[(i+v)%5])

def make_dialogue(ns:dict,s:dict,i:int,v:int)->dict:
    raw=base.turns(ns,s,i,v)
    raw[4]=compact_process(ns,s,i,v)
    did=f"D{v*100+i+1:03d}"; stages=base.STAGES[v]; segs=[]
    for n,((role,en,yu),stage) in enumerate(zip(raw,stages),1):
        en=tidy_articles(en.replace("'","’")); yu=base.clean_yue(yu)
        words=len(en.split())
        if words>35: raise SystemExit(f"{did} S{n:02d}: {words} words > 35: {en}")
        want="P" if n%2 else "C"
        if role!=want: raise SystemExit(f"{did} S{n:02d}: role {role} != {want}")
        lang="en" if role=="P" else "yue"; src=en if lang=="en" else yu; model=yu if lang=="en" else en
        segs.append({"n":n,"role":role,"source_lang":lang,"source":src,"model":model,"en":en,"yue":yu,"wc":words,"stage":stage})
    return {"id":did,"topic":s["topic"],"title":s["title"]+base.VARIANT_SUFFIX[v],"term":s["term_en"],"term_yue":s["term_yue"],"segments":segs,"total":sum(x["wc"] for x in segs),"maxseg":max(x["wc"] for x in segs),"difficulty":"Medium","logic_version":"coherent-v3","encounter_variant":v}

def build():
    ns,seeds=base.load_backbone(); bank=[]
    for v in range(5):
      for i,s in enumerate(seeds): bank.append(make_dialogue(ns,s,i,v))
    if [d["id"] for d in bank]!=[f"D{i:03d}" for i in range(1,501)]: raise SystemExit("ID coverage/order is not D001..D500")
    if sum(len(d["segments"]) for d in bank)!=6000: raise SystemExit("segment coverage is not 6000")
    return bank

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--out",default=str(DEFAULT_OUT)); ap.add_argument("--promote",action="store_true"); args=ap.parse_args()
    bank=build(); out=ROOT/"data/dialogues.json" if args.promote else Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(out),"dialogues":500,"segments":6000,"max_segment_words":max(d["maxseg"] for d in bank),"logic_version":"coherent-v3"},indent=2,ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())

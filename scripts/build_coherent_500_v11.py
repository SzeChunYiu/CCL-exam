#!/usr/bin/env python3
"""Coherent v11: cap-safe/article-neutral wrapper for the v9 high-entropy bank."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import build_coherent_500_v10 as v10
import build_coherent_500_v9 as v9
import build_coherent_500_v8 as v8

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUT=ROOT/'build'/'coherent500.json'
_orig_officer=v10.officer
_orig_client=v9.client

def tidy(text:str)->str:
    t=text
    t=re.sub(r'\b(?:Your|your|This|this|That|that|Our|our) (a|an)\s+',lambda m:m.group(1).capitalize()+' ' if m.group(0)[0].isupper() else m.group(1)+' ',t)
    t=re.sub(r'\bthe the\b','the',t,flags=re.I)
    t=re.sub(r'\bThe the\b','The',t)
    return t

def term_rule(s,i,v):
    rule=v9.RULE_EN[s['topic']]; ry=v9.RULE_Y[s['topic']]
    if v==1:
        ens=[
          f"{s['issue_en']} records {s['detail_en']}; for {s['term_en']}, {rule}.",
          f"On {s['issue_en']}, the recorded fact is {s['detail_en']}; {s['term_en']} follows this rule: {rule}.",
          f"For {s['issue_en']}, {s['detail_en']} is on file; under {s['term_en']}, {rule}.",
          f"The {s['issue_en']} file has {s['detail_en']}; with {s['term_en']}, {rule}.",
        ]
        yus=[
          f"{s['issue_yue']}份紀錄寫住{s['detail_yue']}；講{s['term_yue']}，{ry}。",
          f"講{s['issue_yue']}，而家紀錄係{s['detail_yue']}；至於{s['term_yue']}，{ry}。",
          f"{s['issue_yue']}而家有{s['detail_yue']}呢項資料；{s['term_yue']}嗰邊就要{ry}。",
          f"{s['issue_yue']}份檔案見到{s['detail_yue']}；跟{s['term_yue']}處理時，{ry}。",
        ]
    else:
        ens=[
          f"{s['term_en']}: {rule}; that rule applies to {s['issue_en']}.",
          f"For {s['issue_en']}, {s['term_en']} matters because {rule}.",
          f"On this {s['issue_en']} file, {s['term_en']} uses one rule: {rule}.",
          f"The {s['issue_en']} record uses {s['term_en']}; in practice, {rule}.",
        ]
        yus=[
          f"{s['term_yue']}呢邊要{ry}；{s['issue_yue']}就按呢個原則睇。",
          f"講{s['issue_yue']}，{s['term_yue']}重要係因為{ry}。",
          f"{s['issue_yue']}呢份紀錄用{s['term_yue']}去睇；實際就係{ry}。",
          f"{s['issue_yue']}要跟{s['term_yue']}處理；簡單講就係{ry}。",
        ]
    p=(i+v)%4
    return tidy(ens[p].replace("'","’")),v9.spoken_yue(yus[p])

def officer(stage,ns,s,i,v):
    if stage=='term_rule': en,yu=term_rule(s,i,v)
    else: en,yu=_orig_officer(stage,ns,s,i,v)
    en=tidy(en)
    if len(en.split())>35:
        # Rare long proper names/details get the existing scenario-grounded ultra
        # realization rather than truncation. This is not the normal surface path.
        en2,yu2=v8.ultra(stage,ns,s,i,v)
        en,yu=tidy(en2),v9.spoken_yue(yu2)
    if len(en.split())>35:
        raise SystemExit(f"officer {stage} still {len(en.split())} words >35: {en}")
    return en,yu

def client(stage,ns,s,i,v):
    en,yu=_orig_client(stage,ns,s,i,v); en=tidy(en)
    if len(en.split())>35:
        en2,_=v8.ultra(stage,ns,s,i,v); en=tidy(en2)
    if len(en.split())>35:
        raise SystemExit(f"client {stage} still {len(en.split())} words >35: {en}")
    return en,yu

v9.officer=officer
v9.client=client

def build(): return v9.build()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default=str(DEFAULT_OUT)); ap.add_argument('--promote',action='store_true'); a=ap.parse_args(); b=build(); out=ROOT/'data/dialogues.json' if a.promote else Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'dialogues':500,'segments':6000,'max_segment_words':max(d['maxseg'] for d in b),'logic_version':'coherent-v2'},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

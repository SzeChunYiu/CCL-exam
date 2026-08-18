#!/usr/bin/env python3
"""Coherent v10: v9 high-entropy realization with agreement-safe process answers."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import build_coherent_500_v9 as v9
import build_coherent_500_v3 as v3

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUT=ROOT/'build'/'coherent500.json'
_orig_officer=v9.officer

def officer(stage,ns,s,i,v):
    if stage!='process_answer':
        return _orig_officer(stage,ns,s,i,v)
    c=v9.context(ns,s,i,v); topic=s['topic']; issue=s['issue_en']; iy=s['issue_yue']; detail=s['detail_en']; dy=s['detail_yue']; docs=s['doc_en']; dcy=s['doc_yue']
    act,ay=v9.ACTION_EN[topic],v9.ACTION_Y[topic]
    p=(i+v)%4
    if v==4:
        ens=[
          f"For {issue}, start with {docs}; then {act} through {c['portal_en']}.",
          f"Start the {issue} check with {docs}; use {c['portal_en']} to {act}.",
          f"On {issue}, {docs} is the evidence to start with; then {act} through {c['portal_en']}.",
          f"Use {docs} first for {issue}; after that, {act} through {c['portal_en']}.",
        ]
        yus=[
          f"{iy}先睇{dcy}；跟住經{c['portal_y']}去{ay}。",
          f"{iy}先用{dcy}開始核對；之後喺{c['portal_y']}去{ay}。",
          f"講返{iy}，起步證明係{dcy}；再經{c['portal_y']}去{ay}。",
          f"{iy}先交{dcy}；之後用{c['portal_y']}去{ay}。",
        ]
    else:
        ens=[
          f"For {issue}, the file shows {detail}; now {act} through {c['portal_en']}, with {docs} ready.",
          f"The {issue} file shows {detail}; use {c['portal_en']} to {act}, and keep {docs} ready.",
          f"On {issue}, {detail} is the recorded fact; next, {act} through {c['portal_en']} with {docs} ready.",
          f"Because {issue} records {detail}, {act} through {c['portal_en']}; keep {docs} ready for the service.",
        ]
        yus=[
          f"{iy}份紀錄寫住{dy}；而家經{c['portal_y']}去{ay}，{dcy}準備好先。",
          f"{iy}而家記住{dy}；用{c['portal_y']}去{ay}，手邊留好{dcy}。",
          f"講返{iy}，紀錄資料係{dy}；跟住經{c['portal_y']}去{ay}，{dcy}先準備好。",
          f"因為{iy}紀錄係{dy}，所以經{c['portal_y']}去{ay}；{dcy}就留喺手邊。",
        ]
    return v3.tidy_articles(ens[p].replace("'","’")),v9.spoken_yue(yus[p])

v9.officer=officer

def build(): return v9.build()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default=str(DEFAULT_OUT)); ap.add_argument('--promote',action='store_true'); a=ap.parse_args(); b=build(); out=ROOT/'data/dialogues.json' if a.promote else Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'dialogues':500,'segments':6000,'max_segment_words':max(d['maxseg'] for d in b),'logic_version':'coherent-v2'},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

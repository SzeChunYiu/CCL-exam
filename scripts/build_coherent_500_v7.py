#!/usr/bin/env python3
"""Coherent v7: deterministic short process answers over v6 domain policy."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import build_coherent_500 as base
import build_coherent_500_v3 as v3
import build_coherent_500_v4 as v4
import build_coherent_500_v5 as v5
import build_coherent_500_v6 as v6  # applies complete 12-domain semantic policy
ROOT=Path(__file__).resolve().parents[1]; DEFAULT_OUT=ROOT/'build'/'coherent500.json'

def process_short(ns,s):
    _,_,portal_en,portal_yu=base.service_pair(ns,s); act_en,act_yu=v3.ACTION[s['topic']]
    en=f"For {s['issue_en']}, {act_en}. Use {portal_en}; keep {s['doc_en']} ready."
    yu=f"處理{s['issue_yue']}，要{act_yu}。用{portal_yu}跟進，{s['doc_yue']}準備好先。"
    return 'P',v3.tidy_articles(en),base.clean_yue(yu)

def make_dialogue(ns,s,i,v):
    raw=base.turns(ns,s,i,v); raw[2]=v4.term_rule(s); raw[4]=process_short(ns,s); raw[6]=v5.submission(ns,s)
    did=f'D{v*100+i+1:03d}'; segs=[]
    for n,((role,en,yu),stage) in enumerate(zip(raw,base.STAGES[v]),1):
        en=v3.tidy_articles(en.replace("'","’")); yu=base.clean_yue(yu)
        if len(en.split())>35:
            if stage=='process_answer': _,en,yu=process_short(ns,s)
            else: en,yu=v6.compact(stage,ns,s,i,v)
        words=len(en.split()); want='P' if n%2 else 'C'
        if words>35: raise SystemExit(f'{did} S{n:02d}: compact {stage} still {words} words >35: {en}')
        if role!=want: raise SystemExit(f'{did} S{n:02d}: role {role} != {want}')
        lang='en' if role=='P' else 'yue'; src=en if lang=='en' else yu; model=yu if lang=='en' else en
        segs.append({'n':n,'role':role,'source_lang':lang,'source':src,'model':model,'en':en,'yue':yu,'wc':words,'stage':stage})
    return {'id':did,'topic':s['topic'],'title':s['title']+base.VARIANT_SUFFIX[v],'term':s['term_en'],'term_yue':s['term_yue'],'segments':segs,'total':sum(x['wc'] for x in segs),'maxseg':max(x['wc'] for x in segs),'difficulty':'Medium','logic_version':'coherent-v2','encounter_variant':v}

def build():
    ns,seeds=base.load_backbone(); bank=[make_dialogue(ns,s,i,v) for v in range(5) for i,s in enumerate(seeds)]
    if [d['id'] for d in bank]!=[f'D{i:03d}' for i in range(1,501)]: raise SystemExit('bad IDs')
    if sum(len(d['segments']) for d in bank)!=6000: raise SystemExit('bad segment count')
    return bank

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default=str(DEFAULT_OUT)); ap.add_argument('--promote',action='store_true'); a=ap.parse_args(); b=build(); out=ROOT/'data/dialogues.json' if a.promote else Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'dialogues':500,'segments':6000,'max_segment_words':max(d['maxseg'] for d in b),'logic_version':'coherent-v2'},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

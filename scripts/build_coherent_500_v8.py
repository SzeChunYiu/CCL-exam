#!/usr/bin/env python3
"""Coherent v8: guaranteed concise stage fallback over v7.

A CCL turn should carry one main interpreting task, not four simultaneous
payloads.  If the scenario-rich v7 realization is still over 35 English words,
this layer keeps the stage's contractually important scenario atom(s) and drops
redundant generic concern/filler language.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import build_coherent_500 as base
import build_coherent_500_v3 as v3
import build_coherent_500_v4 as v4
import build_coherent_500_v5 as v5
import build_coherent_500_v6 as v6
import build_coherent_500_v7 as v7  # imports/installs full 12-domain policy
ROOT=Path(__file__).resolve().parents[1]; DEFAULT_OUT=ROOT/'build'/'coherent500.json'

def ultra(stage,ns,s,i,v):
    org_en,org_yu,portal_en,portal_yu=base.service_pair(ns,s)
    dead_en,dead_yu=base.deadline_pair(ns,s,i,v); proc_en,proc_yu=base.proc_pair(ns,i,v)
    issue,iy=s['issue_en'],s['issue_yue']; term,ty=s['term_en'],s['term_yue']; detail,dy=s['detail_en'],s['detail_yue']; docs,dcy=s['doc_en'],s['doc_yue']
    rule_en,rule_yu=base.RULE[s['topic']]; interim_en,interim_yu=base.INTERIM[s['topic']]; review_en,review_yu=base.REVIEW[s['topic']]
    table={
      'opening':(f"I’m calling from {org_en} about {issue}. Before {term}, confirm your name and reference.",f"我係{org_yu}打嚟講{iy}。講{ty}前，先對返你個名同編號。"),
      'concern_deadline':(f"For {issue}, I need {term} clear before {dead_en}. What should I do first?",f"{iy}呢單嘢，我想喺{dead_yu}前搞清楚{ty}。我第一步做咩好呀？"),
      'update_question':(f"For {issue}, the update mentions {term}. Does {detail} change my next step?",f"{iy}個更新提到{ty}。咁{dy}會唔會改變我下一步呀？"),
      'fact_concern':(f"For {issue}, I was told {detail}. Could {term} affect the next step?",f"講返{iy}，我收到嘅資料係{dy}。咁{ty}會唔會影響下一步呀？"),
      'deadline_concern':(f"For {issue}, the record says {detail}. How does {term} affect what I do next?",f"{iy}份紀錄寫住{dy}。咁{ty}會點影響我下一步呀？"),
      'term_rule':(f"For {term}, {rule_en}. The {issue} record shows {detail}.",f"講到{ty}，{rule_yu}。{iy}份紀錄寫住{dy}。"),
      'fact_check':(f"My {term} information says {detail}. Is that still current for {issue}?",f"我份{ty}資料寫住{dy}。講返{iy}，而家仲啱唔啱呀？"),
      'consequence_question':(f"If {issue} is still unresolved at {dead_en}, what happens next?",f"如果{iy}去到{dead_yu}都未搞掂，之後會點呀？"),
      'missing_info_question':(f"Is anything missing for {issue}? I want the {term} record complete.",f"{iy}仲欠唔欠資料呀？我想{ty}份紀錄齊晒。"),
      'process_answer':v7.process_short(ns,s)[1:],
      'evidence_question':(f"For {issue}, I have {docs}. Should I send them now for {term}?",f"{iy}我有{dcy}。而家交嚟跟{ty}得唔得呀？"),
      'evidence_discrepancy':(f"For {issue}, I have {docs}, but one detail differs. Should I explain that with the {term} evidence?",f"{iy}我有{dcy}，但有一個細節唔同。交{ty}證明時要唔要一齊解釋呀？"),
      'submission_answer':(f"For {issue}, send {docs} through {portal_en}. Keep the {term} reference.",f"{iy}經{portal_yu}交{dcy}。{ty}嗰個參考編號要留低。"),
      'interim_question':(f"While {issue} is checked, what should I do about {term}?",f"{iy}仲核對緊時，{ty}我應該點做呀？"),
      'timing_question':(f"For {issue}, when should I follow up on {term}?",f"{iy}呢單{ty}，我幾時先應該跟進呀？"),
      'consequence_followup':(f"While {issue} is checked, could {term} cause another consequence?",f"核對{iy}期間，{ty}會唔會有其他後果呀？"),
      'timing_answer':(f"For {issue}, allow about {proc_en}. Meanwhile, {interim_en}. Then follow up on the same reference.",f"{iy}預大約{proc_yu}。期間，{interim_yu}。之後用返同一個編號跟進。"),
      'review_question':(f"If the {issue} outcome looks wrong, how do I challenge the {term} decision?",f"如果{iy}個結果唔對路，我點樣先可以覆核{ty}個決定呀？"),
      'change_question':(f"If my contact details change before {issue} finishes, how do I update the {term} record?",f"如果{iy}未完我聯絡資料有變，點樣更新{ty}份紀錄呀？"),
      'review_answer':(f"For {issue}, keep the written reason and {review_en}. Keep the result with {term}.",f"{iy}要留低書面原因，再{review_yu}。最後結果同{ty}放埋一齊。"),
      'closure':(f"Thanks. I’ll keep the reference and follow the {term} step.",f"明白喇。我會留低編號，再照{ty}嗰步跟進呀。"),
    }
    en,yu=table[stage]; return v3.tidy_articles(en),base.clean_yue(yu)

def make_dialogue(ns,s,i,v):
    raw=base.turns(ns,s,i,v); raw[2]=v4.term_rule(s); raw[4]=v7.process_short(ns,s); raw[6]=v5.submission(ns,s)
    did=f'D{v*100+i+1:03d}'; segs=[]
    for n,((role,en,yu),stage) in enumerate(zip(raw,base.STAGES[v]),1):
        en=v3.tidy_articles(en.replace("'","’")); yu=base.clean_yue(yu)
        if len(en.split())>35:
            if stage=='process_answer': _,en,yu=v7.process_short(ns,s)
            else: en,yu=v6.compact(stage,ns,s,i,v)
        if len(en.split())>35: en,yu=ultra(stage,ns,s,i,v)
        words=len(en.split()); want='P' if n%2 else 'C'
        if words>35: raise SystemExit(f'{did} S{n:02d}: ultra {stage} still {words} words >35: {en}')
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

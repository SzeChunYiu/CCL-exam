#!/usr/bin/env python3
"""Coherent v6: stage-level compact fallbacks for the full 500-bank.

The causal planner remains coherent-v2.  This layer only replaces an overlong
surface realization with a shorter realization of the *same dialogue stage*.
No scoreable date/amount/detail/evidence that is contractually required at that
stage is silently truncated.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import build_coherent_500 as base
import build_coherent_500_v3 as v3
import build_coherent_500_v4 as v4
import build_coherent_500_v5 as v5

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUT=ROOT/'build'/'coherent500.json'

def compact(stage,ns,s,i,v):
    org_en,org_yu,portal_en,portal_yu=base.service_pair(ns,s)
    dead_en,dead_yu=base.deadline_pair(ns,s,i,v)
    proc_en,proc_yu=base.proc_pair(ns,i,v)
    concern_en,concern_yu=base.CONCERN[s['topic']]
    interim_en,interim_yu=base.INTERIM[s['topic']]
    review_en,review_yu=base.REVIEW[s['topic']]
    issue,iy=s['issue_en'],s['issue_yue']; term,ty=s['term_en'],s['term_yue']; detail,dy=s['detail_en'],s['detail_yue']; docs,dcy=s['doc_en'],s['doc_yue']
    table={
      'opening':(f"I’m calling from {org_en} about {issue}. Before we discuss {term}, confirm your name and reference.",f"我係{org_yu}打嚟講{iy}。講{ty}之前，先對返你個名同編號。"),
      'concern_deadline':(f"For {issue}, I’m worried that {concern_en}. I need the {term} point clear before {dead_en}.",f"{iy}我係{concern_yu}。{ty}我想喺{dead_yu}之前搞清楚呀。"),
      'update_question':(f"The {issue} update mentions {term}. Does that change what I should do about {detail}?",f"{iy}個更新提到{ty}。咁{dy}會唔會令我下一步唔同呀？"),
      'fact_concern':(f"For {issue}, I was told {detail}. I’m worried that {concern_en} while {term} is checked.",f"講返{iy}，我收到嘅資料係{dy}。核對{ty}期間，我係{concern_yu}呀。"),
      'deadline_concern':(f"For {issue}, I can see {detail}. I need to act before {dead_en}. How does {term} affect the next step?",f"{iy}而家見到{dy}。我要喺{dead_yu}之前處理；{ty}會點影響下一步呀？"),
      'term_rule':v4.term_rule(s)[1:],
      'fact_check':(f"My {term} information says {detail}. For {issue}, is that still current?",f"我份{ty}資料寫住{dy}。講返{iy}，而家仲啱唔啱呀？"),
      'consequence_question':(f"If {issue} is not sorted before {dead_en}, what happens next? I’m worried that {concern_en}.",f"如果{iy}去到{dead_yu}都未搞掂，之後會點呀？我係{concern_yu}。"),
      'missing_info_question':(f"Is anything missing for {issue}? I’d rather provide it before {dead_en} than leave a gap in {term}.",f"{iy}仲欠唔欠資料呀？我想喺{dead_yu}之前補齊，唔想{ty}有缺口。"),
      'process_answer':v3.compact_process(ns,s,i,v)[1:],
      'evidence_question':(f"For {issue}, I have {docs}. Should I send them now, and do you need originals for {term}?",f"{iy}我有{dcy}。而家交得唔得呀？{ty}要正本定清楚副本呢？"),
      'evidence_discrepancy':(f"I have {docs} for {issue}, but one detail differs from an older record. Should I explain that with the {term} evidence?",f"{iy}我有{dcy}，但一個細節同舊紀錄唔同。交{ty}證明時要唔要一齊解釋呀？"),
      'submission_answer':v5.submission(ns,s)[1:],
      'interim_question':(f"While {issue} is being checked, what should I do? I’m worried about {term} before {dead_en}.",f"{iy}仲核對緊時，我應該點做呀？我擔心{ty}去到{dead_yu}仲未清楚。"),
      'timing_question':(f"For {issue}, when should I follow up? I don’t want to miss the {term} response.",f"{iy}我幾時先應該跟進呀？我唔想錯過{ty}嗰邊嘅回覆。"),
      'consequence_followup':(f"While {issue} is checked, could {term} cause another consequence? I want to plan before {dead_en}.",f"核對{iy}期間，{ty}會唔會有其他後果呀？我想喺{dead_yu}之前有準備。"),
      'timing_answer':(f"For {issue}, allow about {proc_en}. Meanwhile, {interim_en}. Follow up on the same reference after that.",f"{iy}預大約{proc_yu}。期間，{interim_yu}。之後用返同一個編號跟進。"),
      'review_question':(f"If the {issue} outcome still looks wrong, who should I contact first? I want the {term} reason explained.",f"如果{iy}個結果仲係唔對路，我應該先搵邊個呀？我想先聽清楚{ty}個原因。"),
      'change_question':(f"If my contact details change before {issue} is finished, what should I do so the {term} notice reaches me?",f"如果{iy}未完之前我聯絡資料有變，點做先唔會收漏{ty}個通知呀？"),
      'review_answer':(f"For {issue}, keep the written reason and {review_en}. Put the result with the {term} record.",f"{iy}要留低書面原因，再{review_yu}。最後結果同{ty}紀錄放埋一齊。"),
      'closure':(f"Thanks. I’ll keep the reference and follow the {term} step for {issue}.",f"明白喇。{iy}我會留低編號，再照{ty}嗰步跟進呀。"),
    }
    if stage not in table: raise KeyError(stage)
    en,yu=table[stage]
    return v3.tidy_articles(en),base.clean_yue(yu)

def make_dialogue(ns,s,i,v):
    raw=base.turns(ns,s,i,v); raw[2]=v4.term_rule(s); raw[4]=v3.compact_process(ns,s,i,v); raw[6]=v5.submission(ns,s)
    did=f'D{v*100+i+1:03d}'; segs=[]
    for n,((role,en,yu),stage) in enumerate(zip(raw,base.STAGES[v]),1):
        en=v3.tidy_articles(en.replace("'","’")); yu=base.clean_yue(yu)
        if len(en.split())>35:
            en,yu=compact(stage,ns,s,i,v)
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

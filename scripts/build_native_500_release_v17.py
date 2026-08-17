#!/usr/bin/env python3
"""Release-v17: deterministic bilingual component pairing for professional turns."""
from __future__ import annotations
import build_native_500_release_v11 as v11
import build_native_500_release_v6 as v6
r=v11.r; base=v11.base; f2=v11.f2; v7=v11.v10.v7
v11.FACT=[
"{p}, for {y}, the detail I need checked is {x}.",
"{p}, please check {x} before deciding {y}.",
"{p}, {y} depends on one detail here: {x}.",
"{p}, can you verify {x} and then tell me where {y} stands?",
"{p}, before we settle {y}, I need you to check {x}.",
"{p}, I’m asking you to reconsider {y} because of {x}.",]

def paired_evidence(seed,variant,action):
    ep=v7.en_components(seed['evidence_en']); yp=f2.components(seed['evidence_yue']); n=min(len(ep),len(yp))
    if not n: return str(seed['evidence_en']),f2.atom(seed['evidence_yue'])
    idx=base.h(seed['title'],variant,action,'paired-evidence-v17')%n
    yc=f2.clip_semantic(yp[idx],'evidence')
    ec=v11.v10.strip_unspoken_entities(ep[idx],yc)
    return ec,yc

def accurate_term_yue(seed,variant,action,fallback):
    full=f2.clean_yue(seed['term_yue']).split('即係',1)[0]
    if '緊急護理診所' in full:
        forms=['醫療保險嘅緊急護理診所','國民醫療保險緊急護理診所','醫療保險嗰間緊急護理診所','緊急護理診所嘅醫療保險安排']
        return forms[base.h(seed['title'],variant,action,'urgent-clinic-term')%len(forms)]
    return fallback

def cue_set17(seed,variant,action):
    c=dict(v11.cue_set(seed,variant,action)); e,ec=paired_evidence(seed,variant,action)
    c['e'],c['ec']=e,ec; c['tc']=accurate_term_yue(seed,variant,action,c['tc'])
    if action==1:
        c['f']=str(seed['fact_en']).strip(); c['fc']=f2.atom(seed['fact_yue'])
    return c

def english_officer(seed,variant,action,c):
    original=v11.cue_set
    try:
        v11.cue_set=lambda _s,_v,_a:c
        en,_=v11.officer(seed,variant,action); return en
    finally: v11.cue_set=original

def low_yue(seed,variant,action,c):
    ic,tc,fc,ec=c['ic'],c['tc'],c['fc'],c['ec']
    if action<=2:
        forms=v6.r4.Y_ACTIONS[action]; idx=(base.h(seed['title'],action,'off-y4')+variant)%len(forms)
    else:
        forms=v6.INTERIM if action==3 else v6.CORRECTION if action==4 else v6.CLOSURE
        idx=(base.h(seed['title'],action,'release-v6')+variant*5+action*3)%len(forms)
    return f2.clean_yue(forms[idx].format(ic=ic,tc=tc,fc=fc,ec=ec))

def officer(seed,variant,action):
    c=cue_set17(seed,variant,action); en=english_officer(seed,variant,action,c); y=low_yue(seed,variant,action,c)
    if action!=1 and c['ec'] not in y: raise SystemExit(f"evidence pair lost: {seed['title']} v{variant} a{action}: {en} || {y}")
    if action==1 and c['fc'] not in y: raise SystemExit(f"fact pair lost: {seed['title']} v{variant}: {en} || {y}")
    return en,y
r.client_model=lambda seed,variant,action:v11.client_model(seed,variant,action,r._ORIG_CLIENT(seed,variant,action)[1])
r.client_turn=v11.client_turn; r.repair_turn=v11.repair_turn; r.officer=officer
if __name__=='__main__': raise SystemExit(r.main())

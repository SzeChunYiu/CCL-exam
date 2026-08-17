#!/usr/bin/env python3
"""Release-v18: fully paired officer semantics plus agreement-safe English.

v17 fixed compound evidence alignment and passed every statistical gate. Manual
review then exposed two remaining language-quality issues: some non-numeric fact
propositions were translated as generic Cantonese details, and two English
professional frames depended on singular subject agreement (e.g. plural
"notices comes first"). v18 uses one explicit EN/Yue fact pair and English forms
that never depend on evidence/fact number.
"""
from __future__ import annotations

import re

import build_native_500_release_v17 as v17

r=v17.r; base=v17.base; f2=v17.f2; v11=v17.v11; v6=v17.v6


def fact_pair(seed: dict, variant: int, action: int) -> tuple[str,str]:
    en=str(seed['fact_en']).strip()
    y=f2.atom(seed['fact_yue'])
    # One state carries the complete proposition; the other four use a natural
    # shared semantic head. This preserves meaning without repeating a long fact
    # verbatim five times across the five scenario variants.
    if variant == base.h(seed['title'],'full-fact-v18') % 5:
        return en,y
    low=en.lower()
    choices=[]
    def pick(vals): return vals[base.h(seed['title'],variant,action,'fact-head-v18')%len(vals)]
    if '症狀' in y or 'symptom' in low:
        return 'the symptoms', pick(['啲症狀','症狀情況','而家啲症狀'])
    if '護照' in y or 'passport' in low:
        return 'the passport details', pick(['護照資料','護照嗰項資料','護照情況'])
    if '簽證' in y or 'visa' in low:
        return 'the visa details', pick(['簽證資料','簽證嗰項資料','簽證情況'])
    if '地址' in y or 'address' in low:
        return 'the address', pick(['個地址','地址資料','嗰個地址'])
    if any(k in y for k in ('收入','工資','時薪')) or any(k in low for k in ('income','wage','salary','hourly rate')):
        return 'the income or pay details', pick(['收入資料','人工資料','嗰筆收入資料'])
    if any(k in y for k in ('金額','費用','價錢','元','條數','筆數')) or any(k in low for k in ('amount','fee','cost','price','$')):
        return 'the amount', pick(['個金額','條數','嗰筆數'])
    if any(k in y for k in ('時間','點鐘','鐘')) or any(k in low for k in ('time','hour','minute')):
        return 'the time', pick(['個時間','嗰個時間','時間資料'])
    if any(k in y for k in ('日期','日子','月','星期')) or any(k in low for k in ('date','day','week','month','september','october','november','december','january','february','march','april','may','june','july','august')):
        return 'the date', pick(['個日期','嗰個日期','個日子'])
    if any(k in y for k in ('工作','工時','職務')) or any(k in low for k in ('work','hours','duties','employment')):
        return 'the work details', pick(['工作資料','工時資料','嗰項工作資料'])
    if any(k in y for k in ('結果','決定','批核')) or any(k in low for k in ('result','decision','approved','approval')):
        return 'the decision details', pick(['決定資料','結果資料','批核資料'])
    return 'that detail', pick(['嗰項資料','嗰個資料','嗰一點'])


def cue_set18(seed: dict, variant: int, action: int) -> dict:
    c=dict(v17.cue_set17(seed,variant,action))
    f,fc=fact_pair(seed,variant,action)
    c['f'],c['fc']=f,fc
    return c


def officer_en(seed: dict, variant: int, action: int, c: dict) -> str:
    p,_=v11.oprefix(seed,variant,action)
    s=v11.h(seed,variant,action,'off',6)
    e,t,i,f=c['e'],c['t'],c['i'],c['f']
    if action==0:
        forms=[
            "{p}, start with {e}; I’ll use it to clarify {t} for {i}.",
            "{p}, for {i}, show me {e}; then we can settle {t}.",
            "{p}, for {i}, I’ll use {e} as the reference before I answer {t}.",
            "{p}, for {i}, I’ll start with {e}, then check {t}.",
            "{p}, I’ll read {e}; after that, we can sort out {t} for {i}.",
            "{p}, with {i}, I need {e} before I answer {t}.",
        ]
    elif action==1:
        forms=[
            "{p}, for {i}, I’ll check {f} before answering {t}.",
            "{p}, before I answer {t} for {i}, I need to verify {f}.",
            "{p}, I need {f} checked for {i} before I answer {t}.",
            "{p}, for {i}, let me verify {f}; {t} comes after that.",
            "{p}, I’ll compare {f} with {i}; then we can settle {t}.",
            "{p}, I won’t guess {t}; first I’ll confirm {f} for {i}.",
        ]
    elif action==2:
        forms=[
            "{p}, keep {e} with {i}; I’ll use that material for {t}.",
            "{p}, for {t}, I need {e} from {i}.",
            "{p}, I’ll match {e} to {t} under {i}.",
            "{p}, put {e} beside {i}; then I can check {t}.",
            "{p}, I need {e} for {i}; from there I’ll check {t}.",
            "{p}, don’t separate {e} from {i}; that material supports the check on {t}.",
        ]
    elif action==3:
        forms=[
            "{p}, don’t change {i} yet; first I’ll check {t} against {e}.",
            "{p}, {t} is still open; keep {i} steady while I read {e}.",
            "{p}, for {i}, wait before changing anything; I’ll compare {e} with {t}.",
            "{p}, leave {i} as it is; {e} will help me settle {t}.",
            "{p}, I’ll check {e}; until then, don’t assume {t} changed for {i}.",
            "{p}, {t} needs checking from {e}; keep {i} unchanged for now.",
        ]
    elif action==4:
        forms=[
            "{p}, if {e} is wrong, amend it under {i}; I’ll recheck {t}.",
            "{p}, for {i}, correct {e} there; then I’ll revisit {t}.",
            "{p}, keep {e} with {i}; fix that record before checking {t} again.",
            "{p}, update {i} with the correct {e}; don’t start over on {t}.",
            "{p}, if {e} needs correction, keep it on {i}; I’ll check {t} again.",
            "{p}, amend {e} on the existing {i}; after that I’ll verify {t}.",
        ]
    else:
        forms=[
            "{p}, save {e} with the answer on {t}; keep both under {i}.",
            "{p}, for {i}, keep {e} beside the written {t} answer.",
            "{p}, {e} and the {t} response belong together; file both with {i}.",
            "{p}, put the written {t} answer next to {e} in the {i} record.",
            "{p}, keep {e} for {i}; save the final {t} response with it.",
            "{p}, the record for {i} should hold {e} and the written {t} answer.",
        ]
    return base.tidy_en(forms[s].format(p=p,e=e,t=t,i=i,f=f))


def officer(seed: dict, variant: int, action: int):
    c=cue_set18(seed,variant,action)
    en=officer_en(seed,variant,action,c)
    y=v17.low_yue(seed,variant,action,c)
    if action!=1 and c['ec'] not in y:
        raise SystemExit(f"evidence pair lost: {seed['title']} v{variant} a{action}: {en} || {y}")
    if c['f'] in en and action==1 and c['fc'] not in y:
        raise SystemExit(f"fact pair lost: {seed['title']} v{variant}: {en} || {y}")
    return en,y

r.client_model=lambda seed,variant,action:v11.client_model(seed,variant,action,r._ORIG_CLIENT(seed,variant,action)[1])
r.client_turn=v11.client_turn; r.repair_turn=v11.repair_turn; r.officer=officer
if __name__=='__main__': raise SystemExit(r.main())

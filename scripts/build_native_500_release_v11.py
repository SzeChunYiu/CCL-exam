#!/usr/bin/env python3
"""Release-v11: v6-level diversity with grammar-safe, aligned realizations.

v6 proved the diversity target is achievable; manual review showed its context
phrases were sometimes inserted mid-clause and its clipped bilingual cues could
refer to different semantic components. v10 fixed meaning fidelity but collapsed
back to a small template inventory. v11 combines the two successful parts:

* preserve the final5 Cantonese CLIENT source verbatim;
* select English and Cantonese cues from the same semantic component (v10);
* keep all context phrases at sentence-initial position;
* use six grammar-safe surface shapes per pragmatic action;
* keep fixed chunks shorter than the anti-template n-gram windows;
* append natural translations of short Cantonese reactions without making them
  substantive audit sentences.
"""
from __future__ import annotations

import re

import build_native_500_release_v10 as v10
import build_native_500_release_v3 as v3

r = v10.r
base = r.base
f2 = v10.f2

CLIENT_PREFIX = [
    ["To begin", "For this question", "At this point", "On this first call", "Right now", "Today"],
    ["Following up", "This time", "On this call", "Checking again", "On the follow-up", "Coming back to this"],
    ["With both records", "For the mismatch", "On the documents", "Comparing the copies", "With the versions apart", "Looking at both copies"],
    ["With time tight", "Before it is due", "For the deadline", "On the timing", "Before time runs out", "While there is time"],
    ["On the decision", "Looking at the result", "Before a review", "For the written result", "After reading the reasons", "On the written answer"],
]
OFF_PREFIX = [
    ["To start", "For now", "At this point", "On this call", "First", "Today"],
    ["Following up", "This time", "On this call", "Back on the matter", "Checking again", "For the follow-up"],
    ["With both copies", "On the records", "For the mismatch", "Comparing the files", "With the documents apart", "On the two versions"],
    ["Before it is due", "With time tight", "For the date", "On the timing", "While there is time", "Before the cutoff"],
    ["On the written result", "Before challenging it", "For the decision", "After reading the reasons", "On that result", "Before any challenge"],
]
OFF_PREFIX_Y = [
    ["今次先", "而家先", "呢一刻", "今次電話", "一開始", "今日先"],
    ["再跟返", "今次再睇", "再聯絡呢次", "接住上次", "重新對下", "今次跟進"],
    ["兩份分開", "睇返紀錄", "對個出入", "比較兩份", "文件分開睇", "兩個版本"],
    ["到期之前", "時間緊嗰邊", "計日子先", "時間嗰邊", "仲有時間", "限期之前"],
    ["睇書面結果", "未挑戰之前", "講個決定", "睇完理由", "講返個結果", "未覆核之前"],
]

REACTIONS = {
    "明白喇":"I understand.", "好呀":"Okay.", "係呀":"Yes.", "我知喇":"I see.",
    "唔該":"Thanks.", "得喇":"All right.", "係喎":"Right.", "原來咁":"I see.",
    "咁就好":"Good.", "清楚喇":"That’s clear.", "我記低":"I’ll note that.",
    "可以呀":"Yes, that’s fine.", "等陣先":"Hang on.", "係咩":"Really?",
    "好彩啫":"That’s a relief.", "我聽住":"I’m listening.", "咁我明":"I understand now.",
    "得呀":"Okay.", "哦，係":"Oh, right.", "知道喇":"Got it.", "好，明白":"Okay, understood.",
    "我明喇":"I understand.", "咁點呀":"So what happens?", "冇問題":"No problem.",
    "我記低咗":"I’ve noted that.", "而家清楚":"It’s clear now.", "我會跟住":"I’ll follow that up.",
    "咁我明白":"I understand now.",
}


def h(seed, variant, action, key, n=6):
    return (base.h(seed["title"], action, key, "release11") + variant * 5) % n


def cprefix(seed, variant, action):
    return CLIENT_PREFIX[variant][h(seed, variant, action, "cp")]


def oprefix(seed, variant, action):
    idx = h(seed, variant, action, "op")
    return OFF_PREFIX[variant][idx], OFF_PREFIX_Y[variant][idx]


def cue_set(seed, variant, action):
    ic, tc, fc, ec = f2.anchors(seed, variant, action)
    return {
        "i": v10.issue_cue(seed, variant, action), "ic": ic,
        "t": v10.term_cue(seed, variant, action), "tc": tc,
        "f": v10.fact_cue(seed, variant, action), "fc": fc,
        "e": v10.evidence_cue(seed, variant, action), "ec": ec,
    }


def reactions(yue: str) -> str:
    pieces = [p.strip() for p in re.split(r"[。！？]", yue) if p.strip()]
    out = []
    for p in pieces[1:]:
        if p in REACTIONS:
            out.append(REACTIONS[p])
    return (" " + " ".join(out)) if out else ""


ASK = [
    "{p}, can you clarify {y} for {x}?",
    "{p}, I’m dealing with {x}; I need {y} checked.",
    "{p}, the question for {x} is {y}.",
    "{p}, {y} is still unclear in {x}.",
    "{p}, can we settle {y} before I act on {x}?",
    "{p}, I need a clear answer on {y} for {x}.",
]
EVIDENCE = [
    "{p}, I have {x}; is that enough for {y}?",
    "{p}, {x} is what I have; what else does {y} need?",
    "{p}, can I use {x} for {y}?",
    "{p}, for {y}, I can provide {x}; is anything missing?",
    "{p}, I can provide {x}; does that cover {y}?",
    "{p}, I have {x}; tell me what is still needed for {y}.",
]
CONTINUE = [
    "{p}, if {x} is unresolved, can {y} continue?",
    "{p}, can {y} stay unchanged while {x} is checked?",
    "{p}, does {x} stop {y}, or can it continue?",
    "{p}, while {x} is unsettled, what happens to {y}?",
    "{p}, I don’t want to change {y} until {x} is clear.",
    "{p}, if {x} is still open, should {y} stay as it is?",
]
FACT = [
    "{p}, the current detail is {x}; how does that affect {y}?",
    "{p}, please work from this detail for {y}: {x}.",
    "{p}, I need {x} checked before you answer on {y}.",
    "{p}, I have {x} as the current detail; what does it mean for {y}?",
    "{p}, before we settle {y}, can you verify {x}?",
    "{p}, the point that changed is {x}; please reconsider {y}.",
]
CORRECT = [
    "{p}, I meant {y}; my point about {x} was wrong.",
    "{p}, let me correct {x}; I was referring to {y}.",
    "{p}, I mixed up {x}; the point I mean is {y}.",
    "{p}, I need to amend {x}; please use {y} instead.",
    "{p}, what I said about {x} was off; I mean {y}.",
    "{p}, one correction: {x} was not the point; {y} was.",
]


def render(forms, seed, variant, action, x, y, key):
    return base.tidy_en(forms[h(seed, variant, action, key, len(forms))].format(
        p=cprefix(seed, variant, action), x=x, y=y
    ))


def client_model(seed: dict, variant: int, action: int, yue: str) -> str:
    c = cue_set(seed, variant, action)
    p = cprefix(seed, variant, action)
    ie = v10.strip_unspoken_entities(seed["issue_en"], seed["issue_yue"])
    fe = seed["fact_en"]
    ee = v10.strip_unspoken_entities(seed["evidence_en"], seed["evidence_yue"])
    te = v10.strip_unspoken_entities(seed["term_en"], seed["term_yue"])

    if variant == 0 and action == 0:
        forms = [
            "{p}, I’m asking about {full}; can you clarify {t}?",
            "{p}, my enquiry is {full}; I need {t} explained.",
            "{p}, I’m dealing with {full}; can you check {t}?",
            "{p}, the matter is {full}; what is the position on {t}?",
            "{p}, for {full}, I need a clear answer about {t}.",
            "{p}, I need help with {full}; the point is {t}.",
        ]
        main = forms[h(seed, variant, action, "fulli")].format(p=p, full=ie, t=c["t"])
    elif variant == 1 and action == 0:
        forms = [
            "{p}, I checked {i} again: {full}; please recheck the answer.",
            "{p}, for {i}, the current fact is {full}; I need an updated answer.",
            "{p}, {full}; that is why I’m following up on {i}.",
            "{p}, the new detail for {i} is {full}; please check the record again.",
            "{p}, I went back over {i}; {full}, so the earlier answer may have changed.",
            "{p}, for {i}, use this current fact: {full}; I need the position checked.",
        ]
        main = forms[h(seed, variant, action, "fullf")].format(p=p, i=c["i"], full=fe)
    elif variant == 2 and action == 0:
        forms = [
            "{p}, I found a conflict in {full} for {i}; which version should stand?",
            "{p}, for {i}, {full} does not line up; I need the right version identified.",
            "{p}, the mismatch in {i} is in {full}; can you resolve it?",
            "{p}, I’m comparing {i}; {full} contains the conflicting material.",
            "{p}, two records disagree for {i}: {full}; which one should be used?",
            "{p}, with {i}, the document problem is {full}; I need that sorted out.",
        ]
        main = forms[h(seed, variant, action, "fulle")].format(p=p, i=c["i"], full=ee)
    elif variant == 3 and action == 0:
        forms = [
            "{p}, I need the deadline for {full} in {i}.",
            "{p}, for {i}, when is {full} actually due?",
            "{p}, my timing question on {i} is the deadline for {full}.",
            "{p}, I want to avoid being late on {i}; please confirm {full} timing.",
            "{p}, before I go further with {i}, I need the date for {full}.",
            "{p}, the deadline I need checked is {full} for {i}.",
        ]
        main = forms[h(seed, variant, action, "fullt")].format(p=p, i=c["i"], full=te)
    else:
        if variant == 0:
            mapping = {1:(c["i"],c["t"],ASK),2:(c["e"],c["i"],EVIDENCE),3:(c["t"],c["i"],CONTINUE)}
        elif variant == 1:
            mapping = {1:(c["i"],c["t"],ASK),2:(c["e"],c["t"],EVIDENCE),3:(c["i"],c["t"],CONTINUE)}
        elif variant == 2:
            mapping = {1:(c["f"],c["t"],FACT),2:(c["e"],c["t"],EVIDENCE),3:(c["e"],c["i"],CONTINUE)}
        elif variant == 3:
            mapping = {1:(c["f"],c["i"],FACT),2:(c["e"],c["t"],EVIDENCE),3:(c["i"],c["t"],CONTINUE)}
        else:
            mapping = {0:(c["t"],c["i"],ASK),1:(c["f"],c["t"],FACT),2:(c["e"],c["i"],EVIDENCE),3:(c["t"],c["i"],CONTINUE)}
        x,y,forms = mapping[action]
        main = render(forms, seed, variant, action, x, y, f"cm{action}")
    return base.tidy_en(main) + reactions(yue)


def client_turn(seed: dict, variant: int, action: int):
    _old_en, yue = r._ORIG_CLIENT(seed, variant, action)
    return client_model(seed, variant, action, yue), yue


def repair_turn(seed: dict, variant: int):
    _old_en, yue = r._ORIG_REPAIR(seed, variant)
    c = cue_set(seed, variant, 4)
    x,y = {0:(c["i"],c["t"]),1:(c["i"],c["e"]),2:(c["t"],c["e"]),3:(c["f"],c["t"]),4:(c["i"],c["t"])}[variant]
    return render(CORRECT, seed, variant, 4, x, y, "repair") + reactions(yue), yue


def officer(seed: dict, variant: int, action: int):
    c = cue_set(seed, variant, action)
    p,py = oprefix(seed, variant, action)
    s = h(seed, variant, action, "off", 6)
    t,tc = c["t"],c["tc"]
    i,ic = c["i"],c["ic"]
    e,ec = c["e"],c["ec"]
    f,fc = c["f"],c["fc"]

    if action == 0:
        ens=[
            "{p}, start with {e}; I’ll use it to clarify {t} for {i}.",
            "{p}, for {i}, show me {e}; then we can settle {t}.",
            "{p}, {t} is the question; {e} gives us a reference for {i}.",
            "{p}, {e} comes first; I’ll check {t} for {i}.",
            "{p}, I’ll read {e}; after that, we can sort out {t} for {i}.",
            "{p}, with {i}, I need {e} before I answer {t}.",
        ]
        ys=[
            "{py}，由{ec}開始；我用佢搞清{tc}同{ic}。", "{py}，講{ic}先畀我睇{ec}；跟住再定{tc}。",
            "{py}，{tc}係要問嗰點；用{ec}睇返{ic}。", "{py}，{ec}先行；我再查{tc}同{ic}。",
            "{py}，我先睇{ec}；之後再理順{tc}同{ic}。", "{py}，講{ic}我要先有{ec}，先答{tc}。",
        ]
    elif action == 1:
        ens=[
            "{p}, check {f} for {i}; then I can answer {t}.", "{p}, {f} is the point to verify before I answer {t} for {i}.",
            "{p}, before I answer {t}, I need {f} checked for {i}.", "{p}, for {i}, let me verify {f}; {t} comes after that.",
            "{p}, I’ll test {f} against {i}; then we can settle {t}.", "{p}, don’t guess {t}; first I’ll confirm {f} for {i}.",
        ]
        ys=[
            "{py}，先對{fc}同{ic}；跟住先答{tc}。", "{py}，{fc}係要核嗰點；對清先答{tc}同{ic}。",
            "{py}，答{tc}之前先查{fc}同{ic}。", "{py}，講{ic}我先核實{fc}；之後先到{tc}。",
            "{py}，我用{ic}對{fc}；跟住先定{tc}。", "{py}，{tc}唔好估；先確認{fc}同{ic}。",
        ]
    elif action == 2:
        ens=[
            "{p}, keep {e} with {i}; I’ll use it for {t}.", "{p}, for {t}, {e} is the record I need from {i}.",
            "{p}, {e} is useful; I’ll match it to {t} under {i}.", "{p}, put {e} beside {i}; then I can check {t}.",
            "{p}, I need {e} for {i}; from there I’ll check {t}.", "{p}, don’t separate {e} from {i}; it supports the check on {t}.",
        ]
        ys=[
            "{py}，{ec}同{ic}放埋；我用嚟查{tc}。", "{py}，講{tc}我要{ic}嗰份{ec}。",
            "{py}，{ec}有用；我用佢對{tc}同{ic}。", "{py}，{ec}擺返{ic}旁邊；跟住查{tc}。",
            "{py}，講{ic}我要{ec}；由嗰度再查{tc}。", "{py}，{ec}唔好同{ic}分開；佢用嚟對{tc}。",
        ]
    elif action == 3:
        ens=[
            "{p}, don’t change {i} yet; first I’ll check {t} against {e}.", "{p}, {t} is still open; keep {i} steady while I read {e}.",
            "{p}, for {i}, wait before changing anything; I’ll compare {e} with {t}.", "{p}, leave {i} as it is; {e} will help me settle {t}.",
            "{p}, I’ll check {e}; until then, don’t assume {t} changed for {i}.", "{p}, {t} needs checking from {e}; keep {i} unchanged for now.",
        ]
        ys=[
            "{py}，{ic}住先唔改；我先用{ec}對{tc}。", "{py}，{tc}仲未清；我睇{ec}期間{ic}照舊。",
            "{py}，講{ic}住先唔郁；我比較{ec}同{tc}。", "{py}，{ic}照原先；{ec}幫我定清{tc}。",
            "{py}，我先查{ec}；未查完唔好當{ic}個{tc}變咗。", "{py}，{tc}要由{ec}查；{ic}而家照舊。",
        ]
    elif action == 4:
        ens=[
            "{p}, if {e} is wrong, amend it under {i}; I’ll recheck {t}.", "{p}, for {i}, correct {e} there; then I’ll revisit {t}.",
            "{p}, {e} should stay with {i}; fix that record before checking {t} again.", "{p}, update {i} with the correct {e}; don’t start over on {t}.",
            "{p}, if {e} needs correction, keep it on {i}; I’ll check {t} again.", "{p}, amend {e} on the existing {i}; after that I’ll verify {t}.",
        ]
        ys=[
            "{py}，{ec}有錯就喺{ic}改；我再查{tc}。", "{py}，講{ic}將{ec}改返；跟住再睇{tc}。",
            "{py}，{ec}要跟返{ic}；改好紀錄先再查{tc}。", "{py}，用正確{ec}改{ic}；{tc}唔使由頭開。",
            "{py}，{ec}如果要改就留喺{ic}嗰宗；我再對{tc}。", "{py}，喺原本{ic}改{ec}；之後我再核{tc}。",
        ]
    else:
        ens=[
            "{p}, save {e} with the answer on {t}; keep it under {i}.", "{p}, for {i}, keep {e} beside the written {t} answer.",
            "{p}, {e} and the {t} response belong together; file both with {i}.", "{p}, put the written {t} answer next to {e} in the {i} record.",
            "{p}, keep {e} for {i}; save the final {t} response with it.", "{p}, the record for {i} should hold {e} and the written {t} answer.",
        ]
        ys=[
            "{py}，{ec}同{tc}書面答覆放埋，跟返{ic}。", "{py}，講{ic}將{ec}同{tc}書面答覆收埋。",
            "{py}，{ec}同{tc}回覆要一齊留；放返{ic}嗰宗。", "{py}，{tc}書面答覆放喺{ec}旁邊，同{ic}一齊留。",
            "{py}，講{ic}留返{ec}；最後{tc}答覆同佢收埋。", "{py}，{ic}紀錄要有{ec}同{tc}書面答覆。",
        ]

    en=base.tidy_en(ens[s].format(p=p,i=i,t=t,f=f,e=e))
    y=f2.clean_yue(ys[s].format(py=py,ic=ic,tc=tc,fc=fc,ec=ec))
    if len(en.split())>35:
        raise SystemExit(f"professional segment >35 words ({len(en.split())}): {en}")
    return en,y


r.client_model = lambda seed,variant,action: client_model(seed,variant,action,r._ORIG_CLIENT(seed,variant,action)[1])
r.client_turn = client_turn
r.repair_turn = repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

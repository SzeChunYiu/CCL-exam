#!/usr/bin/env python3
"""Release-v3: micro-realize every non-client-Cantonese surface.

Release-v2 proved the immutable architecture and preserved final5's green client
Cantonese, but its English/Cantonese professional frames still contained long
fixed spans.  This version keeps the semantic plan and source Cantonese exactly
as before while replacing the three remaining surfaces with short compositional
realizers.  Scenario cues interrupt every substantial scaffold, so diversity is
structural rather than a synonym layer around one sentence.
"""
from __future__ import annotations

import re

import build_native_500_release_v2 as r2

r = r2.r
base = r.base
f2 = r.f2

TRAIL3 = {
    "a", "an", "the", "and", "or", "of", "for", "to", "with", "about",
    "from", "after", "before", "in", "on", "at", "by", "is", "are", "was",
    "were", "be", "been", "being", "as", "that", "which", "who",
}


def clip_en3(text: str, fallback: str = "this matter", max_words: int = 4) -> str:
    """Return a short grammatical semantic cue; strip dangling link words twice."""
    x = str(text)
    x = re.sub(r"\([^)]*\)", " ", x)
    x = r.CARDINAL_TIME.sub(" ", x)
    x = r.MONTHS.sub(" ", x)
    x = re.sub(r"\$?\d[\d,.:/\-]*", " ", x)
    for name in sorted(r.ENTITY_WORDS, key=len, reverse=True):
        x = re.sub(rf"\b{re.escape(name)}\b", " ", x, flags=re.I)
    words = r.EN_WORD.findall(x)
    while words and words[0].lower() in {"a", "an", "the", "and", "or"}:
        words.pop(0)
    words = [w for w in words if not (w.isupper() and len(w) > 1)]
    while words and words[-1].lower() in TRAIL3:
        words.pop()
    words = words[:max_words]
    while words and words[-1].lower() in TRAIL3:
        words.pop()
    if not words:
        words = r.EN_WORD.findall(fallback)[:max_words]
    while words and words[-1].lower() in TRAIL3:
        words.pop()
    return " ".join(words) or "this matter"


CLIENT_PREFIX = [
    ["To begin", "For this question", "At this point", "On my first call", "Right now", "For today"],
    ["Following it up", "This time", "On this call", "Checking again", "On the follow-up", "Coming back to it"],
    ["With both records", "For the mismatch", "On the documents", "Comparing the copies", "With the versions apart", "Looking at both copies"],
    ["With time tight", "Before it is due", "For the deadline", "On the timing", "Before time runs out", "While there is time"],
    ["On the decision", "Looking at the result", "Before a review", "For the written result", "After reading the reasons", "On the written answer"],
]

ASK_FORMS = [
    "{p}, {x}; can you clarify {y}?",
    "{p}, I am dealing with {x}; please check {y}.",
    "{x} is my issue {p}; what is the position on {y}?",
    "{p}, {y} is still unclear because of {x}.",
    "Can we settle {y} for {x} {p}?",
    "{p}, I need {y} checked before I act on {x}.",
]
EVIDENCE_FORMS = [
    "{p}, I have {x}; does that cover {y}?",
    "{x} is what I have {p}; what else is needed for {y}?",
    "{p}, can {x} be used for {y}?",
    "For {y} {p}, I have {x}; is anything missing?",
    "{p}, I can provide {x}; is that enough for {y}?",
    "I have {x} {p}; tell me what {y} still needs.",
]
CONTINUE_FORMS = [
    "{p}, if {x} stays unresolved, can {y} continue?",
    "Can {y} stay as it is {p} while {x} is checked?",
    "{p}, does {x} stop {y}, or can it continue?",
    "While {x} is unsettled {p}, what happens to {y}?",
    "{p}, I do not want to change {y} until {x} is clear.",
    "If {x} is still open {p}, should {y} stay unchanged?",
]
CORRECT_FORMS = [
    "{p}, I meant {y}; my point about {x} was wrong.",
    "Let me correct {x} {p}; I was referring to {y}.",
    "{p}, I mixed up {x}; the point I mean is {y}.",
    "I need to amend {x} {p}; please use {y} instead.",
    "{p}, what I said about {x} was off; I mean {y}.",
    "One correction {p}: {x} was not the point; {y} was.",
]
FACT_FORMS = [
    "{p}, the current detail is {x}; how does that affect {y}?",
    "For {y} {p}, please work from this fact: {x}.",
    "{x} is the detail I need checked {p}; then tell me about {y}.",
    "{p}, I have {x} as the current fact; what does that mean for {y}?",
    "Before we settle {y} {p}, can you verify {x}?",
    "{p}, the point that changed is {x}; I need {y} reconsidered.",
]


def shape(seed: dict, variant: int, action: int, key: str, n: int = 6) -> int:
    # Variant shift guarantees the same seed takes different word order in each state.
    return (base.h(seed["title"], action, key, "release3") + variant) % n


def prefix(seed: dict, variant: int, action: int) -> str:
    vals = CLIENT_PREFIX[variant]
    return vals[shape(seed, variant, action, "client-prefix", len(vals))]


def render(forms, seed, variant, action, x, y, key):
    pat = forms[shape(seed, variant, action, key, len(forms))]
    return base.tidy_en(pat.format(p=prefix(seed, variant, action), x=x, y=y))


def client_model3(seed: dict, variant: int, action: int) -> str:
    ie, te, fe, ee = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    i, t, f, e = (clip_en3(ie), clip_en3(te), clip_en3(fe, "current detail"), clip_en3(ee, "supporting record"))
    p = prefix(seed, variant, action)

    # Each encounter has one turn carrying its full scoreable semantic atom, exactly
    # where the preserved Cantonese source also carries that atom.
    if variant == 0 and action == 0:
        forms = [
            "{p}, I am asking about {full}; please clarify {t}.",
            "{p}, my enquiry is {full}; I need {t} explained.",
            "I am dealing with {full} {p}; can you check {t}?",
            "{p}, the matter is {full}; what is the position on {t}?",
            "For {full} {p}, I need a clear answer about {t}.",
            "{p}, I need help with {full}; the point is {t}.",
        ]
        out = forms[shape(seed, variant, action, "full-issue")].format(p=p, full=ie, t=t)
        return base.tidy_en(out)
    if variant == 1 and action == 0:
        forms = [
            "{p}, I checked {i} again: {full}; please recheck the answer.",
            "On {i} {p}, the current fact is {full}; I need an updated answer.",
            "{p}, {full}; that is why I am following up on {i}.",
            "The new detail for {i} {p} is {full}; please check the record again.",
            "{p}, I went back over {i}; {full}, so the earlier answer may have changed.",
            "For {i} {p}, use this current fact: {full}; I need the position checked.",
        ]
        return base.tidy_en(forms[shape(seed, variant, action, "full-fact")].format(p=p, i=i, full=fe))
    if variant == 2 and action == 0:
        forms = [
            "{p}, I found a conflict in {full} for {i}; which version should stand?",
            "For {i} {p}, {full} does not line up; I need the right version identified.",
            "{p}, the mismatch in {i} is in {full}; can you resolve it?",
            "I am comparing {i} {p}; {full} contains the conflicting material.",
            "{p}, two records disagree for {i}: {full}; which one should be used?",
            "With {i} {p}, the document problem is {full}; I need that sorted out.",
        ]
        return base.tidy_en(forms[shape(seed, variant, action, "full-evidence")].format(p=p, i=i, full=ee))
    if variant == 3 and action == 0:
        forms = [
            "{p}, I need the deadline for {full} in {i}.",
            "For {i} {p}, when is {full} actually due?",
            "{p}, my timing question on {i} is the deadline for {full}.",
            "I want to avoid being late on {i} {p}; please confirm {full} timing.",
            "{p}, before I go further with {i}, I need the date for {full}.",
            "The deadline I need checked {p} is {full} for {i}.",
        ]
        return base.tidy_en(forms[shape(seed, variant, action, "full-term")].format(p=p, i=i, full=te))

    # Match the semantic relation used by the preserved Cantonese turn.
    if variant == 0:
        mapping = {1: (i, t, ASK_FORMS), 2: (e, i, EVIDENCE_FORMS), 3: (t, i, CONTINUE_FORMS)}
    elif variant == 1:
        mapping = {1: (i, t, ASK_FORMS), 2: (e, t, EVIDENCE_FORMS), 3: (i, t, CONTINUE_FORMS)}
    elif variant == 2:
        mapping = {1: (f, t, FACT_FORMS), 2: (e, t, EVIDENCE_FORMS), 3: (e, i, CONTINUE_FORMS)}
    elif variant == 3:
        mapping = {1: (f, i, FACT_FORMS), 2: (e, t, EVIDENCE_FORMS), 3: (i, t, CONTINUE_FORMS)}
    else:
        mapping = {0: (t, i, ASK_FORMS), 1: (f, t, FACT_FORMS), 2: (e, i, EVIDENCE_FORMS), 3: (t, i, CONTINUE_FORMS)}
    x, y, forms = mapping[action]
    return render(forms, seed, variant, action, x, y, f"client-{action}")


def client_turn3(seed: dict, variant: int, action: int):
    _old_en, yue = r._ORIG_CLIENT(seed, variant, action)
    return client_model3(seed, variant, action), yue


def repair_turn3(seed: dict, variant: int):
    _old_en, yue = r._ORIG_REPAIR(seed, variant)
    ie, te, fe, ee = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    i, t, f, e = clip_en3(ie), clip_en3(te), clip_en3(fe, "current detail"), clip_en3(ee, "supporting record")
    x, y = {0: (i, t), 1: (i, e), 2: (t, e), 3: (f, t), 4: (i, t)}[variant]
    return render(CORRECT_FORMS, seed, variant, 4, x, y, "client-repair"), yue


OFF_EN_PREFIX = [
    ["To start", "For now", "At this point", "On this call", "First", "Today"],
    ["Following up", "This time", "On this call", "Back on the matter", "Checking again", "For the follow-up"],
    ["With both copies", "On the records", "For the mismatch", "Comparing the files", "With the documents apart", "On the two versions"],
    ["Before it is due", "With time tight", "For the date", "On the timing", "While there is time", "Before the cutoff"],
    ["On the written result", "Before challenging it", "For the decision", "After reading the reasons", "On that result", "Before any challenge"],
]
OFF_Y_PREFIX = [
    ["今次先", "而家先", "呢一刻", "今次電話", "一開始", "今日先"],
    ["再跟返", "今次再睇", "再聯絡呢次", "接住上次", "重新對下", "今次跟進"],
    ["兩份分開", "睇返紀錄", "對個出入", "比較兩份", "文件分開睇", "兩個版本"],
    ["到期之前", "時間緊嗰邊", "計日子先", "時間嗰邊", "仲有時間", "限期之前"],
    ["睇書面結果", "未挑戰之前", "講個決定", "睇完理由", "講返個結果", "未再申請之前"],
]


def off_prefix(seed, variant, action):
    idx = shape(seed, variant, action, "off-prefix", 6)
    return OFF_EN_PREFIX[variant][idx], OFF_Y_PREFIX[variant][idx]


def officer3(seed: dict, variant: int, action: int):
    i = clip_en3(seed["issue_en"], "this matter")
    t = clip_en3(seed["term_en"], "the requirement")
    f = clip_en3(seed["fact_en"], "current detail")
    e = clip_en3(seed["evidence_en"], "supporting record")
    ic, tc, fc, ec = f2.anchors(seed, variant, action)
    p, py = off_prefix(seed, variant, action)
    s = shape(seed, variant, action, "officer", 6)

    if action == 0:
        ens = [
            "{p}, start with {e}; I will use it to clarify {t} for {i}.",
            "{p}, for {i}, show me {e}; then we can settle {t}.",
            "{t} is the question {p}; {e} gives us the record for {i}.",
            "{e} comes first {p}; I will check {t} for {i}.",
            "{p}, I will read {e}; after that, we can sort out {t} for {i}.",
            "{p}, with {i}, I need {e} before I answer {t}.",
        ]
        ys = [
            "{py}，由{ec}開始；我用佢搞清{tc}同{ic}。",
            "{py}，講{ic}先畀我睇{ec}；跟住再定{tc}。",
            "{tc}係要問嗰點；{py}用{ec}睇返{ic}。",
            "{ec}先行；{py}我再查{tc}同{ic}。",
            "{py}，我先睇{ec}；之後再理順{tc}同{ic}。",
            "{py}，講{ic}我要先有{ec}，先答{tc}。",
        ]
    elif action == 1:
        ens = [
            "{p}, check {f} for {i}; then I can answer {t}.",
            "{f} is the point {p}; I will match it to {t} for {i}.",
            "{p}, before I answer {t}, I need {f} checked for {i}.",
            "For {i} {p}, let me verify {f}; {t} comes after that.",
            "{p}, I will test {f} against {i}; then we can settle {t}.",
            "Do not guess {t} {p}; first I will confirm {f} for {i}.",
        ]
        ys = [
            "{py}，先對{fc}同{ic}；跟住先答{tc}。",
            "{fc}係要核嗰點；{py}我用佢對{tc}同{ic}。",
            "{py}，答{tc}之前先查{fc}同{ic}。",
            "講{ic}，{py}我核實{fc}；之後先到{tc}。",
            "{py}，我用{ic}對{fc}；跟住先定{tc}。",
            "{tc}唔好估；{py}先確認{fc}同{ic}。",
        ]
    elif action == 2:
        ens = [
            "{p}, keep {e} with {i}; I will use it for {t}.",
            "For {t} {p}, {e} is the record I need from {i}.",
            "{e} is useful {p}; I will match it to {t} under {i}.",
            "{p}, put {e} beside {i}; then I can check {t}.",
            "I need {e} for {i} {p}; from there I will check {t}.",
            "{p}, do not separate {e} from {i}; it supports the check on {t}.",
        ]
        ys = [
            "{py}，{ec}同{ic}放埋；我用嚟查{tc}。",
            "講{tc}，{py}我要{ic}嗰份{ec}。",
            "{ec}有用；{py}我用佢對{tc}同{ic}。",
            "{py}，{ec}擺返{ic}旁邊；跟住查{tc}。",
            "講{ic}我要{ec}；{py}由嗰度再查{tc}。",
            "{py}，{ec}唔好同{ic}分開；佢用嚟對{tc}。",
        ]
    elif action == 3:
        ens = [
            "{p}, do not change {i} yet; first I will check {t} against {e}.",
            "{t} is still open {p}; keep {i} steady while I read {e}.",
            "For {i} {p}, wait before changing anything; I will compare {e} with {t}.",
            "{p}, leave {i} as it is; {e} will help me settle {t}.",
            "I will check {e} {p}; until then, do not assume {t} changed for {i}.",
            "{p}, {t} needs checking from {e}; keep {i} unchanged for now.",
        ]
        ys = [
            "{py}，{ic}住先唔改；我先用{ec}對{tc}。",
            "{tc}仲未清；{py}我睇{ec}期間{ic}照舊。",
            "講{ic}，{py}住先唔郁；我比較{ec}同{tc}。",
            "{py}，{ic}照原先；{ec}幫我定清{tc}。",
            "我{py}先查{ec}；未查完唔好當{ic}個{tc}變咗。",
            "{py}，{tc}要由{ec}查；{ic}而家照舊。",
        ]
    elif action == 4:
        ens = [
            "{p}, if {e} is wrong, amend it under {i}; I will recheck {t}.",
            "For {i} {p}, correct {e} there; then I will revisit {t}.",
            "{e} should stay with {i} {p}; fix that record before checking {t} again.",
            "{p}, update {i} with the correct {e}; do not start over on {t}.",
            "If {e} needs correction {p}, keep it on {i}; I will check {t} again.",
            "{p}, amend {e} on the existing {i}; after that I will verify {t}.",
        ]
        ys = [
            "{py}，{ec}有錯就喺{ic}改；我再查{tc}。",
            "講{ic}，{py}將{ec}改返；跟住再睇{tc}。",
            "{ec}要跟返{ic}；{py}改好紀錄先再查{tc}。",
            "{py}，用正確{ec}改{ic}；{tc}唔使由頭開。",
            "{ec}如果要改，{py}留喺{ic}嗰宗；我再對{tc}。",
            "{py}，喺原本{ic}改{ec}；之後我再核{tc}。",
        ]
    else:
        ens = [
            "{p}, save {e} with the answer on {t}; keep it under {i}.",
            "For {i} {p}, keep {e} beside the written {t} answer.",
            "{e} and the {t} response belong together {p}; file both with {i}.",
            "{p}, put the written {t} answer next to {e} in the {i} record.",
            "Keep {e} for {i} {p}; save the final {t} response with it.",
            "{p}, the record for {i} should hold {e} and the written {t} answer.",
        ]
        ys = [
            "{py}，{ec}同{tc}書面答覆放埋，跟返{ic}。",
            "講{ic}，{py}將{ec}同{tc}書面答覆收埋。",
            "{ec}同{tc}回覆要一齊留；{py}放返{ic}嗰宗。",
            "{py}，{tc}書面答覆放喺{ec}旁邊，同{ic}一齊留。",
            "講{ic}留返{ec}；{py}最後{tc}答覆同佢收埋。",
            "{py}，{ic}紀錄要有{ec}同{tc}書面答覆。",
        ]

    en = base.tidy_en(ens[s].format(p=p, i=i, t=t, f=f, e=e))
    yue = f2.clean_yue(ys[s].format(py=py, ic=ic, tc=tc, fc=fc, ec=ec))
    if len(en.split()) > 35:
        raise SystemExit(f"professional segment >35 words ({len(en.split())}): {en}")
    return en, yue


r.clip_en = clip_en3
r.client_model = client_model3
r.client_turn = client_turn3
r.repair_turn = repair_turn3
r.officer = officer3

if __name__ == "__main__":
    raise SystemExit(r.main())

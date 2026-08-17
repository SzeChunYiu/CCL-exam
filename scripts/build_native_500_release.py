#!/usr/bin/env python3
"""Build the release 500-dialogue bank without extending the saturated finalN chain.

The client Cantonese from final5 is already release-quality and is preserved
byte-for-byte at turn level.  This builder replaces only the three surfaces the
whole-dialogue audit found to be templated:

* professional English source turns;
* professional Cantonese model turns;
* English models for Cantonese client turns.

The new realizers are compositional.  Long fixed scaffolds are avoided: scenario
cues interrupt every substantive sentence, while encounter state and action vary
word order and pragmatic framing.  The builder writes an immutable candidate by
default; tracked production data is touched only with --promote.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import build_native_500_final5 as f5

f4 = f5.f4
f2 = f4.f2
v11 = f2.v11
base = f2.base
ROOT = Path(__file__).resolve().parents[1]

# Capture the green final5 client Cantonese before replacing the English model.
_ORIG_CLIENT = f2.client_turn
_ORIG_REPAIR = f2.repair_turn

ENTITY_WORDS = [
    "Services Australia", "MyAgedCare", "ImmiAccount", "Centrelink", "Medicare",
    "myGov", "Fair Work", "VEVO", "NDIS", "AFCA", "NCAT", "ATO", "GST",
    "BAS", "ABN", "TFN", "PBS", "USI", "OSHC", "CTP", "BSB", "HECS-HELP",
    "TAFE", "AVO", "AMEP", "CCS",
]
CARDINAL_TIME = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
    r"(?:business\s+days?|working\s+days?|days?|weeks?|fortnights?|months?|years?|hours?|minutes?)\b",
    re.I,
)
MONTHS = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\b", re.I,
)
EN_WORD = re.compile(r"[A-Za-z]+(?:[-’][A-Za-z]+)?")
TRAILING = {"a", "an", "the", "of", "for", "to", "with", "about", "from", "after", "before", "in", "on", "at", "by"}


def hp(seed: dict, variant: int, action: int, key: str, vals):
    return vals[base.h(seed["title"], variant, action, key, "release") % len(vals)]


def clip_en(text: str, fallback: str = "this matter", max_words: int = 6) -> str:
    """Short semantic cue with no standalone 8-word fingerprint or scoreable number."""
    x = str(text)
    x = re.sub(r"\([^)]*\)", " ", x)
    x = CARDINAL_TIME.sub(" ", x)
    x = MONTHS.sub(" ", x)
    x = re.sub(r"\$?\d[\d,.:/\-]*", " ", x)
    for name in sorted(ENTITY_WORDS, key=len, reverse=True):
        x = re.sub(rf"\b{re.escape(name)}\b", " ", x, flags=re.I)
    words = EN_WORD.findall(x)
    while words and words[0].lower() in {"a", "an", "the"}:
        words.pop(0)
    words = [w for w in words if not (w.isupper() and len(w) > 1)]
    while words and words[-1].lower() in TRAILING:
        words.pop()
    if not words:
        words = EN_WORD.findall(fallback)
    return " ".join(words[:max_words])


PAIR_PATTERNS = [
    "I am trying to sort out {x}; the point I need clarified is {y}.",
    "My concern is {x}, and I need a clear answer about {y}.",
    "Because of {x}, I want to check exactly how {y} applies.",
    "Could we go over {y} in relation to {x}? I am not clear on that point.",
    "The part I am stuck on is {y}, in the context of {x}.",
    "With {x} in mind, can you clarify {y} for me?",
    "I need to understand {y} before I decide what to do about {x}.",
    "What I need checked is {y}, given what is happening with {x}.",
    "I am asking about {x}; the uncertain part for me is {y}.",
    "Can you help me reconcile {x} with {y}? That is my question.",
    "I want to be sure about {y}, because {x} is the issue I am dealing with.",
    "For {x}, the thing I still need explained is {y}.",
    "The question for me comes from {x}; I need {y} made clear.",
    "I am dealing with {x} and want to know where {y} leaves me.",
    "Please check {y} for me, because it affects how I handle {x}.",
    "What I cannot settle from the information I have is {y} for {x}.",
    "I understand the general position on {x}; what I still need is an answer on {y}.",
    "The issue I am following is {x}, but the part I need confirmed is {y}.",
    "I want to deal with {x} properly, so I need {y} checked first.",
    "Could you clarify {y} while we are dealing with {x}?",
    "For me, {x} turns on one question: what is the position on {y}?",
    "I have a question about {y} arising from {x}; can we check that point?",
    "Before I act on {x}, I want a definite answer about {y}.",
    "The practical question in {x} is {y}; that is what I need help with.",
]

FACT_PATTERNS = [
    "I checked {issue} again and found this: {fact}; that is why I am asking about {term}.",
    "The detail I need to work from is {fact}; I want to know what that means for {issue} and {term}.",
    "For {issue}, the factual point is {fact}; can you check the position on {term} from there?",
    "What changed my question about {issue} is this fact: {fact}; I need {term} checked against it.",
    "I am following up on {issue} because {fact}; please tell me how that affects {term}.",
    "The record now shows {fact}; I need to know whether that changes the answer on {term} for {issue}.",
    "My question on {term} comes from the fact that {fact}; the matter is {issue}.",
    "Before I do anything else about {issue}, I need {term} considered with this fact: {fact}.",
    "The point I may have had wrong is {fact}; I want the answer on {term} for {issue} checked again.",
    "I am not relying on the earlier assumption about {issue}; the current fact is {fact}, so what happens with {term}?",
    "For the present {issue} question, use this detail: {fact}; I need the position on {term} confirmed.",
    "The factual basis for my {issue} enquiry is {fact}; can we verify {term} from that?",
]

CORRECTION_PATTERNS = [
    "I need to correct what I said about {x}; the point I meant was {y}.",
    "Let me correct that: I was talking about {y}, not the way I first described {x}.",
    "I mixed that up when I mentioned {x}; what I actually need checked is {y}.",
    "I should correct the last point on {x}; I meant {y}.",
    "What I just said about {x} was not quite right; the relevant point is {y}.",
    "I need to put that more accurately: for {x}, I am referring to {y}.",
    "I said the wrong thing about {x}; please use {y} as the point to check.",
    "Let me restate the issue around {x}: it is {y} that I mean.",
    "I want to fix one detail in what I said about {x}; the correct reference is {y}.",
    "There is one correction to my explanation of {x}; I am asking about {y}.",
    "I used the wrong description for {x}; what I meant to identify was {y}.",
    "Please amend what I just said about {x}; the question should be about {y}.",
]


def pair_model(seed: dict, variant: int, action: int, x: str, y: str) -> str:
    pat = hp(seed, variant, action, "client-pair", PAIR_PATTERNS)
    return base.tidy_en(pat.format(x=x, y=y))


def fact_model(seed: dict, variant: int, action: int, issue: str, fact: str, term: str) -> str:
    pat = hp(seed, variant, action, "client-fact", FACT_PATTERNS)
    return base.tidy_en(pat.format(issue=issue, fact=fact, term=term))


def client_model(seed: dict, variant: int, action: int) -> str:
    ie, te, fe, ee = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    # Match the semantic anchors actually used by the green final5 Cantonese turn.
    if variant == 0:
        pairs = [(ie, te), (ie, te), (ee, ie), (te, ie)]
        x, y = pairs[action]
        return pair_model(seed, variant, action, x, y)
    if variant == 1:
        if action == 0:
            return fact_model(seed, variant, action, ie, fe, te)
        pairs = [(ie, te), (ee, te), (ie, te)]
        x, y = pairs[action - 1]
        return pair_model(seed, variant, action, x, y)
    if variant == 2:
        if action == 1:
            return fact_model(seed, variant, action, ie, fe, te)
        pairs = {0: (ee, ie), 2: (ee, te), 3: (ee, ie)}
        return pair_model(seed, variant, action, *pairs[action])
    if variant == 3:
        if action == 1:
            return fact_model(seed, variant, action, ie, fe, te)
        pairs = {0: (te, ie), 2: (ee, te), 3: (ie, te)}
        return pair_model(seed, variant, action, *pairs[action])
    if action == 1:
        return fact_model(seed, variant, action, ie, fe, te)
    pairs = {0: (te, ie), 2: (ee, ie), 3: (te, ie)}
    return pair_model(seed, variant, action, *pairs[action])


def client_turn(seed: dict, variant: int, action: int) -> tuple[str, str]:
    _old_en, yue = _ORIG_CLIENT(seed, variant, action)
    return client_model(seed, variant, action), yue


def repair_turn(seed: dict, variant: int) -> tuple[str, str]:
    _old_en, yue = _ORIG_REPAIR(seed, variant)
    ie, te, fe, ee = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    if variant == 3:
        # The Cantonese repair explicitly corrects the timing/factual basis.
        return fact_model(seed, variant, 4, ie, fe, te), yue
    x, y = {
        0: (ie, te),
        1: (ie, ee),
        2: (te, ee),
        4: (ie, te),
    }[variant]
    pat = hp(seed, variant, 4, "repair-en", CORRECTION_PATTERNS)
    return base.tidy_en(pat.format(x=x, y=y)), yue


START_EN = ["start with", "look at", "check", "use", "compare", "read through"]
START_Y = ["先睇", "先對", "先查", "先用", "先比較", "先跟"]
GOAL_EN = ["pin down", "sort out", "clarify", "trace", "work through", "settle"]
GOAL_Y = ["搞清", "理順", "講清", "追返", "逐樣睇", "定清"]
VERIFY_EN = ["verify", "check", "confirm", "recheck", "match", "test"]
VERIFY_Y = ["核實", "對清", "查清", "再對", "對返", "驗清"]
STATE_EN = ["at the first enquiry", "during this follow-up", "while the records disagree", "before the deadline", "before any review"]
STATE_Y = ["今次初問", "今次跟進", "文件有出入嗰陣", "限期之前", "覆核之前"]


def officer(seed: dict, variant: int, action: int) -> tuple[str, str]:
    ie = clip_en(seed["issue_en"], seed["topic"] + " matter")
    te = clip_en(seed["term_en"], seed["topic"] + " requirement")
    fe = clip_en(seed["fact_en"], "current factual detail")
    ee = clip_en(seed["evidence_en"], "supporting record")
    ic, tc, fc, ec = f2.anchors(seed, variant, action)
    state, state_y = STATE_EN[variant], STATE_Y[variant]
    sv = hp(seed, variant, action, "sv", START_EN)
    svy = hp(seed, variant, action, "svy", START_Y)
    gv = hp(seed, variant, action, "gv", GOAL_EN)
    gvy = hp(seed, variant, action, "gvy", GOAL_Y)
    vv = hp(seed, variant, action, "vv", VERIFY_EN)
    vvy = hp(seed, variant, action, "vvy", VERIFY_Y)
    shape = base.h(seed["title"], variant, action, "officer-shape-release") % 6

    if action == 0:
        en = [
            f"For {ie}, I will {sv} {ee}; then we can {gv} {te} {state}.",
            f"{ee} gives us the first reference for {ie}; I will {gv} {te} {state}.",
            f"On {ie}, {te} is the point to {gv}; I will {sv} {ee} {state}.",
            f"I will {sv} {ee} {state}; that should {gv} {te} for {ie}.",
            f"Before we go further with {ie}, let me {sv} {ee} and {gv} {te} {state}.",
            f"{state}, I will {sv} {ee} for {ie} so we can {gv} {te}.",
        ][shape]
        y = [
            f"講{ic}，我{svy}{ec}；{state_y}再{gvy}{tc}。",
            f"{ec}做第一個參考；{ic}嗰邊{state_y}{gvy}{tc}。",
            f"{ic}而家要{gvy}{tc}；{state_y}我{svy}{ec}。",
            f"我{state_y}{svy}{ec}，跟住用嚟{gvy}{tc}同{ic}。",
            f"{ic}未再行之前，我{svy}{ec}同{gvy}{tc}。",
            f"{state_y}先用{ec}睇{ic}，之後{gvy}{tc}。",
        ][shape]
    elif action == 1:
        en = [
            f"For {ie}, I need to {vv} {fe}; {te} comes after that {state}.",
            f"{state}, I will {vv} {fe} before I give a position on {te} for {ie}.",
            f"The point to {vv} for {ie} is {fe}; only then will I settle {te} {state}.",
            f"I will not guess on {te}: first I will {vv} {fe} for {ie} {state}.",
            f"Before I answer {te} for {ie}, let me {vv} {fe} {state}.",
            f"{fe} is what I will {vv} {state}; that keeps the answer on {te} tied to {ie}.",
        ][shape]
        y = [
            f"講{ic}，我要{vvy}{fc}；{state_y}先再答{tc}。",
            f"{state_y}我會{vvy}{fc}，之後先講{ic}嗰邊{tc}。",
            f"{ic}要{vvy}嘅係{fc}；搞清先定{tc}。",
            f"{tc}我唔估；{state_y}先{vvy}{fc}同{ic}。",
            f"答{tc}之前，我{state_y}{vvy}{fc}，再跟{ic}。",
            f"{fc}我會{state_y}{vvy}；咁{tc}答覆先跟得返{ic}。",
        ][shape]
    elif action == 2:
        en = [
            f"For {ie}, {ee} is the record I want first; I will match it to {te} {state}.",
            f"I will {sv} {ee} for {ie} {state}; that is the material I need for {te}.",
            f"{state}, keep {ee} with {ie}; I will use it to {gv} {te}.",
            f"The useful record for {te} is {ee}; I will read it against {ie} {state}.",
            f"Do not separate {ee} from {ie}; {state}, it is what I will use to check {te}.",
            f"I need {ee} beside the {ie} record {state}; from there I can {gv} {te}.",
        ][shape]
        y = [
            f"{ic}今次先睇{ec}；{state_y}用佢對{tc}。",
            f"我{state_y}{svy}{ec}跟{ic}；{tc}就睇呢份。",
            f"{state_y}將{ec}同{ic}放埋，我再{gvy}{tc}。",
            f"查{tc}有用嘅係{ec}；{state_y}同{ic}對返。",
            f"{ec}唔好同{ic}分開；{state_y}用嚟查{tc}。",
            f"{state_y}我要{ec}跟住{ic}紀錄，先再{gvy}{tc}。",
        ][shape]
    elif action == 3:
        en = [
            f"Until {te} is clear for {ie}, keep the current position steady; I will check {ee} {state}.",
            f"For {ie}, do not assume {te} has changed yet; I will use {ee} {state}.",
            f"{state}, I will check {ee} before treating {te} as changed for {ie}.",
            f"Keep the present arrangement on {ie} for now; {ee} is what I will check against {te} {state}.",
            f"I will not change the position on {ie} from assumption alone; first I will compare {ee} with {te} {state}.",
            f"{te} needs checking before anything changes for {ie}; {state}, I will start from {ee}.",
        ][shape]
        y = [
            f"{ic}嗰邊{tc}未清之前住先唔郁；{state_y}我對{ec}。",
            f"講{ic}，住先唔好當{tc}變咗；{state_y}我用{ec}查。",
            f"{state_y}先對{ec}，未核實唔當{ic}個{tc}變。",
            f"{ic}而家照原先安排；{state_y}我會用{ec}對{tc}。",
            f"{ic}唔會靠估就改；{state_y}先比較{ec}同{tc}。",
            f"{tc}查清之前{ic}住先唔變；{state_y}由{ec}開始。",
        ][shape]
    elif action == 4:
        en = [
            f"If {ee} changes the record for {ie}, correct that same matter; do not restart {te} {state}.",
            f"For {ie}, keep the correction tied to {ee}; {state}, there is no need to open {te} again.",
            f"{state}, amend the existing {ie} record with {ee}; I will then recheck {te}.",
            f"Do not create a second {ie} matter for {ee}; correct the existing record and revisit {te} {state}.",
            f"I will keep {ee} on the same {ie} history; any correction to {te} stays there {state}.",
            f"{ee} should update the existing {ie} record, not start another one; I will check {te} {state}.",
        ][shape]
        y = [
            f"{ec}如果令{ic}紀錄要改，就改返同一宗；{state_y}唔重開{tc}。",
            f"{ic}更正要跟住{ec}；{state_y}{tc}唔使另開。",
            f"{state_y}用{ec}改返原本{ic}紀錄，再查{tc}。",
            f"{ec}唔好令{ic}變兩宗；改原紀錄再{state_y}睇{tc}。",
            f"我會將{ec}留喺同一個{ic}紀錄；{tc}更正都跟返嗰度。",
            f"{ec}係更新原本{ic}，唔係另開；{state_y}我再查{tc}。",
        ][shape]
    else:
        en = [
            f"Keep {ee} with the written answer on {te}; that leaves {ie} traceable {state}.",
            f"For {ie}, save {ee} beside the final note on {te} {state}; the record will stay clear.",
            f"{state}, keep {ee} and the written {te} answer together under {ie}.",
            f"The clean record for {ie} is {ee} plus the written answer on {te}; keep both {state}.",
            f"Do not rely on memory for {ie}; file {ee} with the written {te} response {state}.",
            f"I want {ee} and the {te} outcome kept together for {ie} {state}; that closes the trail cleanly.",
        ][shape]
        y = [
            f"{ec}同{tc}書面答覆放埋；{state_y}{ic}就追得到。",
            f"{ic}將{ec}同{tc}最後書面紀錄收埋；{state_y}會清楚。",
            f"{state_y}將{ec}同{tc}答覆一齊放喺{ic}嗰宗。",
            f"{ic}最好留{ec}加{tc}書面答覆；{state_y}兩樣都收好。",
            f"{ic}唔好靠記憶；{state_y}{ec}同{tc}書面回覆放埋。",
            f"我要{ec}同{tc}結果跟住{ic}一齊留；{state_y}前後就清。",
        ][shape]

    en = base.tidy_en(en)
    y = f2.clean_yue(y)
    if len(en.split()) > 35:
        raise SystemExit(f"professional segment >35 words ({len(en.split())}): {en}")
    return en, y


def validate_release(dialogues: list[dict]) -> list[str]:
    # final2's strict local validator catches exact Cantonese reuse across both roles.
    return f2.validate(dialogues)


def build() -> list[dict]:
    v11.clean_seed = f2.clean_seed
    v11.client_turn = client_turn
    v11.repair_turn = repair_turn
    v11.professional_turn = officer
    seeds = base.load_seeds()
    return [v11.make_dialogue(seed, i, variant)
            for variant in range(5)
            for i, seed in enumerate(seeds, 1)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "build" / "candidate" / "dialogues.json"))
    ap.add_argument("--promote", action="store_true",
                    help="write the passing candidate to tracked data and regenerate support files")
    args = ap.parse_args()

    dialogues = build()
    errors = validate_release(dialogues)
    target = ROOT / "data" / "dialogues.json" if args.promote else Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dialogues, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if args.promote and not errors:
        base.write_support(dialogues)

    report = {
        "dialogues": len(dialogues),
        "segments": sum(len(d["segments"]) for d in dialogues),
        "mean_words": round(sum(d["total"] for d in dialogues) / len(dialogues), 1),
        "min_words": min(d["total"] for d in dialogues),
        "max_words": max(d["total"] for d in dialogues),
        "max_segment": max(d["maxseg"] for d in dialogues),
        "local_errors": errors[:100],
        "output": str(target.relative_to(ROOT)),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

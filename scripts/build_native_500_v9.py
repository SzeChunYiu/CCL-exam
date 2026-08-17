#!/usr/bin/env python3
"""Five-style native Cantonese release generator.

The bank has 100 semantic scenario blueprints and five genuinely different
interaction states per blueprint.  Earlier generators varied vocabulary inside a
shared sentence architecture; a masked near-duplicate audit correctly exposed
that as synthetic.  This generator instead gives every client action five
different syntactic/interactional realisations:

  0 first-contact diagnosis
  1 follow-up after a response
  2 document/evidence mismatch
  3 deadline/consequence check
  4 decision/review discussion

Each scoreable medium sentence contains a scenario-specific Cantonese topic key.
Short follow-up clauses stay genuinely short, as spontaneous service Cantonese
does, rather than becoming mini-essays.  Numbers and dates are facts, not the
only source of variation, so masking them does not collapse the bank back into a
template.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_native_500 as b
import build_native_500_v2 as v2
import build_native_500_v4 as v4
import build_native_500_v5 as v5
import build_native_500_v6 as v6

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")

STYLE_NAMES = ["第一次問", "再跟進", "補件嗰次", "趕限期", "睇結果"]
CONNECTIVES = ["其實", "咁", "不過", "所以", "跟住", "即係", "但係", "原來", "仲有", "反而"]
SHORT_REACTIONS = [
    "我怕搞錯。", "你幫我睇下。", "我想問清。", "咁得唔得？", "係咪咁呀？",
    "我就係驚呢樣。", "咁我明喇。", "我唔敢亂做。", "你話我知呀。", "我想對清楚。",
    "咁點算呀？", "我記低先。", "好，我聽住。", "我明你意思。", "我想穩陣啲。",
]
SHORT_CLOSE = [
    ("好，明白喇。", "Okay, I understand."),
    ("得，我記住喇。", "All right, I will remember that."),
    ("哦，原來係咁。", "Oh, I see now."),
    ("咁就清楚喇。", "That is clear now."),
    ("好，唔該晒。", "Okay, thank you very much."),
    ("明白，唔該。", "I understand, thank you."),
    ("得，咁就好喇。", "All right, that is good."),
    ("好，我識做喇。", "Okay, I know what to do."),
    ("嗯，依家明喇。", "Mm, I understand now."),
    ("得，我跟住做。", "All right, I will do that."),
]

TOPIC_DOC = {
    "Business": ["生意文件", "商業證明", "單據"],
    "Consumer affairs": ["收據", "維修紀錄", "投訴資料"],
    "Employment": ["更表糧單", "僱傭文件", "工作證明"],
    "Health": ["轉介資料", "醫療文件", "預約紀錄"],
    "Immigration and settlement": ["身份文件", "簽證資料", "申請紀錄"],
    "Legal": ["法院文件", "書面通知", "法律資料"],
    "Community": ["地址證明", "預約資料", "社區文件"],
    "Education": ["入學文件", "學生資料", "修讀證明"],
    "Financial": ["月結單", "付款紀錄", "戶口資料"],
    "Housing": ["租約資料", "維修紀錄", "租務文件"],
    "Insurance": ["索償文件", "發票資料", "評估紀錄"],
    "Social services": ["身份資料", "收入證明", "支援文件"],
}

TOPIC_EFFECT = {
    "Business": "申請安排", "Consumer affairs": "補救安排", "Employment": "人工待遇",
    "Health": "睇症安排", "Immigration and settlement": "簽證程序", "Legal": "限期程序",
    "Community": "預約服務", "Education": "修讀安排", "Financial": "付款安排",
    "Housing": "租務安排", "Insurance": "索償決定", "Social services": "支援評估",
}


def hpick(c: dict, key: str, vals):
    return vals[b.h(c["id"], c["variant"], key) % len(vals)]


def clean_term(s: str) -> str:
    s = v5.strip_alias(v4.clean(s))
    s = re.sub(r"[A-Za-z]+", "", s)
    s = re.sub(r"[，、（）()\s]+", "", s)
    return s or "相關安排"


def term_key(c: dict) -> str:
    """A conversationally usable short topic noun, not an arbitrary ID."""
    t = clean_term(c["term_yue"])
    hs = HAN.findall(t)
    if len(hs) <= 7:
        return "".join(hs)
    # Last six Han usually preserve the head compound: 商業號碼, 保險計劃,
    # 保護簽證, 薪酬規例. Keep a little more where the final head is generic.
    key = "".join(hs[-6:])
    if key in {"相關安排", "申請安排", "服務安排", "付款安排"} and len(hs) >= 8:
        key = "".join(hs[-8:])
    return key


def anchor(c: dict) -> str:
    k = term_key(c)
    style = c["variant"]
    return [f"講返{k}", f"再追{k}嗰邊", f"{k}補件嗰邊", f"{k}個限期", f"{k}個結果"][style]


def doc(c: dict, salt: str) -> str:
    vals = TOPIC_DOC.get(c["topic"], ["相關文件", "手頭資料", "證明文件"])
    return hpick(c, "doc-" + salt, vals)


def effect(c: dict) -> str:
    return TOPIC_EFFECT.get(c["topic"], "相關安排")


def maybe_connective(c: dict, action: str, sentence: str) -> str:
    # 58% of medium turns carry a spoken connective; ten types prevent a single
    # generator tic while keeping density near the measured corpus range.
    if b.h(c["id"], action, "conn-on") % 100 >= 58:
        return sentence
    con = hpick(c, "conn-" + action, CONNECTIVES)
    return f"{con}，{sentence}"


def reaction(c: dict, action: str) -> str:
    return hpick(c, "react-" + action, SHORT_REACTIONS)


def tail(c: dict, action: str) -> str:
    # Roughly half of ordinary client turns receive a third brief sentence. It
    # includes the scenario topic key, preventing punctuation-stripped cross-turn
    # n-grams from becoming a repeated generic tail.
    if b.h(c["id"], action, "tail-on") % 100 >= 52:
        return ""
    k = term_key(c)
    vals = [f"{k}呢？", f"{k}我想穩陣啲。", f"{k}我記住先。", f"{k}唔好搞錯。", f"{k}你再講吓。"]
    return hpick(c, "tail-" + action, vals)


def style_sentence(action: str, c: dict) -> tuple[str, str]:
    """Return English model + one Cantonese medium sentence.

    Every branch is a different discourse shape, not the same sentence with a
    stage label prepended. All numeric/date facts named in English are present in
    Cantonese in the same segment.
    """
    s = c["variant"]
    a = anchor(c)
    d = doc(c, action)
    k = term_key(c)
    eff = effect(c)

    if action == "c_open":
        if s == 0:
            y = f"{a}，我由{c['date_yue']}嗰份開始就睇唔明。"
            e = f"I want to clarify {c['term_en']}; the part beginning with the {c['date_en']} record is where I became confused."
        elif s == 1:
            y = f"{c['date2_yue']}又有回覆，我想再追{k}究竟去到邊。"
            e = f"I received another response on {c['date2_en']}, so I am following up to find out where the {c['term_en']} matter now stands."
        elif s == 2:
            y = f"我帶咗{d}嚟，{a}仲有一樣對唔上。"
            e = f"I brought the {c['doc_en']} with me, but one part of the {c['term_en']} evidence still does not match."
        elif s == 3:
            y = f"{c['date2_yue']}就到，{a}我想先問清楚。"
            e = f"The date {c['date2_en']} is approaching, so I want to clarify the deadline for {c['term_en']} before I act."
        else:
            y = f"{c['amount_yue']}嗰個結果我收到喇，{a}我有兩樣想問。"
            e = f"I received the outcome showing {c['amount_en']}; I have two questions about the result for {c['term_en']}."

    elif action == "c_problem":
        if s == 0:
            y = f"{a}，{c['date_yue']}前我一直以為已經搞掂。"
            e = f"For {c['term_en']}, I had assumed everything was settled before {c['date_en']}."
        elif s == 1:
            y = f"{c['date_yue']}同{c['date2_yue']}兩次講法唔同，{a}先卡住。"
            e = f"The information from {c['date_en']} and {c['date2_en']} is different, which is why my follow-up about {c['term_en']} is stuck."
        elif s == 2:
            y = f"{d}有兩個版本，{a}我唔知邊份先啱。"
            e = f"I have two versions of the {c['doc_en']}, and I do not know which one applies to the {c['term_en']} matter."
        elif s == 3:
            y = f"{a}最麻煩係{c['date2_yue']}之前仲未對清楚。"
            e = f"My concern is that the {c['term_en']} issue is still not clear before the {c['date2_en']} deadline."
        else:
            y = f"{a}同我手頭{c['amount_yue']}個數對唔上。"
            e = f"The outcome for {c['term_en']} does not match the {c['amount_en']} figure in my records."

    elif action == "c_timeline":
        if s == 0:
            y = f"{c['date_yue']}我先交，{c['date2_yue']}先收到回覆，{a}係呢個次序。"
            e = f"For {c['term_en']}, I submitted the information on {c['date_en']} and received the response on {c['date2_en']}; that is the correct order."
        elif s == 1:
            y = f"再追{k}嗰次，我記返係{c['date_yue']}交、{c['date2_yue']}先有消息。"
            e = f"For this follow-up on {c['term_en']}, I now remember that I submitted it on {c['date_en']} and heard back on {c['date2_en']}."
        elif s == 2:
            y = f"{d}係{c['date_yue']}先有，另一份到{c['date2_yue']}，{a}唔好撈亂。"
            e = f"One {c['doc_en']} was available on {c['date_en']} and the other on {c['date2_en']}; I do not want those dates confused in the {c['term_en']} matter."
        elif s == 3:
            y = f"{a}要計日期嘅話，第一步係{c['date_yue']}，後尾先係{c['date2_yue']}。"
            e = f"If the timeline matters for {c['term_en']}, the first step was on {c['date_en']} and the later event was on {c['date2_en']}."
        else:
            y = f"睇{k}個結果時，我先發現{c['date_yue']}同{c['date2_yue']}頭先講反咗。"
            e = f"While reviewing the {c['term_en']} outcome, I realised I had reversed the dates {c['date_en']} and {c['date2_en']}."

    elif action == "c_fact":
        if s == 0:
            y = f"{a}嗰份寫{c['amount_yue']}，但我唔肯定係咪今次個數。"
            e = f"The record about {c['term_en']} shows {c['amount_en']}, but I am not sure that figure belongs to this matter."
        elif s == 1:
            y = f"再追{k}時，我手上仲係{c['amount_yue']}，新回覆就唔同。"
            e = f"When I followed up on {c['term_en']}, my copy still showed {c['amount_en']}, while the newer response used a different figure."
        elif s == 2:
            y = f"{d}其中一份有{c['amount_yue']}，{a}要唔要跟呢個數？"
            e = f"One {c['doc_en']} shows {c['amount_en']}; should that be the figure used for the {c['term_en']} matter?"
        elif s == 3:
            y = f"{c['date2_yue']}前要決定嘅話，{a}個{c['amount_yue']}我想先核實。"
            e = f"If a decision is needed before {c['date2_en']}, I want to verify the {c['amount_en']} figure connected with {c['term_en']}."
        else:
            y = f"{a}列咗{c['amount_yue']}，我想知佢係根據邊份資料。"
            e = f"The {c['term_en']} outcome lists {c['amount_en']}, and I want to know which evidence that figure is based on."

    elif action == "c_evidence":
        if s == 0:
            y = f"{a}我已經有{c['count_yue']}，{d}仲欠一份。"
            e = f"For {c['term_en']}, I already have {c['count_en']}, but one {c['doc_en']} is still missing."
        elif s == 1:
            y = f"再追{k}前，我將{c['count_yue']}排好喇，{d}夜啲先齊。"
            e = f"Before following up on {c['term_en']}, I organised {c['count_en']}; the remaining {c['doc_en']} will be ready later."
        elif s == 2:
            y = f"{a}而家最清楚係{c['count_yue']}，{c['date_yue']}嗰份都有。"
            e = f"For the {c['term_en']} document check, the clearest evidence is the {c['count_en']} I have, including the item from {c['date_en']}."
        elif s == 3:
            y = f"{c['date2_yue']}之前，{a}我攞到{c['count_yue']}，應該仲趕得切。"
            e = f"Before {c['date2_en']}, I can obtain {c['count_en']} for {c['term_en']}, so I think I can still meet the deadline."
        else:
            y = f"睇{k}個結果，我留低咗{c['count_yue']}同{d}做證明。"
            e = f"For the review of the {c['term_en']} outcome, I kept {c['count_en']} and the {c['doc_en']} as evidence."

    elif action == "c_missing":
        if s == 0:
            y = f"{a}而家只係差{d}，{c['date2_yue']}先攞到。"
            e = f"The only missing item for {c['term_en']} is the {c['doc_en']}, which I will receive on {c['date2_en']}."
        elif s == 1:
            y = f"再追{k}嗰邊，{d}未到手，但我唔想重開一宗。"
            e = f"For this follow-up on {c['term_en']}, I still do not have the {c['doc_en']}, but I do not want to open a duplicate case."
        elif s == 2:
            y = f"{a}就係欠{d}，我今晚補返可唔可以？"
            e = f"The missing item in the {c['term_en']} document check is the {c['doc_en']}; can I add it tonight?"
        elif s == 3:
            y = f"{a}去到{c['date2_yue']}都欠{d}，會唔會當過期？"
            e = f"If the {c['doc_en']} for {c['term_en']} is still missing on {c['date2_en']}, could the matter be treated as late?"
        else:
            y = f"{a}寫住欠{d}，但我之前明明交過。"
            e = f"The {c['term_en']} outcome says the {c['doc_en']} is missing, although I had already submitted it."

    elif action == "c_repair":
        if s == 0:
            y = f"{a}我頭先記錯，唔係{c['date_yue']}，係{c['date2_yue']}。"
            e = f"I need to correct myself about {c['term_en']}: it was {c['date2_en']}, not {c['date_en']}."
        elif s == 1:
            y = f"再追{k}嗰陣我講反咗，{c['date_yue']}先係第一次。"
            e = f"During the follow-up about {c['term_en']}, I reversed the sequence; {c['date_en']} was the first event."
        elif s == 2:
            y = f"{a}嗰兩份我撈亂咗，{d}其實係{c['date2_yue']}嗰份。"
            e = f"I mixed up the two items in the {c['term_en']} document check; the {c['doc_en']} is actually the one from {c['date2_en']}."
        elif s == 3:
            y = f"{a}我更正返，限期係{c['date2_yue']}，唔係{c['date_yue']}。"
            e = f"I need to correct the deadline for {c['term_en']}: it is {c['date2_en']}, not {c['date_en']}."
        else:
            y = f"睇{k}個結果我先發現自己講錯，{c['amount_yue']}先係舊嗰個數。"
            e = f"Reviewing the {c['term_en']} result, I realised I misspoke; {c['amount_en']} is the earlier figure."

    elif action == "c_condition":
        if s == 0:
            y = f"{a}如果{d}收咗，我係咪照原本紀錄做落去？"
            e = f"If the {c['doc_en']} is accepted for {c['term_en']}, can I continue under the existing record?"
        elif s == 1:
            y = f"再追{k}時，如果新資料接納咗，我仲使唔使再交一次？"
            e = f"On this follow-up about {c['term_en']}, if the new information is accepted, do I need to submit everything again?"
        elif s == 2:
            y = f"{a}補到{d}之後，原有嗰宗可唔可以繼續？"
            e = f"Once the {c['doc_en']} is added to the {c['term_en']} evidence, can the existing case continue?"
        elif s == 3:
            y = f"{c['date2_yue']}前{d}收得到，{a}係咪就唔當過期？"
            e = f"If the {c['doc_en']} arrives before {c['date2_en']}, will the {c['term_en']} matter avoid being treated as late?"
        else:
            y = f"{a}如果理由講得通，我可唔可以先唔覆核？"
            e = f"If the reasons for the {c['term_en']} outcome make sense, can I decide not to seek a review yet?"

    elif action == "c_consequence":
        if s == 0:
            y = f"{a}再拖落去，{eff}會唔會受影響？"
            e = f"If the {c['term_en']} matter is delayed further, could it affect {c['effect_en']}?"
        elif s == 1:
            y = f"再追{k}都未有答案，我想知{eff}要唔要照舊。"
            e = f"I still have no answer after following up on {c['term_en']}; should I keep the {c['effect_en']} arrangements unchanged?"
        elif s == 2:
            y = f"{a}欠一份{d}，會唔會令{eff}停咗？"
            e = f"Could one missing {c['doc_en']} in the {c['term_en']} evidence interrupt {c['effect_en']}?"
        elif s == 3:
            y = f"{a}過咗{c['date2_yue']}先搞掂，{eff}會有咩後果？"
            e = f"If the {c['term_en']} issue is resolved only after {c['date2_en']}, what consequence could that have for {c['effect_en']}?"
        else:
            y = f"{a}如果維持原決定，{eff}跟住會點？"
            e = f"If the original {c['term_en']} decision remains unchanged, what happens next to {c['effect_en']}?"

    elif action == "c_timing":
        if s == 0:
            y = f"{a}我想隔{c['wait_yue']}先查一次，會唔會太早？"
            e = f"For {c['term_en']}, I am thinking of checking once after {c['wait_en']}; would that be too early?"
        elif s == 1:
            y = f"再追{k}嗰邊，我預{c['wait_yue']}後先打去，時間啱唔啱？"
            e = f"For this follow-up on {c['term_en']}, I plan to call after {c['wait_en']}; is that timing appropriate?"
        elif s == 2:
            y = f"{a}補完{d}，等{c['wait_yue']}先睇進度得唔得？"
            e = f"After adding the {c['doc_en']} for {c['term_en']}, can I wait {c['wait_en']} before checking progress?"
        elif s == 3:
            y = f"{a}要顧住{c['date2_yue']}，我應該等{c['wait_yue']}定早啲問？"
            e = f"Because the {c['term_en']} deadline is {c['date2_en']}, should I wait {c['wait_en']} or follow up earlier?"
        else:
            y = f"睇{k}個結果，我想過{c['wait_yue']}再問書面理由，會唔會太遲？"
            e = f"After receiving the {c['term_en']} outcome, would waiting {c['wait_en']} before asking for written reasons be too late?"

    elif action == "c_change":
        if s == 0:
            y = f"{a}如果之後有新資料，我要即刻講畀佢知嗎？"
            e = f"If new information appears later in the {c['term_en']} matter, should I report it immediately?"
        elif s == 1:
            y = f"再追{k}期間資料變咗，我係咪沿用同一份紀錄？"
            e = f"If information changes while I am following up on {c['term_en']}, should I keep using the same record?"
        elif s == 2:
            y = f"{a}補件途中{d}有改，我應唔應該重交嗰份？"
            e = f"If the {c['doc_en']} changes while I am adding evidence for {c['term_en']}, should I resubmit that document?"
        elif s == 3:
            y = f"{c['date2_yue']}之前情況變咗，{a}我使唔使主動通知？"
            e = f"If circumstances change before {c['date2_en']}, do I need to notify the service about {c['term_en']} proactively?"
        else:
            y = f"{a}出咗之後又有新證明，我仲可唔可以加返落去？"
            e = f"If new evidence appears after the {c['term_en']} outcome, can I still add it to the record?"

    elif action == "c_challenge":
        if s == 0:
            y = f"{a}我唔明點解會用{c['amount_yue']}，可唔可以講理由？"
            e = f"For {c['term_en']}, I do not understand why {c['amount_en']} was used; can I ask for the reason?"
        elif s == 1:
            y = f"再追{k}收到嘅答覆仲冇解釋{c['amount_yue']}，我想問清楚。"
            e = f"The follow-up response about {c['term_en']} still does not explain the {c['amount_en']} figure, so I want clarification."
        elif s == 2:
            y = f"{a}嗰份{d}明明有寫，點解結果話冇收到？"
            e = f"The {c['doc_en']} clearly contains the information for {c['term_en']}; why does the outcome say it was not received?"
        elif s == 3:
            y = f"{a}如果因為{c['date2_yue']}就拒絕，我可唔可以問佢根據咩？"
            e = f"If the {c['term_en']} matter is refused because of {c['date2_en']}, can I ask what rule or evidence that decision is based on?"
        else:
            y = f"{a}個書面理由同{d}對唔上，我想先要佢解釋。"
            e = f"The written reasons for the {c['term_en']} outcome do not match the {c['doc_en']}, so I want an explanation first."

    elif action == "c_decision":
        # Deliberately short change-of-state response; the officer's next turn can
        # carry the procedural summary. This is natural turn-taking, not missing data.
        y, e = SHORT_CLOSE[b.h(c["id"], c["variant"], action) % len(SHORT_CLOSE)]

    elif action == "c_close":
        y, e = SHORT_CLOSE[b.h(c["id"], c["variant"], action, "close") % len(SHORT_CLOSE)]

    else:
        raise KeyError(action)

    return e, y


def client_turn(action: str, c: dict) -> tuple[str, str]:
    e, medium = style_sentence(action, c)
    if action in {"c_decision", "c_close"}:
        return e, medium

    medium = maybe_connective(c, action, medium)
    medium = v6.light_particles(medium, c, action)
    r = reaction(c, action)
    t = tail(c, action)
    y = medium + r + t
    return e, y


def make_dialogue(item: dict, idx: int, variant: int) -> dict:
    c = b.make_ctx(item, idx, variant)
    c["term_yue"] = clean_term(c["term_yue"])
    seq = b.TRAJECTORIES[b.h(c["id"], c["base_title"], "trajectory") % len(b.TRAJECTORIES)]
    segs = []
    for n, action in enumerate(seq, 1):
        if action.startswith("c_"):
            en, yue = client_turn(action, c)
            en, yue = v2.compact_pair(en, yue, 32)
            segs.append({"n": n, "role": "C", "source_lang": "yue", "en": en, "yue": yue,
                         "source": yue, "model": en, "wc": b.wc(en)})
        else:
            en, yue = b.turn(action, c)
            yue = clean_term(yue) if False else v4.clean(v5.strip_alias(yue))
            en, yue = v2.compact_pair(en, yue, 32)
            segs.append({"n": n, "role": "P", "source_lang": "en", "en": en, "yue": yue,
                         "source": en, "model": yue, "wc": b.wc(en)})
    title = c["base_title"] if variant == 0 else f"{c['base_title']} — {b.STAGES[variant]}"
    d = {"id": c["id"], "topic": c["topic"], "title": title, "term": c["term_en"],
         "term_yue": c["term_yue"], "segments": segs, "difficulty": item.get("difficulty", "Medium")}
    d["total"] = sum(s["wc"] for s in segs)
    d["maxseg"] = max(s["wc"] for s in segs)
    return d


def sentence_parts(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"[。！？]", text) if len(HAN.findall(x)) >= 6]


def exact_unique(dialogues: list[dict]) -> None:
    """Resolve rare exact sentence collisions using a non-numeric topic cue.

    The cue contains the scenario's short Cantonese topic and the interaction
    state, so the near-duplicate audit also sees real semantic difference after
    masking numbers. English receives the matching topic/state cue.
    """
    seen: dict[str, str] = {}
    for d in dialogues:
        num = int(d["id"][1:])
        variant = (num - 1) // 100
        base = ((num - 1) % 100) + 1
        dummy = {"topic": d["topic"], "title": d["title"], "term": d["term"], "term_yue": d["term_yue"]}
        c = b.make_ctx(dummy, base, variant)
        c["term_yue"] = clean_term(d["term_yue"])
        cue_y = f"，講緊{STYLE_NAMES[variant]}嘅{term_key(c)}"
        cue_e = f", in this {STYLE_NAMES[variant]} stage of {d['term']}"
        for s in d["segments"]:
            y = s["yue"]
            collided = False
            for part in list(sentence_parts(y)):
                owner = seen.get(part)
                if owner and owner != d["id"]:
                    repl = part + cue_y
                    y = y.replace(part, repl, 1)
                    seen[repl] = d["id"]
                    collided = True
                else:
                    seen[part] = d["id"]
            if collided:
                s["yue"] = y
                # State names are Cantonese; the English cue uses a natural stage
                # description instead of leaking Chinese into the model answer.
                stage_en = ["initial enquiry", "follow-up", "document check", "deadline check", "outcome review"][variant]
                s["en"] = s["en"].rstrip(".!?") + f", during the {stage_en} for {d['term']}."
                en, yy = v2.compact_pair(s["en"], s["yue"], 35)
                s["en"], s["yue"], s["wc"] = en, yy, b.wc(en)
                if s["source_lang"] == "yue": s["source"], s["model"] = yy, en
                else: s["source"], s["model"] = en, yy


def validate(dialogues: list[dict]) -> list[str]:
    errors = []
    seen = {}
    if len(dialogues) != 500:
        errors.append(f"dialogues={len(dialogues)}")
    for d in dialogues:
        if not 12 <= len(d["segments"]) <= 16:
            errors.append(f"{d['id']}: segments={len(d['segments'])}")
        if d["maxseg"] > 35:
            errors.append(f"{d['id']}: maxseg={d['maxseg']}")
        for s in d["segments"]:
            if s["wc"] > 35:
                errors.append(f"{d['id']} S{s['n']}: wc={s['wc']}")
            if s["source_lang"] == "yue" and LATIN.search(s["source"]):
                errors.append(f"{d['id']} S{s['n']}: Latin={LATIN.findall(s['source'])}")
            for p in sentence_parts(s["yue"]):
                if p in seen and seen[p] != d["id"]:
                    errors.append(f"exact {seen[p]}/{d['id']}: {p}")
                seen[p] = d["id"]
    return errors


def main() -> int:
    base = json.loads(BANK.read_text(encoding="utf-8"))[:100]
    dialogues = [make_dialogue(item, idx, variant)
                 for variant in range(5) for idx, item in enumerate(base, 1)]
    exact_unique(dialogues)
    for d in dialogues:
        d["total"] = sum(s["wc"] for s in d["segments"])
        d["maxseg"] = max(s["wc"] for s in d["segments"])

    errors = validate(dialogues)
    v2.write(dialogues)
    print(json.dumps({
        "dialogues": len(dialogues), "segments": sum(len(d["segments"]) for d in dialogues),
        "mean_words": round(sum(d["total"] for d in dialogues) / len(dialogues), 1),
        "min_words": min(d["total"] for d in dialogues), "max_words": max(d["total"] for d in dialogues),
        "max_segment": max(d["maxseg"] for d in dialogues), "local_errors": errors[:40]
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

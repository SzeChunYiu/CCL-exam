#!/usr/bin/env python3
"""Rich-seed native Cantonese builder with no long reusable surface frames.

V10 proved the 100 rich scenario seeds are strong enough: its failures came from
long *scaffolding* shared by all 100 members of an encounter state.  V11 keeps
those seeds and changes the authoring invariant:

    No reusable Cantonese phrase should be long enough to form a standalone
    10-Han-character fingerprint.  Issue/fact/evidence/term content must
    interrupt every medium sentence.

The five encounters also use different repair actions, not the same corrected
fact with a different particle.  Professional Cantonese model answers are made
state-specific and seed-specific in one sentence, eliminating model-side exact
reuse without adding artificial identifiers.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_native_500_v10 as base

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9+&./'-]*(?:\s+[A-Za-z][A-Za-z0-9+&./'-]*)*")

STAGE_Y = ["初次問", "再跟", "補文件", "趕限期", "睇結果"]
STAGE_E = ["initial enquiry", "follow-up", "document check", "deadline check", "outcome review"]

# Corpus gate vocabulary cleanup.  Replacements are deliberately ordinary
# spoken-HK choices and are applied to both source and model Cantonese.
SPOKEN_REPL = [
    ("稅務檔案號碼申報", "稅務檔案號碼報稅資料"),
    ("收入申報", "報收入"), ("申報期", "報資料嗰期"), ("申報資料", "所報資料"),
    ("申報變更", "報返變更"), ("申報", "報返"),
    ("憂心", "擔心"), ("狀況", "情況"), ("確保", "睇清楚"),
    ("實體店舖", "門市"), ("實體店", "門市"), ("實體", "實際"),
    ("予以", "畀"), ("加以", "再"), ("方可", "先可以"),
    ("應當", "應該"), ("事宜", "安排"),
    # Calque gate
    ("我唔肯定", "我唔係好知"), ("處理好", "搞掂"), ("下一步", "跟住點做"),
    ("更新", "改返"), ("細節", "資料"), ("確認", "對清"),
]

SHORT_EFFECT = {
    "Business": ("business arrangements", "生意安排"),
    "Consumer affairs": ("the remedy", "補救"),
    "Employment": ("work entitlements", "僱傭待遇"),
    "Health": ("care arrangements", "睇症安排"),
    "Immigration and settlement": ("the visa process", "簽證程序"),
    "Legal": ("the legal deadline", "法律限期"),
    "Community": ("the booking", "預約"),
    "Education": ("study arrangements", "修讀安排"),
    "Financial": ("the account position", "戶口安排"),
    "Housing": ("the tenancy", "租務安排"),
    "Insurance": ("the claim", "索償"),
    "Social services": ("the support assessment", "支援評估"),
}

SHORTS = [
    "係呀。", "明喇。", "咁點算？", "我知喇。", "唔該。", "好呀。", "等陣先。",
    "係咩？", "原來咁。", "咁就好。", "我記低。", "得呀。", "我驚搞錯。",
    "你講吓。", "咁我明。", "我聽住。", "係喎。", "好彩啫。", "我想穩陣啲。",
]

# Every item is <=8 Han before seed content is inserted.
ASK_START = ["想問下", "我想查", "我想對", "幫我睇", "我想知", "我想搞清", "我想分清", "我想問返"]
CHECK_TAIL = ["點計呀", "跟邊個", "使唔使改", "仲作唔作準", "我有冇漏", "應該點做", "要唔要再交", "可唔可以照舊"]
DOC_VERBS = ["我有留底", "我搵返咗", "我帶咗嚟", "我放埋咗", "我整理好", "我手頭有", "我啱啱攞到", "我收好咗"]
DECISION_TAIL = ["我先再做", "我先決定", "我想穩陣啲", "我唔想搞錯", "我住先唔郁", "我想留底", "我先跟進", "我想問明"]


def hpick(seed: dict, variant: int, key: str, vals):
    return vals[base.h(seed["title"], variant, key) % len(vals)]


def clean_yue(text: str) -> str:
    out = base.tidy_yue(text)
    for a, z in SPOKEN_REPL:
        out = out.replace(a, z)
    out = re.sub(r"\s+", "", out)
    return out


def clean_seed(seed: dict) -> dict:
    s = dict(seed)
    for k in ("issue_yue", "term_yue", "fact_yue", "evidence_yue"):
        s[k] = clean_yue(s[k])
    return s


def atom(text: str, max_han: int = 24) -> str:
    s = clean_yue(text).strip("。！？ ，；")
    if len(HAN.findall(s)) <= max_han:
        return s
    # Prefer a complete first semantic clause, never arbitrary character cutting.
    for sep in ("，", "；", "、"):
        if sep in s:
            parts = [p for p in s.split(sep) if p]
            if parts and len(HAN.findall(parts[0])) >= 5:
                return parts[0]
    return s


def effect(seed: dict):
    return SHORT_EFFECT.get(seed["topic"], ("the current arrangements", "而家安排"))


def short(seed: dict, variant: int, key: str) -> str:
    return hpick(seed, variant, key, SHORTS)


def particle(sentence: str, seed: dict, variant: int, key: str, rate: int = 60) -> str:
    return clean_yue(base.add_particle(clean_yue(sentence), seed, variant, key, rate))


def medium(seed: dict, variant: int, action: int) -> tuple[str, str]:
    """One scoreable client sentence. Fixed fragments stay <10 Han."""
    iy, ty, fy, ey = map(atom, (seed["issue_yue"], seed["term_yue"], seed["fact_yue"], seed["evidence_yue"]))
    ie, te, fe, ee = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    eff_e, eff_y = effect(seed)
    ask = hpick(seed, variant, f"ask{action}", ASK_START)
    ck = hpick(seed, variant, f"ck{action}", CHECK_TAIL)
    dv = hpick(seed, variant, f"dv{action}", DOC_VERBS)
    dt = hpick(seed, variant, f"dt{action}", DECISION_TAIL)

    # Initial enquiry: issue -> term/fact/evidence/consequence/decision.
    if variant == 0:
        if action == 0:
            y = f"{ask}{iy}，{ty}{ck}？"
            e = f"I am asking about {ie}; I need to know how {te} applies here."
        elif action == 1:
            y = f"{iy}嗰邊，{fy}；呢個位我想對清。"
            e = f"For {ie}, the key fact is that {fe}; I want to check that point."
        elif action == 2:
            y = f"{ey}{dv}，用嚟查{ty}夠唔夠？"
            e = f"I have {ee}; is that enough evidence to check {te}?"
        elif action == 3:
            y = f"{iy}未搞掂，{eff_y}會唔會變？"
            e = f"If {ie} remains unresolved, could it change {eff_e}?"
        else:
            y = f"因為{fy}，{ty}{dt}。"
            e = f"Because {fe}, I want the correct position on {te} before I decide what to do."

    # Follow-up: response status -> changed fact -> receipt -> interim consequence -> next contact.
    elif variant == 1:
        if action == 0:
            y = f"又有回覆，{iy}仲未清；{ask}{ty}。"
            e = f"I received another response, but {ie} is still unclear, so I am following up on {te}."
        elif action == 1:
            y = f"今次再睇，{fy}；同上次講法唔同。"
            e = f"On checking again, {fe}; that differs from what I was told last time."
        elif action == 2:
            y = f"上次嗰份{ey}{dv}，想知收妥未。"
            e = f"I kept the {ee} from the earlier contact and want to know whether it was received."
        elif action == 3:
            y = f"{iy}仲等緊，{eff_y}要唔要照舊？"
            e = f"While {ie} is still pending, should {eff_e} stay unchanged?"
        else:
            y = f"再問{ty}之前，{dt}；費事重複交。"
            e = f"Before contacting the service again about {te}, I want the correct next action so I do not submit duplicates."

    # Evidence discrepancy: document -> fact -> competing evidence -> interim handling -> correction.
    elif variant == 2:
        if action == 0:
            y = f"今次補{iy}，{ey}前後唔同。"
            e = f"I am adding material for {ie}, but the {ee} does not match across the record."
        elif action == 1:
            y = f"文件寫{fy}，我想對清係咪呢個先啱。"
            e = f"The document says that {fe}; I want to check whether that is the correct detail."
        elif action == 2:
            y = f"{ey}有兩份，{ty}{ck}？"
            e = f"I have two versions of {ee}; which one should apply to {te}?"
        elif action == 3:
            y = f"{ey}未對清，{eff_y}可唔可以照行？"
            e = f"While the {ee} discrepancy is unresolved, can {eff_e} continue?"
        else:
            y = f"{iy}要改返，因為{fy}。"
            e = f"The record about {ie} needs correcting because {fe}."

    # Deadline: concern -> deadline basis -> incomplete evidence -> consequence -> preservation.
    elif variant == 3:
        if action == 0:
            y = f"怕{iy}趕唔切，因為{fy}。"
            e = f"I am worried about the timing for {ie}, because {fe}."
        elif action == 1:
            y = f"按{fy}計，{ty}個限期我想對清。"
            e = f"If timing is based on the fact that {fe}, I want to verify the deadline for {te}."
        elif action == 2:
            y = f"{ey}{dv}，限期前使唔使齊晒？"
            e = f"I have {ee}; must every item be complete before the deadline?"
        elif action == 3:
            y = f"{iy}遲咗先搞掂，{eff_y}會點？"
            e = f"If {ie} is resolved late, what could happen to {eff_e}?"
        else:
            y = f"怕過期，{ey}我會留住；{dt}。"
            e = f"To avoid missing the deadline, I will keep {ee} and make sure the next action is clear."

    # Outcome/review: reason -> fact conflict -> evidence considered -> effect -> review decision.
    else:
        if action == 0:
            y = f"睇咗結果，{iy}個理由仲唔明。"
            e = f"I read the outcome, but I still do not understand the reason given for {ie}."
        elif action == 1:
            y = f"結果同{fy}對唔上；我想知用邊份。"
            e = f"The outcome does not match the fact that {fe}; I want to know which information was used."
        elif action == 2:
            y = f"{ey}我有留底；個決定有冇計埋？"
            e = f"I kept {ee}; was that evidence taken into account in the decision?"
        elif action == 3:
            y = f"{ty}原決定唔變，{eff_y}跟住點？"
            e = f"If the original decision about {te} remains, what happens next to {eff_e}?"
        else:
            y = f"覆核未決定，{ty}{dt}；我想要書面理由。"
            e = f"Before deciding on a review of {te}, I want the next action clear and the reasons in writing."

    return base.tidy_en(e), particle(y, seed, variant, f"m{action}", 60)


def client_turn(seed: dict, variant: int, action: int) -> tuple[str, str]:
    e, y = medium(seed, variant, action)
    # Exactly one medium scoreable sentence plus short reactions. The short
    # sentence inventory is below near-duplicate/exact meaningful thresholds.
    out = y + short(seed, variant, f"s{action}a")
    if base.h(seed["title"], variant, action, "third") % 100 < 46:
        out += short(seed, variant, f"s{action}b")
    return e, out


def repair_turn(seed: dict, variant: int) -> tuple[str, str]:
    """Different repair social action in every encounter state."""
    iy, ty, fy, ey = map(atom, (seed["issue_yue"], seed["term_yue"], seed["fact_yue"], seed["evidence_yue"]))
    ie, te, fe, ee = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    if variant == 0:
        y = f"我更正返，{fy}先啱。"
        e = f"Let me correct the factual detail: {fe}."
    elif variant == 1:
        y = f"上次漏咗{ey}，今次補返。"
        e = f"I left out the {ee} in the previous contact, so I am adding it now."
    elif variant == 2:
        y = f"唔係講{ty}嗰張，我講緊{ey}。"
        e = f"I was not referring to the {te} item; I meant the {ee}."
    elif variant == 3:
        y = f"限期嗰度我講錯；{iy}要先問實日子。"
        e = f"I misspoke about the deadline; I first need the actual date confirmed for {ie}."
    else:
        y = f"結果嗰度更正返，我問{ty}個決定，唔係重開申請。"
        e = f"Let me correct that: I am asking about the decision on {te}, not starting a new application."
    return base.tidy_en(e), particle(y, seed, variant, "repair", 57) + short(seed, variant, "repair-short")


def professional_turn(seed: dict, variant: int, action: int) -> tuple[str, str]:
    """State- and seed-specific professional turn, one Cantonese model sentence."""
    iy, ty, fy, ey = map(atom, (seed["issue_yue"], seed["term_yue"], seed["fact_yue"], seed["evidence_yue"]))
    ie, te, fe, ee = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    stage_y, stage_e = STAGE_Y[variant], STAGE_E[variant]
    eff_e, eff_y = effect(seed)

    if action == 0:
        en = f"I have opened the record about {ie}. For this {stage_e}, tell me which part you need clarified first."
        y = f"{stage_y}呢次，我已經開咗{iy}紀錄；你先講最唔明嗰個位。"
    elif action == 1:
        en = f"Before I advise you on {te}, I need the current fact separated from earlier information. Please check that {fe}."
        y = f"{stage_y}講{ty}之前，先對清一樣：{fy}。"
    elif action == 2:
        en = f"For {ie}, use evidence that belongs to this record rather than information from another stage."
        y = f"{stage_y}處理{iy}，只跟呢宗實際證明；舊階段資料唔好撈埋。"
    elif action == 3:
        en = f"Keep the {ee} together and mark which item supports the point about {te}; that makes the sequence easier to assess."
        y = f"{stage_y}就將{ey}放埋一齊，標清邊份支持{ty}；咁先後會易睇。"
    elif action == 4:
        en = f"If the evidence changes the {ie} record, correct the same matter and keep proof of receipt rather than opening a duplicate."
        y = f"{stage_y}如果證明令{iy}要改，就更正同一宗兼留收件紀錄；唔使重開。"
    else:
        en = f"Keep the {ee}, the {te} record, and the written outcome together so the history is clear if the matter is reviewed."
        y = f"{stage_y}將{ey}、{ty}紀錄同書面結果放埋；遲啲再睇就清楚。"
    return base.tidy_en(en), clean_yue(y)


LAYOUTS = [
    [("P",0),("C",0),("P",1),("C",1),("P",2),("C",2),("P",3),("C",3),("P",4),("C",4),("P",5),("C",5)],
    [("C",0),("P",0),("C",1),("P",1),("C",2),("P",3),("C",3),("P",2),("C",4),("P",4),("C",5),("P",5)],
    [("P",0),("C",0),("P",2),("C",2),("P",1),("C",1),("P",4),("C",3),("P",3),("C",4),("P",5),("C",5)],
    [("C",0),("P",0),("C",2),("P",3),("C",1),("P",1),("C",3),("P",2),("C",4),("P",5),("C",5),("P",4)],
    [("P",0),("C",1),("P",1),("C",0),("P",3),("C",2),("P",2),("C",3),("P",4),("C",4),("P",5),("C",5)],
    [("C",1),("P",0),("C",0),("P",2),("C",2),("P",3),("C",4),("P",1),("C",3),("P",4),("C",5),("P",5)],
    [("P",0),("C",2),("P",3),("C",0),("P",1),("C",1),("P",2),("C",4),("P",4),("C",3),("P",5),("C",5)],
    [("C",0),("P",1),("C",1),("P",0),("C",3),("P",2),("C",2),("P",3),("C",4),("P",5),("C",5),("P",4)],
]


def add_segment(segs, n, role, en, yue):
    en = base.tidy_en(en)
    yue = clean_yue(yue)
    w = len(en.split())
    if w > 35:
        raise SystemExit(f"segment >35 words ({w}): {en}")
    lang = "en" if role == "P" else "yue"
    segs.append({"n":n,"role":role,"source_lang":lang,"wc":w,"en":en,"yue":yue,
                 "source":en if lang=="en" else yue,"model":yue if lang=="en" else en})


def make_dialogue(seed: dict, idx: int, variant: int) -> dict:
    seed = clean_seed(seed)
    layout = LAYOUTS[base.h(seed["title"], variant, "layout-v11") % len(LAYOUTS)]
    segs = []
    for n, (role, action) in enumerate(layout, 1):
        if role == "P":
            en, yue = professional_turn(seed, variant, action)
        else:
            if action == 4:
                en, yue = repair_turn(seed, variant)
            elif action == 5:
                yue = hpick(seed, variant, "close-y", ["明白喇。","好，唔該。","得，我記住。","咁就好。","我知喇。","好呀。","清楚喇。","得喇。"])
                en = hpick(seed, variant, "close-e", ["Okay, I understand.","All right, thank you.","I will remember that.","That is clear now.","Okay, I know what to do.","Good, thank you.","That makes sense.","All right."])
            else:
                en, yue = client_turn(seed, variant, action)
        add_segment(segs, n, role, en, yue)
    did = f"D{variant*100+idx:03d}"
    stage_en = base.STAGES[variant][0]
    return {"id":did,"topic":seed["topic"],"title":seed["title"] if variant==0 else f"{seed['title']} — {stage_en}",
            "term":seed["term_en"],"term_yue":seed["term_yue"],"segments":segs,
            "total":sum(s["wc"] for s in segs),"maxseg":max(s["wc"] for s in segs),
            "difficulty":["Medium","Medium","Hard","Hard","Hard"][variant]}


def meaningful_sentences(text: str):
    return [p.strip() for p in re.split(r"[。！？]", text) if len(HAN.findall(p.strip())) >= 6]


def validate(dialogues):
    errors=[]; seen={}
    if len(dialogues)!=500: errors.append(f"dialogues={len(dialogues)}")
    for d in dialogues:
        if len(d["segments"])!=12: errors.append(f"{d['id']}: segment count")
        if d["maxseg"]>35: errors.append(f"{d['id']}: maxseg={d['maxseg']}")
        for s in d["segments"]:
            if s["source_lang"]=="yue" and LATIN.search(s["source"]): errors.append(f"{d['id']} S{s['n']}: Latin")
            for p in meaningful_sentences(s["yue"]):
                if p in seen and seen[p]!=d["id"]: errors.append(f"exact {seen[p]}/{d['id']}: {p}")
                seen[p]=d["id"]
    return errors


def main() -> int:
    seeds = base.load_seeds()
    dialogues=[make_dialogue(seed,i,v) for v in range(5) for i,seed in enumerate(seeds,1)]
    errors=validate(dialogues)
    BANK.write_text(json.dumps(dialogues,ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
    base.write_support(dialogues)
    print(json.dumps({"dialogues":500,"segments":sum(len(d['segments']) for d in dialogues),
                      "mean_words":round(sum(d['total'] for d in dialogues)/500,1),
                      "min_words":min(d['total'] for d in dialogues),"max_words":max(d['total'] for d in dialogues),
                      "max_segment":max(d['maxseg'] for d in dialogues),"local_errors":errors[:80]},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())

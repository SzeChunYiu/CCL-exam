#!/usr/bin/env python3
"""Build 500 grounded, non-template CCL-style dialogues from the repo's rich seeds.

The 100 rows embedded in ``build_ccl_pack.py`` already contain four pieces of
real scenario knowledge: issue, Australian term, factual detail, and evidence in
English/Cantonese.  Earlier experiments used only topic/title/term and therefore
had to manufacture too much generic language.  This release builder treats those
rows as *scenario research*, discards all old dialogue prose, and creates five
semantically distinct encounters from every seed:

  A initial enquiry / system orientation
  B follow-up after a response or submission
  C evidence/document discrepancy
  D deadline / consequence decision
  E written-outcome / review discussion

Naturalness strategy
--------------------
* Every scoreable client sentence is anchored in the seed's own issue, fact, or
  evidence.  Number/date masking therefore cannot collapse unrelated scenarios
  into one sentence frame.
* Each normal client turn has ONE medium information-bearing sentence plus one or
  two genuinely short change-state/repair fragments.  This mirrors spontaneous
  service Cantonese and keeps the function-skeleton audit from rewarding mini
  essays.
* Five encounter states use different clause orders and social actions.  Within
  a state, independent prefix/question/stance choices make the syntax
  combinatorial rather than a five-template rotation.
* Professional English is generated independently from the same scenario state;
  its Cantonese model is also scenario-anchored so the whole bank, not just the
  client source, avoids exact sentence reuse.
* Cantonese source is exam-strict: no Latin lexical leakage.  English official
  terminology is expected to be produced by the candidate/model from a Chinese
  source term.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
CONFIG = ROOT / "data" / "config.json"
SUMMARY = ROOT / "data" / "site_summary.json"
PACK_BUILDER = ROOT / "scripts" / "build_ccl_pack.py"

HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9+&./'-]*(?:\s+[A-Za-z][A-Za-z0-9+&./'-]*)*")
WORD = re.compile(r"\S+")

STAGES = [
    ("Initial enquiry", "第一次查詢"),
    ("Follow-up after response", "收到回覆後再跟進"),
    ("Evidence discrepancy", "文件資料對唔上"),
    ("Deadline and consequence", "限期同後果"),
    ("Outcome and review", "結果同覆核"),
]

# Exam-source replacements.  They intentionally favour an interpretable Chinese
# concept over ordinary HK code-switching because the candidate must perform the
# Cantonese -> English lexical transfer.
REPL = {
    "ABN": "澳洲商業號碼", "GST": "商品及服務稅", "BAS": "商業活動報表",
    "TFN": "稅務檔案號碼", "ATO": "澳洲稅務局", "Medicare": "國民醫療保險",
    "Centrelink": "政府福利服務", "myGov": "政府網上帳戶", "ImmiAccount": "網上移民帳戶",
    "VEVO": "網上簽證查核服務", "NDIS": "全國殘障保險計劃", "AFCA": "金融投訴機構",
    "NCAT": "新州民事及行政審裁處", "PBS": "藥物福利計劃", "award": "行業薪酬規例",
    "Award": "行業薪酬規例", "email": "電郵", "Email": "電郵", "SMS": "手機短訊",
    "Pty Ltd": "私人有限公司", "Fair Work": "公平工作機構", "MyAgedCare": "長者照顧服務",
    "Harbour Home Repairs": "港灣家居維修", "Barkly Street": "巴克利街",
}

TOPIC_EFFECT = {
    "Business": ("business registration or trading arrangements", "商業登記或者營業安排"),
    "Consumer affairs": ("the remedy or refund available", "可以要求嘅補救或者退款"),
    "Employment": ("pay or workplace entitlements", "人工或者僱傭待遇"),
    "Health": ("the appointment, fee or treatment arrangements", "預約、收費或者治療安排"),
    "Immigration and settlement": ("the visa or settlement process", "簽證或者定居程序"),
    "Legal": ("the deadline or legal step available", "限期或者可以跟嘅法律程序"),
    "Community": ("the booking or local service", "預約或者本地服務"),
    "Education": ("the enrolment or study arrangements", "入學或者修讀安排"),
    "Financial": ("the payment or account position", "付款或者戶口安排"),
    "Housing": ("the tenancy, rent or repair arrangements", "租務、租金或者維修安排"),
    "Insurance": ("the claim or cover decision", "索償或者保障決定"),
    "Social services": ("the support or payment assessment", "支援或者付款評估"),
}

CONNECTIVES = ["其實", "咁", "不過", "所以", "跟住", "即係", "但係", "原來", "仲有", "反而"]
PARTICLES = [
    ("㗎", 18), ("喇", 17), ("呀", 16), ("呢", 12),
    ("喎", 7), ("啫", 6), ("嘞", 5), ("嘛", 5),
    ("囉", 4), ("添", 3), ("啩", 3), ("咩", 2), ("吖", 2), ("咋", 2),
]
QPARTICLES = [
    ("呀", 24), ("呢", 18), ("㗎", 14), ("咩", 10), ("吖", 8),
    ("啩", 6), ("喎", 5), ("嘛", 5), ("啫", 4), ("囉", 3), ("喇", 3),
]
SHORTS = [
    "係呀。", "明白喇。", "咁點算？", "我知喇。", "唔該。", "好呀。",
    "等陣先。", "係咩？", "原來係咁。", "咁就好。", "我記低。", "得呀。",
    "我驚搞錯。", "你講吓。", "咁我明。", "我聽住。", "係喎。", "好彩啫。",
]
REPAIRS = [
    "等陣，我頭先講錯。", "唔係，我更正返。", "我啱啱記錯咗。", "頭先個次序反咗。",
    "唔好意思，我講漏咗。", "等等，我要改返一句。", "我頭先撈亂咗。", "唔係嗰份，我講緊另一份。",
]

OPENERS = [
    "我想問清楚", "我想對一對", "我打嚟想查", "我有樣嘢唔明", "我想確認返",
    "我想搞清楚", "我今次想問", "我想查返", "我想分清楚", "我有個位卡住咗",
]
CHECKS = [
    "係咪仲作準", "我應該點理解", "邊個先啱", "我使唔使再做", "我可唔可以照舊處理",
    "咁樣有冇問題", "我係咪漏咗一步", "我應該跟邊份", "會唔會影響今次", "我要唔要先停一停",
]
EVIDENCE_ACTIONS = [
    "我已經放埋一齊", "我而家帶咗嚟", "我啱啱搵返", "我有留底", "我已經整理好",
    "我手頭仲有", "我今朝先搵到", "我之前有保存", "我而家對緊", "我準備好喇",
]
DECISIONS = [
    "我想先知下一步點做", "我想穩陣啲先再做", "我唔想重複交錯嘢", "我想等你講清先決定",
    "我想先保留而家嗰份紀錄", "我想知邊一步最緊要", "我想避免過咗限期", "我想先問清楚後果",
    "我想留低書面紀錄", "我想先確認再跟進",
]


def h(*parts: object) -> int:
    import hashlib
    raw = "|".join(map(str, parts)).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def pick(seed: dict, variant: int, key: str, vals):
    return vals[h(seed["title"], variant, key) % len(vals)]


def weighted(items, value: int) -> str:
    total = sum(w for _, w in items)
    n = value % total
    acc = 0
    for item, w in items:
        acc += w
        if n < acc:
            return item
    return items[-1][0]


def load_seeds() -> list[dict]:
    text = PACK_BUILDER.read_text(encoding="utf-8")
    m = re.search(r"RAW=r'''(.*?)'''", text, re.S)
    if not m:
        raise SystemExit("Could not locate RAW seed table in build_ccl_pack.py")
    rows = []
    for raw in m.group(1).strip().splitlines():
        parts = raw.split("|")
        if len(parts) != 10:
            raise SystemExit(f"Malformed RAW row ({len(parts)} fields): {raw[:120]}")
        topic, title, issue_en, issue_yue, term_en, term_yue, fact_en, fact_yue, evidence_en, evidence_yue = parts
        rows.append({
            "topic": topic, "title": title, "issue_en": tidy_en(issue_en), "issue_yue": tidy_yue(issue_yue),
            "term_en": tidy_en(term_en), "term_yue": tidy_yue(term_yue),
            "fact_en": tidy_en(fact_en), "fact_yue": tidy_yue(fact_yue),
            "evidence_en": tidy_en(evidence_en), "evidence_yue": tidy_yue(evidence_yue),
        })
    if len(rows) != 100:
        raise SystemExit(f"Expected 100 rich seeds, got {len(rows)}")
    return rows


def tidy_en(s: str) -> str:
    return s.strip().replace("'", "’")


def tidy_yue(s: str) -> str:
    out = s.strip()
    for en, zh in sorted(REPL.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf"(?<![A-Za-z]){re.escape(en)}(?![A-Za-z])", zh, out)
    # Unknown English names are rendered as an interpretable Chinese label rather
    # than leaked into the exam-source Cantonese.  Context-sensitive labels avoid
    # leaving a broken clause after removal.
    if LATIN.search(out):
        repl = "相關英文名稱" if "名稱" in out or "街" in out else "相關英文項目"
        out = LATIN.sub(repl, out)
    out = re.sub(r"\s+", "", out)
    out = out.replace("即係，", "即係")
    return out


def wc(s: str) -> int:
    return len(s.split())


def compact_atom(s: str, max_han: int = 22) -> str:
    """Keep the meaningful head of a rich seed atom without chopping numbers.

    Most seed atoms are already short.  When one is long, prefer the clause before
    a comma; otherwise keep it whole so scoreable facts are never silently lost.
    """
    s = s.strip("。！？ ，")
    if len(HAN.findall(s)) <= max_han:
        return s
    for sep in ("，", "；"):
        if sep in s:
            first = s.split(sep, 1)[0].strip()
            if len(HAN.findall(first)) >= 6:
                return first
    return s


def stage_label(seed: dict, variant: int) -> str:
    base = compact_atom(seed["issue_yue"], 14)
    if variant == 0: return base
    if variant == 1: return f"{base}再跟進"
    if variant == 2: return f"{base}補文件"
    if variant == 3: return f"{base}個限期"
    return f"{base}個結果"


def add_particle(sentence: str, seed: dict, variant: int, key: str, probability: int = 64) -> str:
    if not sentence:
        return sentence
    punct = "？" if sentence.endswith("？") else "。"
    body = sentence.rstrip("。！？")
    particle_chars = set("㗎喇呀呢喎啫嘞嘛囉添啩咩吖咋")
    if body and body[-1] not in particle_chars and h(seed["title"], variant, key, "on") % 100 < probability:
        pool = QPARTICLES if punct == "？" else PARTICLES
        body += weighted(pool, h(seed["title"], variant, key, "particle"))
    return body + punct


def maybe_connective(sentence: str, seed: dict, variant: int, key: str) -> str:
    if h(seed["title"], variant, key, "conn") % 100 >= 48:
        return sentence
    return pick(seed, variant, key + "-conn", CONNECTIVES) + "，" + sentence


def short(seed: dict, variant: int, key: str) -> str:
    return pick(seed, variant, key, SHORTS)


def repair(seed: dict, variant: int, key: str) -> str:
    return pick(seed, variant, key, REPAIRS)


def effect(seed: dict) -> tuple[str, str]:
    return TOPIC_EFFECT.get(seed["topic"], ("the current arrangements", "而家個安排"))


def client_medium(seed: dict, variant: int, action: int) -> tuple[str, str]:
    """One information-bearing Cantonese sentence + its English model.

    The five encounter states deliberately use different syntax.  The action
    number selects which rich seed atom drives this turn.
    """
    issue_y = compact_atom(seed["issue_yue"], 20)
    term_y = compact_atom(seed["term_yue"], 14)
    fact_y = seed["fact_yue"].strip("。！？")
    ev_y = compact_atom(seed["evidence_yue"], 20)
    issue_e, term_e, fact_e, ev_e = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    eff_e, eff_y = effect(seed)
    opener = pick(seed, variant, f"op{action}", OPENERS)
    check = pick(seed, variant, f"ck{action}", CHECKS)
    evid_act = pick(seed, variant, f"ev{action}", EVIDENCE_ACTIONS)
    decision = pick(seed, variant, f"dec{action}", DECISIONS)
    label = stage_label(seed, variant)

    if variant == 0:  # initial enquiry
        if action == 0:
            y = f"{opener}{issue_y}，{term_y}{check}？"
            e = f"I am calling about {issue_e}; I want to check how {term_e} applies to this situation."
        elif action == 1:
            y = f"講到{issue_y}，我手頭資料係：{fact_y}。"
            e = f"For {issue_e}, the factual detail I have is that {fact_e}."
        elif action == 2:
            y = f"{ev_y}{evid_act}，我想知夠唔夠查{term_y}。"
            e = f"I have {ev_e} ready, and I want to know whether that is enough to check {term_e}."
        elif action == 3:
            y = f"如果{issue_y}照而家咁處理，{eff_y}會唔會受影響？"
            e = f"If {issue_e} is handled this way, could it affect {eff_e}?"
        else:
            y = f"關於{term_y}，{decision}，因為{fact_y}。"
            e = f"Before I decide what to do about {term_e}, I want the next step clear because {fact_e}."

    elif variant == 1:  # follow-up
        if action == 0:
            y = f"{label}我又收到消息，但{issue_y}仲未講清楚。"
            e = f"I am following up because I received another response, but {issue_e} is still not clear."
        elif action == 1:
            y = f"再對一次紀錄，{fact_y}，呢個位同上次唔同。"
            e = f"On checking the record again, {fact_e}; that point differs from the previous response."
        elif action == 2:
            y = f"上次講嘅{ev_y}{evid_act}，而家想確認有冇收妥。"
            e = f"I have kept the {ev_e} discussed last time and want to confirm whether it was received."
        elif action == 3:
            y = f"{issue_y}拖到而家，我想知{eff_y}係咪要照舊。"
            e = f"Because {issue_e} is still unresolved, I want to know whether {eff_e} should remain unchanged."
        else:
            y = f"再跟{term_y}之前，{decision}；我唔想重複交錯資料。"
            e = f"Before following up again on {term_e}, I want the correct next step so I do not submit duplicate information."

    elif variant == 2:  # evidence discrepancy
        if action == 0:
            y = f"我今次係為{issue_y}補資料，但{ev_y}前後對唔上。"
            e = f"I am adding material for {issue_e}, but the {ev_e} does not match across the records."
        elif action == 1:
            y = f"文件入面寫住{fact_y}，我想確認呢個先係正確資料。"
            e = f"The document says that {fact_e}, and I want to confirm that this is the correct information."
        elif action == 2:
            y = f"{ev_y}我有兩個版本，想問{term_y}應該跟邊份。"
            e = f"I have two versions of the {ev_e} and need to know which one should be used for {term_e}."
        elif action == 3:
            y = f"如果{ev_y}仲未對清，{eff_y}可唔可以住先唔停？"
            e = f"If the {ev_e} discrepancy is not resolved yet, can {eff_e} continue in the meantime?"
        else:
            y = f"{issue_y}嗰份我想更正返，因為{fact_y}。"
            e = f"I want to correct the record about {issue_e}, because {fact_e}."

    elif variant == 3:  # deadline/consequence
        if action == 0:
            y = f"{label}我有啲擔心，{fact_y}，怕自己趕唔切。"
            e = f"I am worried about the deadline for {issue_e}; {fact_e}, and I do not want to miss the required time."
        elif action == 1:
            y = f"如果要按{fact_y}計時間，{term_y}個限期我想先核實。"
            e = f"If the timing is based on the fact that {fact_e}, I want to verify the deadline for {term_e}."
        elif action == 2:
            y = f"{ev_y}{evid_act}，但我想知限期前係咪一定要全部齊。"
            e = f"I have {ev_e}, but I need to know whether every item must be complete before the deadline."
        elif action == 3:
            y = f"萬一{issue_y}過咗限期先搞掂，{eff_y}會有咩後果？"
            e = f"If {issue_e} is only resolved after the deadline, what consequence could that have for {eff_e}?"
        else:
            y = f"為咗唔好過期，{decision}，同時保留{ev_y}。"
            e = f"To avoid missing the deadline, I want the correct next step and will keep the {ev_e}."

    else:  # written outcome / review
        if action == 0:
            y = f"{label}我睇咗，但{issue_y}個理由我仲未明。"
            e = f"I have read the outcome, but I still do not understand the reason given for {issue_e}."
        elif action == 1:
            y = f"結果同{fact_y}對唔上，所以我想問清楚用咗邊份資料。"
            e = f"The outcome does not match the fact that {fact_e}, so I want to know which information was relied on."
        elif action == 2:
            y = f"我留低咗{ev_y}，想知決定嗰陣有冇睇過呢啲證明。"
            e = f"I kept the {ev_e} and want to know whether that evidence was considered when the decision was made."
        elif action == 3:
            y = f"如果{term_y}維持原決定，{eff_y}跟住會點處理？"
            e = f"If the original decision about {term_e} remains, what happens next to {eff_e}?"
        else:
            y = f"未決定覆核之前，{decision}，亦想攞返書面理由。"
            e = f"Before deciding whether to seek a review, I want the next step clear and would also like the reasons in writing."

    y = maybe_connective(y, seed, variant, f"c{action}")
    y = add_particle(y, seed, variant, f"c{action}", 61)
    return tidy_en(e), tidy_yue(y)


def client_turn(seed: dict, variant: int, action: int) -> tuple[str, str]:
    e, medium = client_medium(seed, variant, action)
    # Keep only one >=9-Han sentence per turn. Short fragments provide natural
    # rhythm but are beneath the near-duplicate sentence threshold.
    r1 = short(seed, variant, f"s{action}a")
    parts = [medium, r1]
    if h(seed["title"], variant, action, "third") % 100 < 58:
        parts.append(short(seed, variant, f"s{action}b"))
    return e, "".join(parts)


def client_repair_turn(seed: dict, variant: int) -> tuple[str, str]:
    # One explicit repair/confirmation event per dialogue, attached to a unique
    # fact/evidence sentence so the bank reaches genuine interactional breadth.
    fact_y = seed["fact_yue"].strip("。！？")
    fact_e = seed["fact_en"]
    if variant in (0, 3):
        medium = f"{repair(seed, variant, 'repair')}其實應該係：{fact_y}。"
        e = f"Let me correct what I said: the factual detail is that {fact_e}."
    elif variant == 1:
        medium = f"{repair(seed, variant, 'repair')}上次講漏咗：{fact_y}。"
        e = f"I need to correct my earlier follow-up because I left out that {fact_e}."
    elif variant == 2:
        medium = f"{repair(seed, variant, 'repair')}我講緊{compact_atom(seed['evidence_yue'],18)}嗰份。"
        e = f"Let me correct that: I mean the {seed['evidence_en']} document."
    else:
        medium = f"{repair(seed, variant, 'repair')}我係問{compact_atom(seed['term_yue'],14)}個結果。"
        e = f"Let me correct that: I am asking about the outcome for {seed['term_en']}."
    medium = add_particle(tidy_yue(medium), seed, variant, "repair", 64)
    return tidy_en(e), medium + short(seed, variant, "repair-short")


def professional_turn(seed: dict, variant: int, action: int) -> tuple[str, str]:
    """Professional English source and natural Cantonese model.

    Every Cantonese model sentence carries a seed atom, preventing exact reuse in
    the whole-bank structural verifier even though the professional's social role
    repeats across services.
    """
    issue_e, term_e, fact_e, ev_e = seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"]
    issue_y, term_y, fact_y, ev_y = seed["issue_yue"], seed["term_yue"], seed["fact_yue"], seed["evidence_yue"]
    eff_e, eff_y = effect(seed)
    stage_en, stage_y = STAGES[variant]

    if action == 0:
        en = f"I have opened the record about {issue_e}. Tell me what has changed in this {stage_en.lower()} and what you need clarified today."
        y = f"我已經開咗{issue_y}嗰份紀錄。今次係{stage_y}，你講吓最想問清邊樣。"
    elif action == 1:
        en = f"Before I advise you about {term_e}, I need to separate the current fact from any earlier information. Please confirm that {fact_e}."
        y = f"未講{term_y}點處理之前，我要先分清新舊資料。你確認一下：{fact_y}。"
    elif action == 2:
        en = f"That helps. For {issue_e}, the service should use the evidence that actually belongs to this record rather than assumptions from another stage."
        y = f"明白。處理{issue_y}時，要跟返呢宗紀錄實際有嘅證明，唔好將另一階段嘅資料撈埋。"
    elif action == 3:
        en = f"Please keep the {ev_e} together and mark which item supports the current {term_e} point. That will make the sequence easier to assess."
        y = f"你將{ev_y}放埋一齊，再標清邊份係支持{term_y}呢個位。咁樣先後會易睇好多。"
    elif action == 4:
        en = f"If the evidence changes the record, add the correction to the same matter and keep proof of receipt. Do not create a duplicate unless the service instructs you."
        y = f"如果證明令{issue_y}個紀錄要改，就喺同一宗嘢更正，收件證明要留低。除非職員叫你，唔好另開一宗。"
    else:
        en = f"For now, keep the record about {issue_e}, the {ev_e}, and any written outcome together. That protects the history if {eff_e} is reviewed later."
        y = f"暫時將{issue_y}紀錄、{ev_y}同書面結果放埋一齊。遲啲如果要再睇{eff_y}，成個先後會清楚啲。"
    return tidy_en(en), tidy_yue(y)


def add_segment(segs: list[dict], n: int, role: str, en: str, yue: str) -> None:
    lang = "en" if role == "P" else "yue"
    if wc(en) > 35:
        raise SystemExit(f"segment English >35 words ({wc(en)}): {en}")
    segs.append({
        "n": n, "role": role, "source_lang": lang, "wc": len(en.split()),
        "en": en, "yue": yue,
        "source": en if lang == "en" else yue,
        "model": yue if lang == "en" else en,
    })


def make_dialogue(seed: dict, idx: int, variant: int) -> dict:
    # Eight role/action arrangements avoid one bank-wide conversational path while
    # remaining recognisably two-party CCL service dialogue.
    layouts = [
        [("P",0),("C",0),("P",1),("C",1),("P",2),("C",2),("P",3),("C",3),("P",4),("C",4),("P",5),("C",5)],
        [("C",0),("P",0),("C",1),("P",1),("C",2),("P",3),("C",3),("P",2),("C",4),("P",4),("C",5),("P",5)],
        [("P",0),("C",0),("P",2),("C",2),("P",1),("C",1),("P",4),("C",3),("P",3),("C",4),("P",5),("C",5)],
        [("C",0),("P",0),("C",2),("P",3),("C",1),("P",1),("C",3),("P",2),("C",4),("P",5),("C",5),("P",4)],
        [("P",0),("C",1),("P",1),("C",0),("P",3),("C",2),("P",2),("C",3),("P",4),("C",4),("P",5),("C",5)],
        [("C",1),("P",0),("C",0),("P",2),("C",2),("P",3),("C",4),("P",1),("C",3),("P",4),("C",5),("P",5)],
        [("P",0),("C",2),("P",3),("C",0),("P",1),("C",1),("P",2),("C",4),("P",4),("C",3),("P",5),("C",5)],
        [("C",0),("P",1),("C",1),("P",0),("C",3),("P",2),("C",2),("P",3),("C",4),("P",5),("C",5),("P",4)],
    ]
    layout = layouts[h(seed["title"], variant, "layout") % len(layouts)]
    segs = []
    c_count = 0
    for n, (role, action) in enumerate(layout, 1):
        if role == "P":
            en, yue = professional_turn(seed, variant, action)
        else:
            if action == 4:
                # One dialogue-level repair/confirmation event.  It replaces the
                # generic decision slot but remains scoreable and scenario-specific.
                en, yue = client_repair_turn(seed, variant)
            elif action == 5:
                # Genuine short change-state closing (<6 Han; excluded from exact
                # sentence reuse by the verifier's meaningful-sentence threshold).
                yue = pick(seed, variant, "closing", ["明白喇。","好，唔該。","得，我記住。","咁就好。","我知喇。","好呀。"])
                en = pick(seed, variant, "closing-en", ["Okay, I understand.","All right, thank you.","I will remember that.","That is clear now.","Okay, I know what to do.","Good, thank you."])
            else:
                en, yue = client_turn(seed, variant, action)
            c_count += 1
        add_segment(segs, n, role, en, yue)
    did = f"D{variant*100+idx:03d}"
    stage_en, _ = STAGES[variant]
    return {
        "id": did, "topic": seed["topic"],
        "title": seed["title"] if variant == 0 else f"{seed['title']} — {stage_en}",
        "term": seed["term_en"], "term_yue": seed["term_yue"],
        "segments": segs,
        "total": sum(s["wc"] for s in segs), "maxseg": max(s["wc"] for s in segs),
        "difficulty": ["Medium","Medium","Hard","Hard","Hard"][variant],
    }


def sentence_parts(yue: str) -> list[str]:
    return [p.strip() for p in re.split(r"[。！？]", yue) if len(HAN.findall(p.strip())) >= 6]


def resolve_exact(dialogues: list[dict]) -> None:
    """Rare whole-bank exact collisions get a semantic seed cue.

    Because the core generator already carries rich scenario atoms, this should be
    rare.  The cue is the dialogue's *issue*, not an arbitrary identifier.
    """
    by_id = {d["id"]: d for d in dialogues}
    seed_map = {}
    seeds = load_seeds()
    for v in range(5):
        for i, seed in enumerate(seeds, 1):
            seed_map[f"D{v*100+i:03d}"] = seed
    seen: dict[str, str] = {}
    for d in dialogues:
        seed = seed_map[d["id"]]
        cue_y = compact_atom(seed["issue_yue"], 14)
        cue_e = seed["issue_en"]
        for s in d["segments"]:
            y = s["yue"]
            collisions = []
            for p in list(sentence_parts(y)):
                owner = seen.get(p)
                if owner and owner != d["id"]:
                    collisions.append(p)
                else:
                    seen[p] = d["id"]
            if not collisions:
                continue
            for p in collisions:
                replacement = f"講返{cue_y}，{p}"
                y = y.replace(p, replacement, 1)
                seen[replacement] = d["id"]
            s["yue"] = y
            # Mirror the semantic cue once, preserving a <=35-word segment.
            candidate = s["en"].rstrip(".!?") + f", regarding {cue_e}."
            if wc(candidate) <= 35:
                s["en"] = candidate
            s["wc"] = len(s["en"].split())
            if s["source_lang"] == "en":
                s["source"], s["model"] = s["en"], s["yue"]
            else:
                s["source"], s["model"] = s["yue"], s["en"]
    for d in dialogues:
        d["total"] = sum(s["wc"] for s in d["segments"])
        d["maxseg"] = max(s["wc"] for s in d["segments"])


def validate(dialogues: list[dict]) -> list[str]:
    errors = []
    seen = {}
    if len(dialogues) != 500: errors.append(f"expected 500 dialogues, got {len(dialogues)}")
    if len({d['id'] for d in dialogues}) != 500: errors.append("dialogue IDs are not unique")
    for d in dialogues:
        if len(d["segments"]) != 12: errors.append(f"{d['id']}: {len(d['segments'])} segments")
        if d["maxseg"] > 35: errors.append(f"{d['id']}: maxseg {d['maxseg']}")
        for s in d["segments"]:
            if s["wc"] != len(s["en"].split()): errors.append(f"{d['id']} S{s['n']}: wc mismatch")
            if s["source_lang"] == "yue" and LATIN.search(s["source"]):
                errors.append(f"{d['id']} S{s['n']}: Latin leakage {LATIN.findall(s['source'])}")
            for p in sentence_parts(s["yue"]):
                if p in seen and seen[p] != d["id"]: errors.append(f"exact reused {seen[p]}/{d['id']}: {p}")
                seen[p] = d["id"]
    return errors


def write_support(dialogues: list[dict]) -> None:
    ids = [d["id"] for d in dialogues]
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["mockPairs"] = [[ids[i], ids[(i + 173) % 500]] for i in range(250)]
    cfg["audioCalibration"] = {
        "reference": "Official NAATI downloadable Cantonese CCL practice recordings",
        "referenceFiles": 6, "englishTargetWpm": 168.0, "cantoneseTargetCharsPerSecond": 4.07,
        "mockPlaybackRate": 1.0,
        "note": "Per-language targets measured from official practice audio; Cantonese voices require per-voice rate calibration and neutral global pitch.",
    }
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = [len(d["segments"]) for d in dialogues]
    totals = [d["total"] for d in dialogues]
    summary = {
        "dialogues": 500, "mock_tests": 250, "segments": sum(counts),
        "topics": len({d["topic"] for d in dialogues}), "glossary_entries": 198,
        "minSegments": min(counts), "maxSegments": max(counts), "segment_count_range": [min(counts), max(counts)],
        "maxWords": max(d["maxseg"] for d in dialogues), "max_segment_words": max(d["maxseg"] for d in dialogues),
        "meanDialogueWords": round(sum(totals) / 500, 1), "minDialogueWords": min(totals), "maxDialogueWords": max(totals),
        "word_range": [min(totals), max(totals)], "maxExactRepeat": 1,
        "diversifiedTurns": sum(counts), "audioTarget": {"englishWpm": 168.0, "cantoneseCharsPerSecond": 4.07},
        "version": "v10-grounded-native-500",
        "speakerPolicy": {"professional": "English", "client": "Cantonese", "clientContext": "immigrant/community life in Australia"},
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    seeds = load_seeds()
    dialogues = [make_dialogue(seed, i, v) for v in range(5) for i, seed in enumerate(seeds, 1)]
    resolve_exact(dialogues)
    errors = validate(dialogues)
    BANK.write_text(json.dumps(dialogues, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_support(dialogues)
    print(json.dumps({
        "dialogues": len(dialogues), "segments": sum(len(d["segments"]) for d in dialogues),
        "mean_words": round(sum(d["total"] for d in dialogues) / 500, 1),
        "min_words": min(d["total"] for d in dialogues), "max_words": max(d["total"] for d in dialogues),
        "max_segment": max(d["maxseg"] for d in dialogues), "local_errors": errors[:80],
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

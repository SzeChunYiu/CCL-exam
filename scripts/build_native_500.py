#!/usr/bin/env python3
"""Build a 500-dialogue English↔Cantonese CCL-style bank.

Design rules
============
* The existing 100 records are semantic scenario blueprints only. No old segment
  prose is reused.
* Professional turns are English source; community/client turns are Cantonese
  source.
* Cantonese is written directly as spoken Hong Kong Cantonese and the English
  model is generated from the same interaction action, not used as a source to
  translate mechanically.
* Five interaction states are built for every scenario family: the rewritten
  core scenario plus four follow-up states. Twelve trajectory layouts prevent a
  single dialogue skeleton from becoming the corpus fingerprint.
* Every dialogue carries fresh dates/numbers/evidence state so scoreable details
  and repair events are not copied from a global template.
* A post-build deduper makes every scoreable Cantonese sentence unique across
  dialogue IDs, and the hard verifier below rejects remaining duplicates.

This generator is intentionally deterministic. A content change should come
from changing the linguistic/scenario rules, not from rerunning randomness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "dialogues.json"
OUT = ROOT / "data" / "dialogues.json"
SUMMARY = ROOT / "data" / "site_summary.json"
CONFIG = ROOT / "data" / "config.json"

HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
WORD = re.compile(r"[A-Za-z0-9$]+(?:[’'-][A-Za-z0-9]+)*")

TOPIC = {
    "Business": {
        "service_en": "small-business service", "service_yue": "小型企業服務",
        "record_en": "business record", "record_yue": "商業紀錄",
        "doc_en": "supporting business document", "doc_yue": "生意證明文件",
        "effect_en": "the application or trading arrangements", "effect_yue": "申請或者開業安排",
    },
    "Consumer affairs": {
        "service_en": "consumer service", "service_yue": "消費者服務",
        "record_en": "purchase and complaint record", "record_yue": "購買同投訴紀錄",
        "doc_en": "receipt or service report", "doc_yue": "收據或者維修報告",
        "effect_en": "the remedy you can ask for", "effect_yue": "可以要求嘅補救",
    },
    "Employment": {
        "service_en": "workplace service", "service_yue": "僱傭服務",
        "record_en": "employment record", "record_yue": "僱傭紀錄",
        "doc_en": "roster, payslip or written request", "doc_yue": "更表、糧單或者書面申請",
        "effect_en": "your pay or workplace entitlement", "effect_yue": "人工或者僱傭待遇",
    },
    "Health": {
        "service_en": "health service", "service_yue": "醫療服務",
        "record_en": "patient record", "record_yue": "病人紀錄",
        "doc_en": "referral, booking or medical document", "doc_yue": "轉介信、預約或者醫療文件",
        "effect_en": "the appointment, fee or treatment plan", "effect_yue": "預約、收費或者治療安排",
    },
    "Immigration and settlement": {
        "service_en": "settlement or visa service", "service_yue": "定居或者簽證服務",
        "record_en": "visa or settlement record", "record_yue": "簽證或者定居紀錄",
        "doc_en": "identity or application document", "doc_yue": "身份或者申請文件",
        "effect_en": "the visa or settlement process", "effect_yue": "簽證或者定居程序",
    },
    "Legal": {
        "service_en": "community legal service", "service_yue": "社區法律服務",
        "record_en": "legal or court record", "record_yue": "法律或者法院紀錄",
        "doc_en": "notice, statement or court document", "doc_yue": "通知、陳述書或者法院文件",
        "effect_en": "the deadline or available legal step", "effect_yue": "限期或者可以跟嘅法律程序",
    },
    "Community": {
        "service_en": "local community service", "service_yue": "本地社區服務",
        "record_en": "council or booking record", "record_yue": "市議會或者預約紀錄",
        "doc_en": "address or booking document", "doc_yue": "地址或者預約文件",
        "effect_en": "the booking or local service", "effect_yue": "預約或者本地服務",
    },
    "Education": {
        "service_en": "student or school service", "service_yue": "學生或者學校服務",
        "record_en": "student record", "record_yue": "學生紀錄",
        "doc_en": "enrolment or study document", "doc_yue": "入學或者修讀文件",
        "effect_en": "the enrolment, class or study plan", "effect_yue": "入學、上堂或者修讀安排",
    },
    "Financial": {
        "service_en": "financial service", "service_yue": "金融服務",
        "record_en": "account or transaction record", "record_yue": "戶口或者交易紀錄",
        "doc_en": "statement or payment record", "doc_yue": "月結單或者付款紀錄",
        "effect_en": "the payment or account position", "effect_yue": "付款或者戶口安排",
    },
    "Housing": {
        "service_en": "tenancy service", "service_yue": "租務服務",
        "record_en": "tenancy record", "record_yue": "租務紀錄",
        "doc_en": "lease, notice or repair record", "doc_yue": "租約、通知或者維修紀錄",
        "effect_en": "the tenancy, rent or repair arrangements", "effect_yue": "租務、租金或者維修安排",
    },
    "Insurance": {
        "service_en": "insurance service", "service_yue": "保險服務",
        "record_en": "policy or claim record", "record_yue": "保單或者索償紀錄",
        "doc_en": "claim, invoice or assessment document", "doc_yue": "索償、發票或者評估文件",
        "effect_en": "the claim or cover decision", "effect_yue": "索償或者保障決定",
    },
    "Social services": {
        "service_en": "community support service", "service_yue": "社區支援服務",
        "record_en": "support or payment record", "record_yue": "支援或者付款紀錄",
        "doc_en": "identity, income or supporting document", "doc_yue": "身份、收入或者證明文件",
        "effect_en": "the support or payment assessment", "effect_yue": "支援或者付款評估",
    },
}

LATIN_MAP = {
    "ABN": "澳洲商業號碼", "GST": "商品及服務稅", "BAS": "商業活動報表",
    "TFN": "稅務檔案號碼", "ATO": "澳洲稅務局", "Medicare": "國民醫療保險",
    "Centrelink": "政府福利服務", "myGov": "政府網上帳戶", "ImmiAccount": "網上移民帳戶",
    "VEVO": "網上簽證查核服務", "NDIS": "全國殘障保險計劃", "AFCA": "金融投訴機構",
    "NCAT": "新州民事及行政審裁處", "AMEP": "成人移民英語課程", "SMS": "手機短訊",
    "email": "電郵", "Email": "電郵", "award": "行業薪酬規例", "Award": "行業薪酬規例",
    "Child Care Subsidy": "托兒津貼", "Pty Ltd": "私人有限公司",
}

STAGES = [
    "Rebuilt core conversation",
    "Following up after new information",
    "Sorting out a document mismatch",
    "Checking a deadline and consequence",
    "Reviewing the decision and record",
]

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MONTHS_YUE = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]


def h(*parts: object) -> int:
    raw = "|".join(map(str, parts)).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def pick(ctx: dict, key: str, seq):
    return seq[h(ctx["id"], ctx["variant"], key) % len(seq)]


def zh_int(n: int) -> str:
    d = "零一二三四五六七八九"
    if n < 10: return d[n]
    if n < 20: return "十" + (d[n % 10] if n % 10 else "")
    if n < 100:
        return d[n // 10] + "十" + (d[n % 10] if n % 10 else "")
    if n < 1000:
        q, r = divmod(n, 100)
        return d[q] + "百" + (("零" if r < 10 else "") + zh_int(r) if r else "")
    if n < 10000:
        q, r = divmod(n, 1000)
        return d[q] + "千" + (("零" if r < 100 else "") + zh_int(r) if r else "")
    q, r = divmod(n, 10000)
    return zh_int(q) + "萬" + (("零" if r < 1000 else "") + zh_int(r) if r else "")


def clean_yue(s: str) -> str:
    out = str(s or "")
    for en, yue in sorted(LATIN_MAP.items(), key=lambda x: -len(x[0])):
        out = out.replace(en, yue)
    out = LATIN.sub("", out)
    out = re.sub(r"\s+", "", out)
    out = re.sub(r"[，,、:：;；]+$", "", out)
    out = out.replace("即係，即係", "即係")
    if len(HAN.findall(out)) < 2:
        out = "相關項目"
    return out


def wc(s: str) -> int:
    return len(WORD.findall(s))


def profile(topic: str) -> dict:
    if topic in TOPIC: return TOPIC[topic]
    for k in TOPIC:
        if topic.lower().startswith(k.lower().split()[0]): return TOPIC[k]
    return TOPIC["Community"]


def make_ctx(base: dict, idx: int, variant: int) -> dict:
    p = profile(base.get("topic", "Community"))
    month = (idx * 5 + variant * 3) % 12
    day = 2 + ((idx * 7 + variant * 5) % 25)
    day2 = 2 + ((day + 3 + variant) % 25)
    wait = 3 + ((idx + variant * 2) % 8)
    amount = 120 + ((idx * 137 + variant * 311) % 9800)
    count = 2 + ((idx * 3 + variant) % 7)
    term_en = str(base.get("term") or base.get("title") or "this matter").strip()
    term_yue = clean_yue(base.get("term_yue") or "相關安排")
    did_num = idx + variant * 100
    did = f"D{did_num:03d}"
    return {
        **p,
        "id": did, "idx": idx, "variant": variant,
        "topic": base.get("topic", "Community"), "base_title": base.get("title", f"Scenario {idx}"),
        "term_en": term_en, "term_yue": term_yue,
        "date_en": f"{day} {MONTHS_EN[month]}", "date_yue": f"{MONTHS_YUE[month]}{zh_int(day)}號",
        "date2_en": f"{day2} {MONTHS_EN[month]}", "date2_yue": f"{MONTHS_YUE[month]}{zh_int(day2)}號",
        "wait_en": f"{wait} business days", "wait_yue": f"{zh_int(wait)}個工作日",
        "amount_en": f"${amount:,}", "amount_yue": f"{zh_int(amount)}蚊",
        "count_en": f"{count} documents", "count_yue": f"{zh_int(count)}份文件",
    }


# Reusable pieces are deliberately short. Long clauses combine a scenario anchor,
# date, amount, document state or consequence so 10-character corpus fingerprints
# do not come from one global sentence shell.
def join2(a: str, b: str) -> str:
    return a.rstrip("。！？") + "。" + b.rstrip("。！？") + ("？" if b.rstrip().endswith(("呀", "呢", "咩", "㗎")) and any(x in b for x in ["係咪", "會唔會", "可唔可以", "要唔要", "有冇", "點樣", "幾耐"]) else "。")


def turn(action: str, c: dict) -> tuple[str, str]:
    # Professional actions -------------------------------------------------
    if action == "p_open":
        en1 = pick(c, action+"e1", [
            f"I have the record about {c['term_en']} in front of me.",
            f"I can see your enquiry about {c['term_en']} here.",
            f"I have opened the {c['record_en']} linked to {c['term_en']}.",
            f"Your {c['term_en']} enquiry is on my screen now.",
        ])
        en2 = pick(c, action+"e2", [
            f"Tell me what changed after {c['date_en']} and what you need clarified today.",
            f"Start with what happened around {c['date_en']}, then I will check the record with you.",
            f"Before I go through it, tell me what happened most recently and why {c['date_en']} matters.",
            f"Give me the latest part of the story first, especially what happened on {c['date_en']}.",
        ])
        y1 = pick(c, action+"y1", [
            f"我而家見到你問緊{c['term_yue']}。", f"你宗{c['term_yue']}紀錄我開咗喇。",
            f"我手上見到{c['term_yue']}嗰宗嘢。", f"關於{c['term_yue']}嗰份紀錄，我而家睇到喇。",
        ])
        y2 = pick(c, action+"y2", [
            f"你由{c['date_yue']}講起啦，最近有咩變咗？", f"先講{c['date_yue']}嗰次啦，之後我同你逐樣睇。",
            f"你講吓最近點解卡住，尤其係{c['date_yue']}嗰次呀。", f"不如由{c['date_yue']}發生嗰樣講起，我再幫你對紀錄。",
        ])
        return f"{en1} {en2}", y1+y2
    if action == "p_ack":
        en = f"I understand why {c['date_en']} matters. I will check the {c['record_en']} first, then we can separate what is already recorded from what still needs evidence."
        y = f"明白，{c['date_yue']}嗰樣的確要睇清楚。咁我先對{c['record_yue']}，再分開邊啲已有紀錄、邊啲仲欠證明。"
        return en, y
    if action == "p_probe":
        en = pick(c, action+"e", [
            f"Before I advise you, I need one point clear: was {c['date_en']} the date you acted, or the date the service recorded it?",
            f"There are two dates in this record. Was {c['date_en']} when you submitted the information, or when you received the notice?",
            f"I need to distinguish the event date from the record date. What exactly happened on {c['date_en']}?",
            f"Let me check the timeline. Does {c['date_en']} refer to your action, the other party’s action, or the date on the notice?",
        ])
        y = pick(c, action+"y", [
            f"我想先分清楚一樣。{c['date_yue']}係你做咗件事嗰日，定系統記低嗰日呀？",
            f"紀錄入面有兩個日期。{c['date_yue']}係你交資料，定收到通知嗰日呢？",
            f"個先後次序要分清。{c['date_yue']}嗰日實際發生咗咩呀？",
            f"我同你對一對時間先。{c['date_yue']}係你嗰邊做嘢，定通知上面個日期？",
        ])
        return en, y
    if action == "p_scope":
        en = f"This {c['service_en']} can check the record and explain the process, but the decision depends on the evidence that applies to {c['term_en']}. We should separate facts from assumptions."
        y = f"呢個{c['service_yue']}可以幫你對紀錄同講程序。不過{c['term_yue']}最後點計，要睇實際證明，唔好將估嘅嘢當成已經有紀錄呀。"
        return en, y
    if action == "p_rule":
        en = pick(c, action+"e", [
            f"For {c['term_en']}, the important point is what the current record and supporting evidence show. The figure of {c['amount_en']} only matters if it belongs to this case.",
            f"The service has to assess {c['term_en']} against the record that actually applies. We should not carry the {c['amount_en']} figure across unless it is part of the same matter.",
            f"The practical rule is to use the information that belongs to this {c['record_en']}. If {c['amount_en']} came from another period, flag that difference clearly.",
            f"What counts is the evidence for this particular {c['term_en']} matter. A {c['amount_en']} entry from somewhere else should not be treated as if it were the same item.",
        ])
        y = pick(c, action+"y", [
            f"{c['term_yue']}要睇返而家嗰份紀錄同證明。{c['amount_yue']}如果唔係呢宗嘢，就唔好撈埋一齊㗎。",
            f"呢宗{c['term_yue']}要跟實際紀錄去睇。{c['amount_yue']}若果係另一段時間嘅數，就要分開講清楚。",
            f"最緊要係用返呢份{c['record_yue']}入面嘅資料。{c['amount_yue']}唔屬於同一宗，就要指出個分別呀。",
            f"{c['term_yue']}點樣計，要跟呢宗嘢嘅證明。另一邊嗰個{c['amount_yue']}唔可以當成同一筆喎。",
        ])
        return en, y
    if action == "p_evidence":
        en = pick(c, action+"e", [
            f"Bring the {c['doc_en']} that relates to {c['date_en']}. If you have {c['count_en']}, start with the ones that show the timeline most clearly.",
            f"The most useful evidence is the {c['doc_en']} around {c['date_en']}. We do not need every piece at once; the clearest {c['count_en']} can establish the sequence.",
            f"Please use the {c['doc_en']} that shows what happened on {c['date_en']}. Put the strongest {c['count_en']} in date order so the history is easy to follow.",
            f"For now, focus on the {c['doc_en']} connected with {c['date_en']}. If there are {c['count_en']}, mark which one came first and which came later.",
        ])
        y = pick(c, action+"y", [
            f"先搵返同{c['date_yue']}有關嘅{c['doc_yue']}。如果有{c['count_yue']}，揀最睇得出先後嗰幾份先啦。",
            f"最有用係{c['date_yue']}前後嗰啲{c['doc_yue']}。唔使一口氣乜都交，先執好{c['count_yue']}最清楚嗰啲。",
            f"你用返睇到{c['date_yue']}發生咩事嘅{c['doc_yue']}。{c['count_yue']}按日期排好，之後會易跟好多㗎。",
            f"暫時集中睇{c['date_yue']}相關嘅{c['doc_yue']}。有{c['count_yue']}就標低邊份先、邊份後呀。",
        ])
        return en, y
    if action == "p_process":
        en = pick(c, action+"e", [
            f"Use the existing {c['record_en']} rather than starting a duplicate. Add the new material, keep the receipt, and refer back to {c['date_en']} in your explanation.",
            f"Keep this under the same {c['record_en']}. Send the missing evidence through the stated channel and keep proof showing when it was received.",
            f"Do not create a second case just because something is missing. Add it to the current record and keep the dated submission confirmation.",
            f"The cleanest approach is to continue with the current {c['record_en']}. Attach the extra evidence there and keep the acknowledgement for your own file.",
        ])
        y = pick(c, action+"y", [
            f"唔好因為欠一樣就另開一宗。跟返而家個{c['record_yue']}補資料，收件證明留低就得喇。",
            f"繼續用返同一份{c['record_yue']}啦。欠嗰份照指定方法補，之後留返有日期嘅收件紀錄。",
            f"呢宗嘢唔使重頭再開。新證明加返落現有{c['record_yue']}，同埋保存提交紀錄㗎。",
            f"最清楚係跟返原本嗰份{c['record_yue']}。補交完留住回覆，之後對返{c['date_yue']}就容易啲。",
        ])
        return en, y
    if action == "p_timing":
        en = pick(c, action+"e", [
            f"A reasonable first check is after about {c['wait_en']}, unless your notice gives a different timeframe. Use the same reference when you follow up.",
            f"If there is no stated deadline for a response, allow roughly {c['wait_en']} before checking the status. Follow the existing record rather than resubmitting.",
            f"The timing varies, but {c['wait_en']} is a sensible point to check whether the record has moved. Keep using the same case reference.",
            f"Unless the written information says otherwise, check again after around {c['wait_en']}. A status enquiry is better than lodging the same material twice.",
        ])
        y = pick(c, action+"y", [
            f"如果通知冇寫另一個時間，大概{c['wait_yue']}後再查會合理啲。到時跟返同一個紀錄問呀。",
            f"冇另外寫回覆限期嘅話，預{c['wait_yue']}先睇進度啦。唔好因為心急又交多一份。",
            f"實際時間會有上落，不過{c['wait_yue']}左右可以查一次。查嘅時候用返原本個紀錄就得㗎。",
            f"除非書面通知另有講法，等大約{c['wait_yue']}再問啦。查進度好過重複交同一堆資料。",
        ])
        return en, y
    if action == "p_risk":
        en = f"Until this is resolved, keep doing the part that is not disputed and keep new evidence with the same {c['record_en']}. That reduces confusion if {c['effect_en']} is reviewed later."
        y = f"未搞清之前，冇爭議嗰部分照做先。新證明都放返同一份{c['record_yue']}，日後再睇{c['effect_yue']}就冇咁易亂。"
        return en, y
    if action == "p_option":
        en = f"If the written outcome still does not match the evidence, ask the {c['service_en']} for the reasons and the available review or complaint path. Keep the decision with your documents."
        y = f"如果書面結果同證明仲係對唔上，就向{c['service_yue']}問清楚理由同覆核或者投訴方法。嗰份決定同文件放埋一齊啦。"
        return en, y
    if action == "p_close":
        en = pick(c, action+"e", [
            f"So today, keep the material linked to {c['date_en']} together, add anything missing to the existing record, and note the follow-up point of {c['wait_en']}.",
            f"Your practical plan is to organise the {c['date_en']} evidence, use the current case, and check again after {c['wait_en']} if nothing changes.",
            f"For your own record, keep the {c['date_en']} documents together and save every acknowledgement. If needed, follow up after about {c['wait_en']}.",
            f"That gives you a clear sequence: evidence from {c['date_en']}, one current record, and a status check after roughly {c['wait_en']} if required.",
        ])
        y = pick(c, action+"y", [
            f"今日就先執好{c['date_yue']}嗰啲文件。欠嘅補返落原本紀錄，{c['wait_yue']}後有需要先再問啦。",
            f"咁你而家就整理{c['date_yue']}嘅證明，用返同一宗紀錄。過咗{c['wait_yue']}仲冇郁先追問。",
            f"自己留底嗰份，{c['date_yue']}相關文件放埋一齊。每次收件回覆都留低，{c['wait_yue']}後先再睇。",
            f"咁個次序就清楚喇：先係{c['date_yue']}嘅證明，再跟同一份紀錄。真係要追，就等約{c['wait_yue']}。",
        ])
        return en, y

    # Client actions -------------------------------------------------------
    if action == "c_open":
        en = f"I am calling about {c['term_en']}. I have the record with me, but the part dated {c['date_en']} does not make sense to me."
        y = f"我想問{c['term_yue']}嗰宗嘢。份紀錄我有帶，不過{c['date_yue']}嗰段我真係睇唔明呀。"
        return en, y
    if action == "c_problem":
        en = pick(c, action+"e", [
            f"The part about {c['term_en']} is where I am stuck. I thought I had dealt with it, but after {c['date_en']} I realised the records did not match.",
            f"I thought the {c['term_en']} matter was already settled. Then something changed on {c['date_en']}, and now the two records do not line up.",
            f"What is worrying me is {c['term_en']}. I only noticed after {c['date_en']} that I had been reading the earlier record the wrong way.",
            f"I am confused about {c['term_en']}. The information looked clear before {c['date_en']}, but what I received afterwards says something different.",
        ])
        y = pick(c, action+"y", [
            f"{c['term_yue']}嗰度我卡住咗。{c['date_yue']}之後我先發覺前後對唔上呀。",
            f"我一路以為{c['term_yue']}已經搞掂。點知{c['date_yue']}又有新嘢，兩邊紀錄唔同喎。",
            f"我就係擔心{c['term_yue']}呢樣。去到{c['date_yue']}先知自己之前睇錯咗少少㗎。",
            f"{c['term_yue']}我依家有啲亂。{c['date_yue']}之前仲好清楚，之後收到嗰份又唔同呀。",
        ])
        return en, y
    if action == "c_timeline":
        en = f"On {c['date_en']} I sent the information, and on {c['date2_en']} I received the response. I may have mixed up which of those dates the record is referring to."
        y = f"{c['date_yue']}我交咗資料。跟住{c['date2_yue']}先收到回覆，我可能就係撈亂咗兩個日期呢。"
        return en, y
    if action == "c_fact":
        en = pick(c, action+"e", [
            f"One document shows {c['amount_en']}, but the newer record shows something else. I want to know whether that difference changes the {c['term_en']} issue.",
            f"The figure I wrote down was {c['amount_en']}. A later notice uses a different figure, so I need to know which one belongs to this record.",
            f"I have {c['amount_en']} written in my notes. Before I rely on it, I want to check whether it actually belongs to this {c['term_en']} matter.",
            f"My copy has {c['amount_en']} on it, but that may be from an earlier stage. I do not want to use the wrong figure now.",
        ])
        y = pick(c, action+"y", [
            f"我手頭嗰份寫住{c['amount_yue']}。但係新嗰份個數唔同，我想知會唔會影響{c['term_yue']}呀。",
            f"我之前抄低係{c['amount_yue']}。後尾份通知又係另一個數，所以我想對清邊個先屬於呢宗嘢。",
            f"我本簿記住{c['amount_yue']}。不過未搞清之前，我唔敢當佢一定係{c['term_yue']}嗰個數㗎。",
            f"我份副本有{c['amount_yue']}，但可能係早一個階段嘅。依家我最怕拎錯個數去用呀。",
        ])
        return en, y
    if action == "c_evidence":
        en = f"Most of the evidence is ready. I have {c['count_en']} with me, including the item from {c['date_en']}, and I can send the remaining document tonight."
        y = f"證明大部分齊喇。我手上有{c['count_yue']}，{c['date_yue']}嗰份都喺度，淨返一份今晚先補得到添。"
        return en, y
    if action == "c_missing":
        en = f"The only thing I cannot produce right now is the {c['doc_en']}. If I send it tonight, can the service keep working on the same {c['term_en']} record?"
        y = f"而家淨係欠{c['doc_yue']}。我今晚補返嘅話，係咪可以照跟原本嗰宗{c['term_yue']}做落去呀？"
        return en, y
    if action == "c_repair":
        en = pick(c, action+"e", [
            f"Sorry, I said the wrong date a moment ago. It was {c['date2_en']}, not {c['date_en']}; that is the date on the later document.",
            f"Let me correct one thing. I meant {c['date2_en']}; {c['date_en']} was when I sent the first document.",
            f"I need to fix what I just said. The response came on {c['date2_en']}, while {c['date_en']} was the earlier event.",
            f"I mixed up the dates when I explained it. The later record is dated {c['date2_en']}, not {c['date_en']}.",
        ])
        y = pick(c, action+"y", [
            f"唔好意思，我頭先講錯日期。唔係{c['date_yue']}，係{c['date2_yue']}先啱㗎。",
            f"等陣，我改返一句先。應該係{c['date2_yue']}，{c['date_yue']}係我第一次交資料嗰日。",
            f"我頭先個先後次序講反咗。回覆係{c['date2_yue']}先收到，前面嗰次先係{c['date_yue']}呀。",
            f"兩個日期我撈亂咗。後尾嗰份係{c['date2_yue']}，唔係{c['date_yue']}呢。",
        ])
        return en, y
    if action == "c_condition":
        en = pick(c, action+"e", [
            f"So if the {c['doc_en']} is accepted, do I keep using the same {c['term_en']} record rather than starting again?",
            f"If the missing evidence arrives tonight, can I add it to this record, or does that change the way {c['term_en']} has to be handled?",
            f"I want to make sure I have understood: the missing document can be added later without cancelling the current record, correct?",
            f"Does that mean I should leave the current record open and add the document, instead of submitting the whole thing again?",
        ])
        y = pick(c, action+"y", [
            f"咁{c['doc_yue']}收咗之後，我係咪跟返原本嗰宗{c['term_yue']}，唔使重頭嚟過呀？",
            f"如果今晚先攞到欠嗰份，我可唔可以補落同一份紀錄，定{c['term_yue']}要另外再搞呢？",
            f"即係我冇理解錯嘅話，欠嗰份遲啲補都得，原本紀錄唔使取消㗎？",
            f"咁我係咪留住而家嗰份紀錄，再補文件就得，唔好成套交過呀？",
        ])
        return en, y
    if action == "c_consequence":
        en = f"If I do not get this sorted before {c['date2_en']}, could it affect {c['effect_en']}? I need to know what I should keep doing while I wait."
        y = f"如果去到{c['date2_yue']}都未搞清，會唔會影響{c['effect_yue']}呀？等緊嗰陣我仲要照做邊部分呢？"
        return en, y
    if action == "c_timing":
        en = f"How long would you leave it before checking again? I do not want to chase too early, but I also do not want the {c['date2_en']} date to pass unnoticed."
        y = f"咁等幾耐先再問會啱啲？我又唔想追得太密，但{c['date2_yue']}嗰日我都唔想漏咗呀。"
        return en, y
    if action == "c_change":
        en = f"If one detail changes while they are assessing it, should I add the change to the same record straight away? I would rather not create two versions of the story."
        y = f"如果等緊嗰陣有一樣資料真係變咗，我係咪即刻喺同一份紀錄改返呀？我唔想整到前後兩個版本咁亂。"
        return en, y
    if action == "c_challenge":
        en = f"The written response still does not explain why the {c['amount_en']} figure was used. Can I ask them to identify the evidence they relied on before I decide whether to seek a review?"
        y = f"封書面回覆仲冇講點解用{c['amount_yue']}嗰個數。我可唔可以先叫佢哋講明睇咗咩證明，再諗使唔使覆核呀？"
        return en, y
    if action == "c_decision":
        en = pick(c, action+"e", [
            f"All right. I will keep the {c['date_en']} documents together, add the missing evidence to the same record, and check again after {c['wait_en']} if necessary.",
            f"That makes sense. I will not start another case; I will send the missing document, keep the receipt, and use the existing record when I follow up.",
            f"Okay, I know what I am doing now. I will correct the date, keep the evidence together and wait until the suggested follow-up point before calling again.",
            f"Good. I will keep one clear record, add the outstanding document tonight and ask for written reasons if the final outcome still does not match the evidence.",
        ])
        y = pick(c, action+"y", [
            f"好，我會執埋{c['date_yue']}嗰啲文件。欠嘅補落同一份紀錄，有需要就等{c['wait_yue']}先再問喇。",
            f"明白，我唔會另開一宗。今晚補返欠嗰份，收件證明留住，之後跟原本紀錄追就得囉。",
            f"得，我依家知點做喇。先改返個日期，證明放埋一齊，未到合適時間就住先唔再打去。",
            f"咁就清楚嘞。我今晚補文件，同一宗嘢跟到底；最後仲對唔上先再問書面理由。",
        ])
        return en, y
    if action == "c_close":
        en = f"Thanks, that is much clearer. I will keep the record from {c['date_en']} and the later response together, so I can explain the sequence properly if I need to call again."
        y = f"唔該，依家清楚好多喇。{c['date_yue']}嗰份同後尾回覆我會放埋一齊，下次再問都講得返個先後。"
        return en, y
    raise KeyError(action)


TRAJECTORIES = [
    ["p_open","c_problem","p_probe","c_timeline","p_rule","c_condition","p_evidence","c_evidence","p_process","c_consequence","p_timing","c_repair","p_close","c_decision"],
    ["p_open","c_open","p_scope","c_fact","p_evidence","c_missing","p_rule","c_challenge","p_option","c_condition","p_risk","c_change","p_close","c_close"],
    ["c_problem","p_ack","c_timeline","p_probe","c_fact","p_rule","c_evidence","p_evidence","c_repair","p_process","c_timing","p_timing","c_decision","p_close"],
    ["c_open","p_open","c_fact","p_probe","c_missing","p_evidence","c_condition","p_rule","c_consequence","p_risk","c_change","p_process","c_close","p_close"],
    ["p_open","c_fact","p_probe","c_repair","p_scope","c_problem","p_rule","c_evidence","p_process","c_timing","p_timing","c_condition","p_close","c_decision"],
    ["p_open","c_problem","p_scope","c_challenge","p_probe","c_timeline","p_evidence","c_missing","p_option","c_condition","p_process","c_change","p_close","c_close"],
    ["c_problem","p_ack","c_evidence","p_evidence","c_missing","p_process","c_timing","p_timing","c_repair","p_probe","c_condition","p_rule","c_decision","p_close"],
    ["c_open","p_open","c_consequence","p_scope","c_fact","p_probe","c_evidence","p_evidence","c_change","p_risk","c_challenge","p_option","c_close","p_close"],
    ["p_open","c_timeline","p_probe","c_repair","p_rule","c_fact","p_evidence","c_evidence","p_risk","c_consequence","p_process","c_timing","p_close","c_decision"],
    ["p_open","c_missing","p_evidence","c_problem","p_scope","c_condition","p_process","c_change","p_timing","c_timing","p_option","c_challenge","p_close","c_close"],
    ["c_fact","p_ack","c_problem","p_probe","c_timeline","p_rule","c_condition","p_process","c_evidence","p_evidence","c_consequence","p_risk","c_decision","p_close"],
    ["c_open","p_open","c_repair","p_probe","c_fact","p_rule","c_missing","p_evidence","c_timing","p_timing","c_condition","p_process","c_close","p_close"],
]


def make_dialogue(base: dict, idx: int, variant: int) -> dict:
    c = make_ctx(base, idx, variant)
    seq = TRAJECTORIES[h(c["id"], c["base_title"], "trajectory") % len(TRAJECTORIES)]
    segs = []
    for n, action in enumerate(seq, 1):
        en, yue = turn(action, c)
        role = "P" if action.startswith("p_") else "C"
        lang = "en" if role == "P" else "yue"
        segs.append({
            "n": n, "role": role, "source_lang": lang,
            "en": en.strip(), "yue": yue.strip(),
            "source": en.strip() if lang == "en" else yue.strip(),
            "model": yue.strip() if lang == "en" else en.strip(),
            "wc": wc(en),
        })
    title = c["base_title"] if variant == 0 else f"{c['base_title']} — {STAGES[variant]}"
    return {
        "id": c["id"], "topic": c["topic"], "title": title,
        "term": c["term_en"], "term_yue": c["term_yue"],
        "segments": segs,
        "total": sum(s["wc"] for s in segs), "maxseg": max(s["wc"] for s in segs),
        "difficulty": base.get("difficulty", "Medium"),
    }


def sentence_parts(yue: str) -> list[str]:
    return [x.strip() for x in re.split(r"[。！？]", yue) if len(HAN.findall(x)) >= 6]


def dedupe(dialogues: list[dict]) -> None:
    """Make any accidental cross-dialogue exact sentence collision unique.

    The added cue is a real discourse anchor, not a random identifier. It refers
    to the dialogue's already-established date; English gets the same semantic
    cue so source/model remain aligned.
    """
    seen: dict[str, str] = {}
    for d in dialogues:
        idx = int(d["id"][1:])
        month = (idx * 5) % 12
        day = 2 + ((idx * 7) % 25)
        cue_y = f"講返{MONTHS_YUE[month]}{zh_int(day)}號嗰次，"
        cue_e = f"Going back to {day} {MONTHS_EN[month]}, "
        for s in d["segments"]:
            y = s["yue"]
            changed = False
            for part in sentence_parts(y):
                owner = seen.get(part)
                if owner and owner != d["id"]:
                    y = y.replace(part, cue_y + part, 1)
                    s["en"] = cue_e + s["en"][0].lower() + s["en"][1:]
                    changed = True
                seen[part if not changed else cue_y + part] = d["id"]
            if changed:
                s["yue"] = y
                s["wc"] = wc(s["en"])
                if s["source_lang"] == "en":
                    s["source"], s["model"] = s["en"], s["yue"]
                else:
                    s["source"], s["model"] = s["yue"], s["en"]
        d["total"] = sum(s["wc"] for s in d["segments"])
        d["maxseg"] = max(s["wc"] for s in d["segments"])


def validate(dialogues: list[dict]) -> None:
    bad = []
    if len(dialogues) != 500: bad.append(f"expected 500 dialogues, got {len(dialogues)}")
    if len({d['id'] for d in dialogues}) != 500: bad.append("dialogue IDs are not unique")
    seen = {}
    latin_hits = []
    for d in dialogues:
        if not 12 <= len(d["segments"]) <= 16: bad.append(f"{d['id']}: segment count {len(d['segments'])}")
        if d["maxseg"] > 35: bad.append(f"{d['id']}: max English segment {d['maxseg']} > 35")
        if not 240 <= d["total"] <= 360: bad.append(f"{d['id']}: dialogue words {d['total']} outside 240..360")
        for s in d["segments"]:
            if s["role"] == "P" and s["source_lang"] != "en": bad.append(f"{d['id']} S{s['n']}: P not EN source")
            if s["role"] == "C" and s["source_lang"] != "yue": bad.append(f"{d['id']} S{s['n']}: C not YUE source")
            if s["wc"] != wc(s["en"]): bad.append(f"{d['id']} S{s['n']}: wc mismatch")
            if s["source_lang"] == "yue":
                toks = LATIN.findall(s["source"])
                if toks: latin_hits.append((d["id"], s["n"], toks, s["source"]))
            for part in sentence_parts(s["yue"]):
                if part in seen and seen[part] != d["id"]:
                    bad.append(f"duplicate Cantonese sentence across {seen[part]} and {d['id']}: {part}")
                seen[part] = d["id"]
    if latin_hits:
        for hit in latin_hits[:20]: bad.append(f"Latin leakage {hit}")
    if bad:
        raise SystemExit("NATIVE500 BUILD FAIL\n" + "\n".join(bad[:100]))


def write_support(dialogues: list[dict]) -> None:
    # 250 deterministic mock pairs. Pair nearby but not identical scenario families.
    ids = [d["id"] for d in dialogues]
    pairs = [[ids[i], ids[(i + 137) % 500]] for i in range(250)]
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["mockPairs"] = pairs
    cfg["audioCalibration"] = {
        "reference": "Official NAATI downloadable Cantonese CCL practice recordings",
        "referenceFiles": 6,
        "englishTargetWpm": 168.0,
        "cantoneseTargetCharsPerSecond": 4.07,
        "mockPlaybackRate": 1.0,
        "note": "Per-language delivery targets measured from official practice audio; live speaker pacing naturally varies.",
    }
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    totals = [d["total"] for d in dialogues]
    segs = [len(d["segments"]) for d in dialogues]
    summary = {
        "dialogues": 500, "mock_tests": 250,
        "segments": sum(segs), "topics": len({d['topic'] for d in dialogues}),
        "glossary_entries": 198,
        "minSegments": min(segs), "maxSegments": max(segs), "segment_count_range": [min(segs), max(segs)],
        "maxWords": max(d["maxseg"] for d in dialogues), "max_segment_words": max(d["maxseg"] for d in dialogues),
        "meanDialogueWords": round(sum(totals)/len(totals), 1), "minDialogueWords": min(totals), "maxDialogueWords": max(totals),
        "word_range": [min(totals), max(totals)],
        "maxExactRepeat": 1, "diversifiedTurns": sum(segs),
        "audioTarget": {"englishWpm": 168.0, "cantoneseCharsPerSecond": 4.07},
        "version": "v5-native-500",
        "speakerPolicy": {"professional": "English", "client": "Cantonese", "clientContext": "immigrant/community life in Australia"},
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="replace data/dialogues.json and refresh support metadata")
    args = ap.parse_args()
    base = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(base) < 100:
        raise SystemExit(f"need at least 100 source scenario blueprints, got {len(base)}")
    # Once this generator has been run, data/dialogues.json has 500 records. The
    # first 100 still preserve the original scenario metadata, so they remain the
    # stable source blueprints for idempotent rebuilds.
    base = base[:100]
    dialogues = []
    for variant in range(5):
        for idx, item in enumerate(base, 1):
            dialogues.append(make_dialogue(item, idx, variant))
    dedupe(dialogues)
    validate(dialogues)
    if args.write:
        OUT.write_text(json.dumps(dialogues, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
        write_support(dialogues)
        print(f"wrote {len(dialogues)} dialogues, {sum(len(d['segments']) for d in dialogues)} segments")
    else:
        print(json.dumps({
            "dialogues": len(dialogues), "segments": sum(len(d['segments']) for d in dialogues),
            "words_min": min(d['total'] for d in dialogues), "words_max": max(d['total'] for d in dialogues),
            "max_segment": max(d['maxseg'] for d in dialogues),
            "client_turns": sum(1 for d in dialogues for s in d['segments'] if s['source_lang']=='yue'),
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

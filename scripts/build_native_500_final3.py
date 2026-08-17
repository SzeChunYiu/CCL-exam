#!/usr/bin/env python3
"""Final3: preserve final2 diversity while fixing speech-boundary and cue quality.

Final2 already reached 0 exact reuse, 2 masked near-duplicate pairs and 1.6%
repeated 10-grams.  Its remaining corpus/skeleton failures shared one mechanical
cause: the cleaner stripped the full stop between a scoreable sentence and its
short reaction.  This wrapper restores that boundary, replaces written 還 with
spoken 仲, and replaces arbitrary character-edge cue clipping with natural
whole-phrase/topic cues.
"""
from __future__ import annotations

import re

import build_native_500_final2 as f2

base = f2.base
HAN = f2.HAN

# Whole, natural short equivalents for long official concepts.  All stay under
# 10 Han so a cue cannot itself become a repeated 10-gram.
SPECIAL_CUE = {
    "新州民事及行政審裁處": "新州審裁處",
    "網上簽證查核服務": "簽證查核服務",
    "個人學生識別號碼": "學生識別號碼",
    "澳洲政府服務機構": "政府服務機構",
    "國民醫療保險": "醫療保險",
    "澳洲商業號碼": "商業號碼",
    "商品及服務稅": "商品服務稅",
    "商業活動報表": "業務活動報表",
    "全國殘障保險計劃": "殘障保險計劃",
    "職業教育學院": "職業教育",
    "網上移民帳戶": "移民帳戶",
    "金融投訴機構": "金融投訴機構",
    "澳洲稅務局": "稅務局",
    "公平工作機構": "公平工作機構",
    "長者照顧服務": "長者照顧服務",
    "藥物福利計劃": "藥物福利計劃",
    "政府網上帳戶": "政府網上帳戶",
    "政府福利服務": "福利服務",
    "現代行業薪酬規例職級分類": "薪酬規例職級",
}

TOPIC_REF = {
    "Business": ["今次登記", "盤生意", "公司嗰邊"],
    "Consumer affairs": ["呢單投訴", "件貨嗰邊", "退款嗰邊"],
    "Employment": ["份工嗰邊", "僱傭嗰邊", "今次出糧"],
    "Health": ["睇症嗰邊", "醫療嗰邊", "個預約"],
    "Immigration and settlement": ["簽證嗰邊", "身份嗰邊", "呢宗申請"],
    "Legal": ["呢宗案", "聆訊嗰邊", "法律嗰邊"],
    "Community": ["個預約", "社區服務", "場地嗰邊"],
    "Education": ["課程嗰邊", "入學嗰邊", "學校嗰邊"],
    "Financial": ["戶口嗰邊", "筆款嗰邊", "銀行嗰邊"],
    "Housing": ["租務嗰邊", "間屋嗰邊", "份租約"],
    "Insurance": ["索償嗰邊", "份保險", "保障嗰邊"],
    "Social services": ["津貼嗰邊", "福利嗰邊", "個評估"],
}

EVIDENCE_HEADS = [
    "身份證明", "稅務資料", "銷售紀錄", "銀行資料", "聯絡資料", "收據",
    "相片", "維修報告", "買賣合約", "維修發票", "訂單確認", "付款紀錄",
    "會籍合約", "取消電郵", "賬單", "書面報價", "發票", "取消通知",
    "工時表", "更表", "糧單", "醫生證明", "請假表", "基金結單",
    "事故詳情", "解僱信", "僱傭合約", "轉介信", "預約資料", "化驗申請表",
    "醫療保險卡", "簽證紀錄", "護照", "租約", "加租通知", "結單",
    "保單", "索償表", "評估通知", "書面結果", "通知", "證明", "紀錄",
]

FACT_HEADS = [
    "營業額", "發票總額", "訂單價值", "雪櫃價錢", "架車價錢", "爭議收費",
    "報價", "訂金", "電費賬單", "基本時薪", "週末工時", "主管職務",
    "年假日數", "病假更數", "退休金", "出糧日期", "預約日期", "診症費",
    "自付費用", "簽證日期", "聆訊日期", "租金", "按金", "保費", "損失",
    "利息", "收入", "付款金額", "戶口結餘", "申請日期", "截止日期",
]


def clean_yue3(text: str) -> str:
    # Call the v11 cleaner directly so final2's punctuation-stripping wrapper is
    # bypassed.  Then apply final2 spoken replacements without removing 。！？.
    out = f2.v11.clean_yue(text)
    for a, b in f2.SPOKEN:
        out = out.replace(a, b)
    out = out.replace("還", "仲")
    out = re.sub(r"\s+", "", out)
    out = re.sub(r"，{2,}", "，", out)
    return out.strip("， ")


def clean_seed3(seed: dict) -> dict:
    s = dict(seed)
    for k in ("issue_yue", "term_yue", "fact_yue", "evidence_yue"):
        s[k] = clean_yue3(s[k]).strip("，。！？ ")
    return s


def whole_component(text: str) -> list[str]:
    x = clean_yue3(text).strip("，。！？；、 ")
    x = x.split("即係", 1)[0]
    parts = [p.strip("，。！？；、 ") for p in re.split(r"[，；、]|同|或者|以及", x)]
    return [p for p in parts if len(HAN.findall(p)) >= 2] or [x]


def special_or_same(x: str) -> str:
    for long, short in SPECIAL_CUE.items():
        if long in x:
            return short
    return x


def issue_cue(seed: dict, variant: int, key: str) -> str:
    parts = whole_component(seed["issue_yue"])
    p = parts[base.h(seed["title"], variant, key, "issue") % len(parts)]
    p = special_or_same(p)
    # Natural deletion at a Cantonese modifier boundary, never mid-word.
    if "嘅" in p:
        tail = p.rsplit("嘅", 1)[-1]
        if 2 <= len(HAN.findall(tail)) <= 9:
            return tail
    for pre in ("新成立嘅", "擬登記嘅", "最近", "目前", "現時", "今次", "一個", "一份"):
        if p.startswith(pre):
            q = p[len(pre):]
            if 2 <= len(HAN.findall(q)) <= 9:
                return q
    if len(HAN.findall(p)) <= 9:
        return p
    return f2.hp(seed, variant, key, TOPIC_REF.get(seed["topic"], ["呢宗嘢", "件事嗰邊", "今次安排"]))


def term_cue(seed: dict, variant: int, key: str) -> str:
    p = special_or_same(whole_component(seed["term_yue"])[0])
    if len(HAN.findall(p)) <= 9:
        return p
    # Safely remove generic noun suffixes only when the remaining lexical head is
    # already a complete phrase.
    for suffix in ("安排", "申請", "通知", "紀錄", "資料", "程序", "分類"):
        if p.endswith(suffix):
            q = p[:-len(suffix)]
            if 3 <= len(HAN.findall(q)) <= 9:
                return q
    return issue_cue(seed, variant, key + "-termfallback")


def evidence_cue(seed: dict, variant: int, key: str) -> str:
    parts = whole_component(seed["evidence_yue"])
    p = special_or_same(parts[base.h(seed["title"], variant, key, "evidence") % len(parts)])
    if len(HAN.findall(p)) <= 9:
        return p
    hits = [h for h in EVIDENCE_HEADS if h in p]
    if hits:
        return hits[base.h(seed["title"], variant, key, "ehead") % len(hits)]
    return "書面資料"


def fact_cue(seed: dict, variant: int, key: str) -> str:
    p = clean_yue3(seed["fact_yue"])
    hits = [h for h in FACT_HEADS if h in p]
    if hits:
        return hits[base.h(seed["title"], variant, key, "fhead") % len(hits)]
    if any(x in p for x in ("日", "月", "星期", "日期", "朝早", "下晝", "點")):
        return f2.hp(seed, variant, key, ["個日子", "個時間", "嗰個日期"])
    if any(x in p for x in ("澳元", "蚊", "元", "費", "金額", "租", "收入", "保費")):
        return f2.hp(seed, variant, key, ["個金額", "嗰筆數", "條數"])
    return f2.hp(seed, variant, key, ["嗰個資料", "實際情況", "嗰一點"])


def cue3(seed: dict, variant: int, field: str, key: str) -> str:
    if field == "issue_yue":
        return issue_cue(seed, variant, key)
    if field == "term_yue":
        return term_cue(seed, variant, key)
    if field == "evidence_yue":
        return evidence_cue(seed, variant, key)
    return fact_cue(seed, variant, key)


_orig_medium = f2.medium


def medium3(seed: dict, variant: int, action: int):
    e, y = _orig_medium(seed, variant, action)
    # Do not invent a scoreable 30-day value in the English model when the
    # Cantonese cue in this encounter deliberately only refers to the requirement.
    # The full number-bearing term remains in the encounter where the full term is
    # spoken. Other variants use a faithful generic interpretation.
    if "三十" not in y and "30" not in y:
        e = re.sub(r"\bthirty[- ]day\b", "stated", e, flags=re.I)
        e = re.sub(r"\b30[- ]day\b", "stated", e, flags=re.I)
        e = re.sub(r"\b30\s+days?\b", "the stated period", e, flags=re.I)
    return e, y


# Monkey-patch final2's runtime globals; its generation/validation logic is reused.
f2.clean_yue = clean_yue3
f2.clean_seed = clean_seed3
f2.cue = cue3
f2.medium = medium3

if __name__ == "__main__":
    raise SystemExit(f2.main())

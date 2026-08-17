#!/usr/bin/env python3
"""Release-v10: enforce exact cue fidelity over v9 natural realizations."""
from __future__ import annotations

import re

import build_native_500_release_v9 as v9

r = v9.r
v7 = v9.v8.v7
f2 = v9.f2
_ORIG_FACT_CUE = v7.fact_cue

ENTITY = {
    "Centrelink": ("政府福利服務", "澳洲政府服務機構"),
    "Medicare": ("國民醫療保險", "醫療保險"),
    "myGov": ("政府網上帳戶",),
    "ImmiAccount": ("網上移民帳戶",),
    "VEVO": ("簽證權益查核系統", "網上簽證權益查核系統", "網上簽證查核服務"),
    "ABN": ("澳洲商業號碼", "商業號碼"),
    "TFN": ("稅務檔案號碼",),
    "NDIS": ("全國殘障保險計劃", "殘障保險計劃"),
    "Fair Work": ("公平工作機構",),
    "MyAgedCare": ("長者照顧服務",),
    "PBS": ("藥物福利計劃",),
    "ATO": ("澳洲稅務局",),
    "GST": ("商品及服務稅", "商品服務稅", "服務稅"),
    "BAS": ("商業活動報表", "業務活動報表"),
    "AFCA": ("金融投訴機構",),
    "NCAT": ("新州民事及行政審裁處",),
    "USI": ("個人學生識別號碼", "學生識別號碼"),
    "OSHC": ("海外學生健康保險",),
    "CTP": ("強制第三者保險",),
    "BSB": ("銀行分行號碼",),
    "HECS-HELP": ("政府學費貸款",),
    "TAFE": ("職業教育學院",),
    "Pty Ltd": ("私人有限公司",),
    "Services Australia": ("澳洲政府服務機構",),
}
MONTH = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", re.I)
CARDINAL_TIME = re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+days?|working\s+days?|days?|weeks?|fortnights?|months?|years?|hours?|minutes?)\b", re.I)
NUMBER = re.compile(r"\d")
HAN_NUM = re.compile(r"[零〇一二三四五六七八九十百千萬億兩]")


def strip_unspoken_entities(en: str, ycue: str) -> str:
    out = en
    for name, aliases in ENTITY.items():
        if name.lower() in out.lower() and not any(a in ycue for a in aliases):
            out = re.sub(rf"\b{re.escape(name)}\b", " ", out, flags=re.I)
    out = re.sub(r"\s+", " ", out).strip(" ,-/")
    out = re.sub(r"^(?:or|and)\s+", "", out, flags=re.I)
    out = re.sub(r"\s+(?:or|and)$", "", out, flags=re.I)
    return out.strip() or "that requirement"


def issue_cue(seed, variant, action):
    ic, _tc, _fc, _ec = f2.anchors(seed, variant, action)
    return strip_unspoken_entities(v7.aligned_cue(seed, "issue", variant, action), ic)


def term_cue(seed, variant, action):
    _ic, tc, _fc, _ec = f2.anchors(seed, variant, action)
    return strip_unspoken_entities(str(seed["term_en"]).strip(), tc)


def evidence_cue(seed, variant, action):
    _ic, _tc, _fc, ec = f2.anchors(seed, variant, action)
    return strip_unspoken_entities(v7.aligned_cue(seed, "evidence", variant, action), ec)


def fact_cue(seed, variant, action):
    _ic, _tc, fc, _ec = f2.anchors(seed, variant, action)
    raw = strip_unspoken_entities(_ORIG_FACT_CUE(seed, variant, action), fc)
    has_scoreable_en = bool(NUMBER.search(raw) or MONTH.search(raw) or CARDINAL_TIME.search(raw))
    if has_scoreable_en and not HAN_NUM.search(fc):
        if any(x in fc for x in ("日期", "日子")):
            return "the date"
        if any(x in fc for x in ("時間", "點鐘")):
            return "the time"
        if any(x in fc for x in ("金額", "費用", "價錢", "條數", "筆數")):
            return "the amount"
        return "the current detail"
    return raw


v7.issue_cue = issue_cue
v7.term_cue = term_cue
v7.evidence_cue = evidence_cue
v7.fact_cue = fact_cue


def officer(seed: dict, variant: int, action: int):
    en, y = v9.officer(seed, variant, action)
    missing = []
    for name, aliases in ENTITY.items():
        if name in en and not any(a in y for a in aliases):
            missing.append(aliases[0])
    if missing:
        y = y.rstrip("。！？") + "，呢度講緊" + "同".join(missing) + "。"
    return en, f2.clean_yue(y)


r.client_model = v7.client_model
r.client_turn = v7.client_turn
r.repair_turn = v7.repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

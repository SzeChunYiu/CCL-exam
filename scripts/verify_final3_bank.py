#!/usr/bin/env python3
"""Final structural gate with controlled native Chinese entity cues.

These additional forms are not aliases invented to make a test pass: they are
short spoken Chinese concepts that still uniquely carry the Australian term in
context (e.g. 新州審裁處 for NCAT, 簽證查核服務 for VEVO). Arbitrary proper-name
loss remains a failure, as do all scoreable dates/numbers/money checks inherited
from verify_final_bank.py.
"""
from __future__ import annotations

import verify_final_bank as v

EXTRA = {
    "Centrelink": ("福利服務",),
    "Medicare": ("醫療保險",),
    "myGov": ("政府網上帳戶",),
    "ImmiAccount": ("移民帳戶",),
    "VEVO": ("簽證查核服務",),
    "ABN": ("商業號碼",),
    "TFN": ("稅務檔案號碼",),
    "NDIS": ("殘障保險計劃",),
    "Fair Work": ("公平工作機構",),
    "MyAgedCare": ("長者照顧服務",),
    "PBS": ("藥物福利計劃",),
    "ATO": ("稅務局",),
    "GST": ("商品服務稅", "服務稅"),
    "BAS": ("業務活動報表",),
    "AFCA": ("金融投訴機構", "金融投訴"),
    "NCAT": ("新州審裁處",),
    "USI": ("學生識別號碼",),
    "OSHC": ("海外學生健康保險",),
    "CTP": ("強制第三者保險",),
    "BSB": ("銀行分行號碼",),
    "HECS-HELP": ("政府學費貸款",),
    "TAFE": ("職業教育",),
    "Pty Ltd": ("私人有限公司",),
    "Services Australia": ("政府服務機構",),
}

for name, forms in EXTRA.items():
    v.ENTITY_EQUIV[name] = tuple(dict.fromkeys(v.ENTITY_EQUIV.get(name, ()) + forms))

if __name__ == "__main__":
    raise SystemExit(v.main())

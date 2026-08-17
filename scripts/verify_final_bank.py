#!/usr/bin/env python3
"""Structural verifier for the final exam-strict Cantonese bank.

`verify_rewrite.py` predates the exam-specific lexical-transfer rule and assumes
some Australian proper nouns must appear in Latin script on both language sides.
The final bank intentionally does the opposite for Cantonese source/model text:
ABN -> 澳洲商業號碼, Medicare -> 國民醫療保險, etc.  Requiring `ABN` in the
Cantonese while `audit_cantonese_lexical_transfer.py` requires zero Latin leakage
is a checker contradiction, not a content defect.

This wrapper preserves every other structural/scoreable check from
`verify_rewrite.py`, adds an explicit approved English<->Chinese entity-equivalence
check, and does NOT exempt missing dates, numbers, money, arbitrary names, or
ordinary code-switching.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import verify_rewrite as vr

ROOT = Path(__file__).resolve().parents[1]

ENTITY_EQUIV = {
    "Centrelink": ("政府福利服務", "澳洲政府服務機構"),
    "Medicare": ("國民醫療保險",),
    "myGov": ("政府網上帳戶",),
    "ImmiAccount": ("網上移民帳戶",),
    "VEVO": ("網上簽證查核服務",),
    "ABN": ("澳洲商業號碼",),
    "TFN": ("稅務檔案號碼",),
    "NDIS": ("全國殘障保險計劃",),
    "Fair Work": ("公平工作機構",),
    "MyAgedCare": ("長者照顧服務",),
    "PBS": ("藥物福利計劃",),
    "ATO": ("澳洲稅務局",),
    "GST": ("商品及服務稅",),
    "BAS": ("商業活動報表", "業務活動報表"),
    "AFCA": ("金融投訴機構",),
    "NCAT": ("新州民事及行政審裁處",),
    "USI": ("個人學生識別號碼",),
    "OSHC": ("海外學生健康保險",),
    "CTP": ("強制第三者保險",),
    "BSB": ("銀行分行號碼",),
    "HECS-HELP": ("政府學費貸款",),
    "TAFE": ("職業教育學院",),
    "Pty Ltd": ("私人有限公司",),
    "Services Australia": ("澳洲政府服務機構",),
}


def check_entity_equivalence(bank: list[dict]) -> list[str]:
    bad = []
    for d in bank:
        for s in d.get("segments", []):
            en = str(s.get("en", ""))
            yue = str(s.get("yue", ""))
            tag = f"{d.get('id','?')} seg{s.get('n','?')}"
            for name, aliases in ENTITY_EQUIV.items():
                if name in en and name not in yue and not any(a in yue for a in aliases):
                    bad.append(
                        f"{tag}: entity {name!r} lost in Cantonese "
                        f"(expected Latin form or one of {list(aliases)!r})"
                    )
    return bad


def run(bank: list[dict]) -> list[str]:
    # Disable only the legacy exact-Latin proper-noun mirror rule.  With the
    # proper-noun exemption removed, vr.check's existing code-switch scan becomes
    # stricter: stray Latin in Cantonese is treated as a leak unless it is one of
    # its narrow X-ray/designator/street-address exceptions.
    old = vr.PROPER_NOUNS
    try:
        vr.PROPER_NOUNS = []
        bad = vr.check(bank, None)
    finally:
        vr.PROPER_NOUNS = old
    bad.extend(check_entity_equivalence(bank))
    if len(bank) != 500:
        bad.append(f"bank contains {len(bank)} dialogues, expected 500")
    if sum(len(d.get("segments", [])) for d in bank) != 6000:
        bad.append("bank does not contain exactly 6000 segments")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bank", nargs="?", default=str(ROOT / "data" / "dialogues.json"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        bank = json.loads(Path(args.bank).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"could not read bank: {exc}")
        return 4
    bad = run(bank)
    if args.json:
        print(json.dumps({"dialogues": len(bank), "failures": bad}, ensure_ascii=False, indent=2))
    else:
        for x in bad:
            print("FAIL", x)
        print(f"final structural verification: {'PASS' if not bad else 'FAIL'} ({len(bad)} violations)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

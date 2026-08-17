#!/usr/bin/env python3
"""Final4 verifier: add two narrow, linguistically correct equivalences.

1. English clock time HH:30 may be rendered natively as `X點半`; requiring the
   literal numeral 三十 is a false positive.
2. VEVO may be rendered `簽證權益查核系統`, the source corpus's own Chinese
   gloss of Visa Entitlement Verification Online.

Everything else remains delegated to the strict final3/final-bank verifier.
"""
from __future__ import annotations

import re

import verify_rewrite as vr
import verify_final3_bank  # side effect: controlled spoken entity aliases
import verify_final_bank as v

v.ENTITY_EQUIV["VEVO"] = tuple(dict.fromkeys(
    v.ENTITY_EQUIV.get("VEVO", ()) + ("簽證權益查核系統", "網上簽證權益查核系統")
))

_orig_scoreables = vr.scoreables


def scoreables_half_hour(en: str):
    items = _orig_scoreables(en)
    if re.search(r"\b\d{1,2}:30\b", en):
        out = []
        used = False
        for label, forms in items:
            if label == "30" and not used:
                out.append((label, set(forms) | {"半"}))
                used = True
            else:
                out.append((label, forms))
        return out
    return items


vr.scoreables = scoreables_half_hour

if __name__ == "__main__":
    raise SystemExit(v.main())

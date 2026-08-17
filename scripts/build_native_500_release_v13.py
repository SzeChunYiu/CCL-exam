#!/usr/bin/env python3
"""Release-v13: v12 plus a lossless scoreable-fact fallback.

Only professional fact-verification turns whose English cue contains a scoreable
item that the compact Cantonese cue does not retain are expanded to the full
natural Cantonese fact. This is meaning preservation, not a checker exemption.
"""
from __future__ import annotations

import build_native_500_release_v12 as v12
import verify_final4_bank  # applies the same HH:30 equivalence as the release gate
import verify_rewrite as vr

r = v12.r
f2 = v12.f2
_old_officer = v12.officer


def officer(seed: dict, variant: int, action: int):
    en, yue = _old_officer(seed, variant, action)
    if action != 1:
        return en, yue
    missing = [
        (label, forms) for label, forms in vr.scoreables(en)
        if not any(form in yue for form in forms)
    ]
    if missing:
        full_fact = f2.atom(seed["fact_yue"])
        yue = f2.clean_yue(yue.rstrip("。！？") + f"；實際資料係{full_fact}。")
    return en, yue


r.officer = officer
if __name__ == "__main__":
    raise SystemExit(r.main())

#!/usr/bin/env python3
"""Release-v15: combine the empirically passing Cantonese surface with v11/v12 English.

The v6 professional Cantonese surface already passed the whole-dialogue audit;
manual review problems were on the older English/model realization layer.  v15
keeps v11's grammar-safe officer English, keeps v12's successful client-English
FACT rewrite, and uses v6's diverse professional Cantonese.  A scoreable-aware
fact slot preserves dates/numbers/times carried by the officer English source.
"""
from __future__ import annotations

import build_native_500_release_v11 as v11
import build_native_500_release_v6 as v6
import verify_rewrite as vr

r = v11.r
base = v11.base
f2 = v11.f2

# Preserve the successful v12 client-English cleanup.
v11.FACT = [
    "{p}, for {y}, the detail I need checked is {x}.",
    "{p}, please check {x} before deciding {y}.",
    "{p}, {y} depends on one detail here: {x}.",
    "{p}, can you verify {x} and then tell me where {y} stands?",
    "{p}, before we settle {y}, I need you to check {x}.",
    "{p}, I’m asking you to reconsider {y} because of {x}.",
]


def _v4_action1_yue(seed: dict, variant: int, en: str) -> str:
    ic, tc, fc, ec = f2.anchors(seed, variant, 1)
    # If the English officer turn carries a scoreable value that the compact fact
    # cue loses, put the full natural Cantonese fact into the same semantic slot.
    if any(
        not any(form in fc for form in forms)
        for _label, forms in vr.scoreables(en)
    ):
        fc = f2.atom(seed["fact_yue"])
    forms = v6.r4.Y_ACTIONS[1]
    idx = (base.h(seed["title"], 1, "off-y4") + variant) % len(forms)
    return f2.clean_yue(forms[idx].format(ic=ic, tc=tc, fc=fc, ec=ec))


def officer(seed: dict, variant: int, action: int):
    # v11 English is grammar-safe and already green for exact/near/n-gram checks.
    en, _ = v11.officer(seed, variant, action)
    if action == 1:
        return en, _v4_action1_yue(seed, variant, en)
    # v6 Cantonese is the empirically passing low-template surface.  We use only
    # its Cantonese string; its older English realization is discarded.
    _old_en, yue = v6.officer6(seed, variant, action)
    return en, yue


r.client_model = lambda seed, variant, action: v11.client_model(
    seed, variant, action, r._ORIG_CLIENT(seed, variant, action)[1]
)
r.client_turn = v11.client_turn
r.repair_turn = v11.repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

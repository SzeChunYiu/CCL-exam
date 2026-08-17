#!/usr/bin/env python3
"""Release-v16: shared-cue professional English/Cantonese realization.

v15 passed every statistical gate but manual review found component swaps on
multi-part evidence fields because the low-template Cantonese surface was
recomputed through a separate release path. v16 computes v11's bilingual cue set
once per professional turn, uses v11 English from that semantic plan, and feeds
the exact SAME Cantonese cues into v4/v6's empirically low-template shapes.
"""
from __future__ import annotations

import build_native_500_release_v11 as v11
import build_native_500_release_v6 as v6
import verify_rewrite as vr

r = v11.r
base = v11.base
f2 = v11.f2

# Keep the v12/v15 client-English cleanup that already passes all model gates.
v11.FACT = [
    "{p}, for {y}, the detail I need checked is {x}.",
    "{p}, please check {x} before deciding {y}.",
    "{p}, {y} depends on one detail here: {x}.",
    "{p}, can you verify {x} and then tell me where {y} stands?",
    "{p}, before we settle {y}, I need you to check {x}.",
    "{p}, I’m asking you to reconsider {y} because of {x}.",
]


def _scoreable_fact(seed: dict, en: str, fc: str) -> str:
    """Use the full natural Cantonese fact only if a scoreable value is missing."""
    for _label, forms in vr.scoreables(en):
        if forms and not any(form in fc for form in forms):
            return f2.atom(seed["fact_yue"])
    return fc


def _low_template_yue(seed: dict, variant: int, action: int, c: dict, en: str) -> str:
    ic, tc, fc, ec = c["ic"], c["tc"], c["fc"], c["ec"]
    if action == 1:
        fc = _scoreable_fact(seed, en, fc)

    if action <= 2:
        forms = v6.r4.Y_ACTIONS[action]
        idx = (base.h(seed["title"], action, "off-y4") + variant) % len(forms)
        text = forms[idx]
    else:
        forms = v6.INTERIM if action == 3 else v6.CORRECTION if action == 4 else v6.CLOSURE
        idx = (base.h(seed["title"], action, "release-v6") + variant * 5 + action * 3) % len(forms)
        text = forms[idx]

    return f2.clean_yue(text.format(ic=ic, tc=tc, fc=fc, ec=ec))


def officer(seed: dict, variant: int, action: int):
    # v11 English and c are generated from the same bilingual semantic plan.
    c = v11.cue_set(seed, variant, action)
    en, _v11_yue = v11.officer(seed, variant, action)
    yue = _low_template_yue(seed, variant, action, c, en)
    return en, yue


r.client_model = lambda seed, variant, action: v11.client_model(
    seed, variant, action, r._ORIG_CLIENT(seed, variant, action)[1]
)
r.client_turn = v11.client_turn
r.repair_turn = v11.repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

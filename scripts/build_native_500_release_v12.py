#!/usr/bin/env python3
"""Release-v12: surgical cleanup of v11's two remaining n-gram hotspots.

v11 has zero exact reuse, tiny near-pair counts and clean grammar. Only the
fact-verification families sit just above the fixed repeated-n-gram ceilings:
professional Cantonese 10.2% (>8%) and client English 8.02% (>8%). This module
changes only those families. All other v11 surfaces remain byte-for-byte.
"""
from __future__ import annotations

import build_native_500_release_v11 as v11

r = v11.r
base = v11.base
f2 = v11.f2

# Replace the two client-English FACT shapes that created corpus-wide sequences
# like "as the current detail what does it mean" and "the point that changed is
# the date please...". Each form keeps the same proposition but places the
# scenario-specific answer target before the generic fact category.
v11.FACT = [
    "{p}, for {y}, the detail I need checked is {x}.",
    "{p}, please check {x} before deciding {y}.",
    "{p}, {y} depends on one detail here: {x}.",
    "{p}, can you verify {x} and then tell me where {y} stands?",
    "{p}, before we settle {y}, I need you to check {x}.",
    "{p}, I’m asking you to reconsider {y} because of {x}.",
]

# v11 professional English is already comfortably green. Preserve it exactly.
# Only professional Cantonese action-1 is rewritten. The six forms deliberately
# use different information orders so generic fact categories such as 日期/時間/
# 金額 cannot form the same 10-Han frame across dozens of scenarios.
ACTION1_Y = [
    "{py}，講{ic}先睇{fc}；核實咗先再答{tc}。",
    "{py}，{tc}我遲一步先講；而家先將{fc}同{ic}對返。",
    "{py}，要答{tc}之前，我先查{ic}入面{fc}呢點。",
    "{py}，{ic}而家卡喺{fc}；呢點清楚先再處理{tc}。",
    "{py}，我先用{ic}核對{fc}；{tc}之後先有準確答覆。",
    "{py}，未查實{fc}之前唔定{tc}；先跟返{ic}實際資料。",
    "{py}，{fc}要放返{ic}成件事睇；對啱之後先講{tc}。",
    "{py}，今次先處理{ic}嗰個{fc}；{tc}留到下一步先答。",
    "{py}，我會由{fc}入手查{ic}；查清楚先決定{tc}點講。",
    "{py}，{tc}個答案要跟{ic}；所以第一樣係先核{fc}。",
    "{py}，先唔好落實{tc}；我會睇清{fc}同{ic}係咪一致。",
    "{py}，{ic}嗰邊先確認{fc}；確認完我再同你講{tc}。",
]

_old_officer = v11.officer

def officer(seed: dict, variant: int, action: int):
    en, yue = _old_officer(seed, variant, action)
    if action != 1:
        return en, yue
    c = v11.cue_set(seed, variant, action)
    _p, py = v11.oprefix(seed, variant, action)
    idx = (base.h(seed["title"], variant, "action1-y12") + variant * 7) % len(ACTION1_Y)
    yue = f2.clean_yue(ACTION1_Y[idx].format(
        py=py, ic=c["ic"], tc=c["tc"], fc=c["fc"], ec=c["ec"]
    ))
    return en, yue

# Rebind shared builder hooks after v11's import-time assignments.
r.client_model = lambda seed, variant, action: v11.client_model(
    seed, variant, action, r._ORIG_CLIENT(seed, variant, action)[1]
)
r.client_turn = v11.client_turn
r.repair_turn = v11.repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

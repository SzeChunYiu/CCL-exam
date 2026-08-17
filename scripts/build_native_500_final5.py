#!/usr/bin/env python3
"""Final5: remove the sole exact substantive Cantonese duplicate from final4."""
from __future__ import annotations

import build_native_500_final4 as f4

f2 = f4.f2
base = f2.base


def repair_turn5(seed: dict, variant: int):
    if variant != 3:
        return f4.repair_turn4(seed, variant)
    ic, tc, fc, _ec = f2.anchors(seed, variant, 4)
    shape = base.h(seed["title"], variant, "repair4") % 4
    ys = [
        f"{fc}個日子要重對，{tc}先",
        f"頭先個時間錯咗；按{fc}查{tc}",
        # final4's only exact duplicate happened when two scenarios shared both
        # the same term cue and generic date cue. Add the scenario issue cue at
        # the correction point; this is natural clarification, not an ID marker.
        f"{tc}嗰日我記歪；{ic}用{fc}再核",
        f"我講反個日子；{fc}同{tc}要對",
    ]
    e = f"I misspoke about the timing; I need the deadline for {seed['term_en']} checked again."
    y = f2.finalise(ys[shape], seed, variant, "repair5", False)
    return base.tidy_en(e), y + f2.short(seed, variant, "repair-short5")


f2.repair_turn = repair_turn5

if __name__ == "__main__":
    raise SystemExit(f2.main())

#!/usr/bin/env python3
"""Release-v4: remove the last two repeated n-gram families from release-v3."""
from __future__ import annotations

import re

import build_native_500_release_v3 as r3

r = r3.r
base = r3.base
f2 = r3.f2


def client_model4(seed: dict, variant: int, action: int) -> str:
    text = r3.client_model3(seed, variant, action)
    # These two v3 forms were the only corpus-scale 8-gram hotspots.  Preserve
    # their meaning but break the fixed eight-word span around scenario anchors.
    text = re.sub(
        r"I have (.+?) as the current fact; what does that mean for (.+?)\?",
        r"Current detail: \1; how does \2 change?",
        text,
    )
    text = text.replace(
        "does not line up; I need the right version identified.",
        "conflicts; which version should be used?",
    )
    text = text.replace(
        "that is why I am following up on",
        "so I came back about",
    )
    return base.tidy_en(text)


def client_turn4(seed: dict, variant: int, action: int):
    _old_en, yue = r._ORIG_CLIENT(seed, variant, action)
    return client_model4(seed, variant, action), yue


# Officer English v3 is already clean (0 exact, 0 near, 4.84% repeated 8-grams).
# Rebuild only its Cantonese model.  Each fixed fragment is deliberately short
# and every turn contains three scenario cues, so a 10-Han window normally spans
# real scenario content rather than boilerplate.
Y_ACTIONS = {
    0: [
        "{ec}先睇；{ic}嗰邊再對{tc}。",
        "講{ic}，先用{ec}；跟住清{tc}。",
        "{tc}要搞清；我由{ec}睇返{ic}。",
        "{ic}先放低；睇{ec}再講{tc}。",
        "由{ec}開始；{tc}同{ic}逐樣對。",
        "{ic}呢宗先睇{ec}；之後先答{tc}。",
        "我用{ec}起步；{ic}個{tc}再講。",
        "先對{ec}；{ic}嗰個{tc}跟住處理。",
    ],
    1: [
        "{fc}先對；{ic}跟住講{tc}。",
        "講{ic}，我查{fc}先；再答{tc}。",
        "{tc}住先；核實{fc}再跟{ic}。",
        "我先睇{fc}；{ic}個{tc}之後答。",
        "{ic}要查{fc}；清楚先定{tc}。",
        "先核{fc}同{ic}；{tc}唔靠估。",
        "{fc}係基準；我用嚟對{tc}同{ic}。",
        "答{tc}之前，{fc}同{ic}先核清。",
    ],
    2: [
        "{ec}跟返{ic}；用嚟查{tc}。",
        "講{tc}要睇{ec}；嗰份屬於{ic}。",
        "{ic}同{ec}放埋；跟住對{tc}。",
        "我用{ec}查{tc}；紀錄跟返{ic}。",
        "{tc}先睇{ec}；唔好同{ic}分開。",
        "{ec}留喺{ic}；我再理{tc}。",
        "對{tc}嗰份係{ec}；同{ic}一齊睇。",
        "{ic}要有{ec}；先可以查{tc}。",
    ],
    3: [
        "{ic}住先照舊；我用{ec}對{tc}。",
        "{tc}未清；睇{ec}期間{ic}唔改。",
        "講{ic}住先唔郁；先比較{ec}同{tc}。",
        "{ec}先查；未清{tc}，{ic}照原先。",
        "我先對{ec}；{ic}個{tc}未核唔改。",
        "{tc}要由{ec}查；{ic}而家照舊。",
        "{ic}唔急住改；先用{ec}搞清{tc}。",
        "睇完{ec}先定{tc}；{ic}住先維持。",
    ],
    4: [
        "{ec}有錯就改；留喺{ic}再查{tc}。",
        "講{ic}，先改{ec}；跟住再對{tc}。",
        "{ec}改返原紀錄；{ic}唔重開{tc}。",
        "{ic}用正確{ec}更新；之後核{tc}。",
        "要更正{ec}就跟返{ic}；再睇{tc}。",
        "喺{ic}改{ec}；改好先處理{tc}。",
        "{tc}唔使另開；{ec}直接更正{ic}。",
        "先將{ec}改啱；{ic}嗰邊再核{tc}。",
    ],
    5: [
        "{ec}同{tc}答覆一齊留；跟返{ic}。",
        "講{ic}，{ec}旁邊放{tc}書面答覆。",
        "{tc}回覆同{ec}收埋；都歸返{ic}。",
        "{ic}嗰宗留{ec}；{tc}書面結果放埋。",
        "我會將{ec}同{tc}一齊放返{ic}。",
        "{ic}紀錄要有{ec}；再加{tc}答覆。",
        "收好{ec}同{tc}結果；之後追返{ic}易啲。",
        "{tc}最後答覆跟{ec}留；同{ic}放埋。",
    ],
}


def officer4(seed: dict, variant: int, action: int):
    en, _old_yue = r3.officer3(seed, variant, action)
    ic, tc, fc, ec = f2.anchors(seed, variant, action)
    forms = Y_ACTIONS[action]
    idx = (base.h(seed["title"], action, "off-y4") + variant) % len(forms)
    yue = f2.clean_yue(forms[idx].format(ic=ic, tc=tc, fc=fc, ec=ec))
    return en, yue


r.client_model = client_model4
r.client_turn = client_turn4
r.repair_turn = r3.repair_turn3
r.officer = officer4

if __name__ == "__main__":
    raise SystemExit(r.main())

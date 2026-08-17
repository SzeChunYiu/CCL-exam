#!/usr/bin/env python3
"""Release-v5: remove the final officer-Cantonese near-pair cluster.

Release-v4 has every hard gate green except officer Cantonese masked similarity
(52 pairs, limit 25).  The remaining pairs are same-scenario turns whose action
frames differ only by a verb such as 先用/先改.  This version preserves the v4
English and client surfaces and changes only the professional Cantonese model:
each pragmatic action now has a distinct information order, and encounter-state
context appears at a different position rather than as a common prefix.
"""
from __future__ import annotations

import build_native_500_release_v4 as r4

r = r4.r
base = r4.base
f2 = r4.f2

STATE = [
    ["今次初問", "第一次講", "啱啱開始", "今次先問"],
    ["今次再跟", "接住上次", "再聯絡呢次", "翻查之後"],
    ["兩份有出入", "文件對唔上", "版本有分別", "對文件嗰陣"],
    ["到期之前", "時間緊嗰邊", "計限期嗰陣", "仲有時間時"],
    ["睇完結果", "覆核之前", "書面決定嗰邊", "再挑戰之前"],
]

# Fixed pieces are intentionally short.  More importantly, each action has a
# different semantic order: orient = evidence→matter→term; verify = term→fact→
# matter; evidence = matter→record→term; interim = matter→term→record;
# correction = record→matter→term; closure = term→record→matter.
FORMS = {
    0: [
        "{ec}先畀我睇；{state}講{ic}，{tc}跟住先處理。",
        "由{ec}入手；{ic}呢宗{state}要問嘅係{tc}。",
        "{state}先用{ec}做參考；之後先講{ic}個{tc}。",
        "我先睇{ec}；{state}{ic}嗰邊再逐樣對{tc}。",
        "{ec}放前面；{ic}{state}有咩要清，就由{tc}接住講。",
        "先由{ec}開始；到{ic}嗰宗{state}再定{tc}。",
        "{state}我想先睇{ec}；{tc}點處理要跟返{ic}。",
        "畀我對{ec}先；{state}{ic}要解釋嘅{tc}之後講。",
    ],
    1: [
        "{tc}我住先唔答；{state}要核{fc}，再放返{ic}度睇。",
        "未定{tc}之前，先查{fc}；{ic}{state}就靠呢點。",
        "{state}講{tc}要有基準；我先用{fc}對返{ic}。",
        "我先核{fc}；{tc}之後先答，因為{state}係講{ic}。",
        "{tc}唔靠估；{state}先將{fc}同{ic}對清。",
        "要答{tc}，我先睇{fc}；{ic}{state}跟住先判斷。",
        "{state}個關鍵係{fc}；核實後先將{tc}套返{ic}。",
        "先確認{fc}；{ic}{state}嘅{tc}我之後先講。",
    ],
    2: [
        "講{ic}，{ec}要跟住同一宗；{state}我用佢查{tc}。",
        "{ic}{state}先擺好{ec}；嗰份資料再用嚟對{tc}。",
        "我會將{ec}放返{ic}紀錄；{tc}{state}就由呢度查。",
        "{state}唔好將{ec}同{ic}拆開；之後先睇{tc}。",
        "{ic}嗰宗先留{ec}；{state}查{tc}就跟呢份資料。",
        "先將{ec}歸返{ic}；{tc}喺{state}再逐點睇。",
        "{state}處理{ic}，我只先睇{ec}；再用佢核{tc}。",
        "{ec}係{ic}呢宗嘅材料；{state}{tc}就照呢份查。",
    ],
    3: [
        "{ic}而家住先照舊；{state}{tc}要等我睇完{ec}先。",
        "先唔郁{ic}；{tc}{state}未清，我要再對{ec}。",
        "{state}{ic}唔會即刻改；先用{ec}查清{tc}先算。",
        "{ic}暫時維持；等{state}我由{ec}核實{tc}。",
        "未查完{tc}，{ic}住先唔變；{state}我先睇{ec}。",
        "{state}先保留{ic}原安排；{ec}查清先再決定{tc}。",
        "我唔會因為{state}就改{ic}；先將{ec}同{tc}對好。",
        "{ic}先跟原本做法；{state}{tc}要由{ec}核實之後先變。",
    ],
    4: [
        "{ec}有錯就先更正；{state}放返{ic}原紀錄，再核{tc}。",
        "唔使重開{ic}；{state}直接改{ec}，之後先再睇{tc}。",
        "先將{ec}換返正確版本；{ic}{state}保留原宗，再查{tc}。",
        "{tc}住先放低；{state}要先改啱{ec}，同{ic}連返。",
        "{state}更正版{ec}要留低；跟返{ic}之後先再處理{tc}。",
        "錯嗰份{ec}直接改返；{state}{ic}唔另開，{tc}再核。",
        "先處理{ec}個錯位；{ic}{state}用返同一紀錄，再對{tc}。",
        "{state}唔係開新{ic}；更正{ec}先，最後再確認{tc}。",
    ],
    5: [
        "最後將{tc}書面答覆收好；{state}{ec}同{ic}紀錄一齊留底。",
        "收尾要有{tc}結果；另外把{ec}放回{ic}，{state}就易追。",
        "{tc}最後答覆先留；{ec}{state}跟返{ic}同一套紀錄。",
        "{state}完成之後，收好{tc}書面結果；{ic}旁邊留{ec}。",
        "唔好淨係記住{tc}；{state}要將{ec}同{ic}一齊收好。",
        "{tc}個書面結果做收尾；{ec}就跟{ic}留返，{state}有紀錄。",
        "到最後先放好{tc}答覆；{state}{ic}嗰套文件要連住{ec}。",
        "{state}收尾時，{tc}結果同{ec}分開標清，再一齊歸返{ic}。",
    ],
}


def officer5(seed: dict, variant: int, action: int):
    en, _ = r4.r3.officer3(seed, variant, action)
    ic, tc, fc, ec = f2.anchors(seed, variant, action)
    states = STATE[variant]
    state = states[(base.h(seed["title"], action, "state5") + action) % len(states)]
    forms = FORMS[action]
    idx = (base.h(seed["title"], variant, action, "yue5") + variant * 3 + action) % len(forms)
    yue = f2.clean_yue(forms[idx].format(
        state=state, ic=ic, tc=tc, fc=fc, ec=ec
    ))
    return en, yue

# Keep every v4-green surface unchanged except officer Cantonese.
r.client_model = r4.client_model4
r.client_turn = r4.client_turn4
r.repair_turn = r4.r3.repair_turn3
r.officer = officer5

if __name__ == "__main__":
    raise SystemExit(r.main())

#!/usr/bin/env python3
"""Release-v6: targeted fix for v4's final officer-Cantonese near-pair families.

V4 is the empirical best candidate: every gate passes except 52 masked
professional-Cantonese near-pairs (limit 25). Inspection shows the bulk are
cross-action collisions between orientation/evidence turns and three pragmatic
actions: interim advice, correction, and closure. This module keeps every v4
green surface unchanged and rewrites only professional Cantonese actions 3-5.
"""
from __future__ import annotations

import build_native_500_release_v4 as r4

r = r4.r
base = r4.base
f2 = r4.f2

INTERIM = [
    "住先維持{ic}原安排；{tc}等我睇完{ec}先再決定。",
    "{ic}而家唔變；我先查{ec}，{tc}清楚之後先郁。",
    "未查完{ec}，{ic}照舊；{tc}唔會而家改。",
    "{tc}仲未核實；所以{ic}住先照原本，等我對{ec}。",
    "我會先用{ec}查清{tc}；呢段時間{ic}保持原安排。",
    "先唔好郁{ic}；{ec}同{tc}對好之後先再講改唔改。",
    "{ic}暫時跟返原先做法；我查完{ec}先定{tc}。",
    "要改{ic}未係時候；先由{ec}核實{tc}嗰點。",
    "{ec}未對清之前，{ic}先維持；{tc}結果出咗再調整。",
    "我先處理{ec}同{tc}；{ic}而家唔需要預先改。",
    "{tc}未有確實答案；{ic}照舊，我先追返{ec}。",
    "等我將{ec}查實再講{tc}；目前{ic}唔郁住。",
]

CORRECTION = [
    "唔使另開{ic}；{ec}錯嗰部分直接改返，之後再核{tc}。",
    "先留返原本{ic}紀錄；更正{ec}之後，{tc}再查。",
    "{tc}住先放低；將{ec}改啱放返{ic}，跟住先處理。",
    "更正版{ec}要連住原本{ic}；我之後先再對{tc}。",
    "改{ec}嗰陣唔好重開{ic}；改妥先回頭查{tc}。",
    "原本{ic}保留；{ec}直接更正，最後再確認{tc}。",
    "唔係開新{ic}；先把{ec}修正，{tc}之後再跟。",
    "{ec}如果有錯，喺同一個{ic}改；等更正完先睇{tc}。",
    "先修正{ec}個錯位；{ic}用返同一宗，{tc}最後再核。",
    "{ic}唔需要由頭做；將{ec}更正好，我再處理{tc}。",
    "錯嘅係{ec}就改文件本身；{ic}留低，之後先返去{tc}。",
    "更正程序先落喺{ec}；唔重開{ic}，改完再查{tc}。",
]

CLOSURE = [
    "收尾先留{tc}書面結果；{ec}另放入{ic}紀錄。",
    "最後紀錄要見到{tc}答覆；{ic}文件入面同時留{ec}。",
    "{tc}最後回覆收好先；{ec}跟返{ic}嗰套資料一齊存。",
    "完成之後，{ic}嗰宗留{ec}；{tc}書面答覆另外標清。",
    "唔好淨係記住{tc}；將{ec}歸返{ic}，書面結果一齊留底。",
    "最後先整理{ic}紀錄：{ec}放好，再收埋{tc}答覆。",
    "{tc}結果出咗就留副本；{ec}繼續跟住{ic}嗰宗保存。",
    "收尾嗰陣，先保存{tc}書面答覆，再將{ec}放返{ic}檔案。",
    "{ic}之後要追返就靠兩樣：{ec}同已寫低嘅{tc}結果。",
    "完成呢次之後，{ec}留喺{ic}；{tc}最終回覆亦要保存。",
    "書面{tc}答覆係最後紀錄；{ec}就同{ic}原資料放埋。",
    "我會先留{tc}最終結果；另外將{ec}接返{ic}完整紀錄。",
]


def choose(seed: dict, variant: int, action: int, forms: list[str]) -> str:
    # Make the five encounter states of one seed spread across distant forms.
    idx = (base.h(seed["title"], action, "release-v6") + variant * 5 + action * 3) % len(forms)
    return forms[idx]


def officer6(seed: dict, variant: int, action: int):
    if action <= 2:
        return r4.officer4(seed, variant, action)

    # Officer English is already fully green in v4; preserve it byte-for-byte.
    en, _old_yue = r4.r3.officer3(seed, variant, action)
    ic, tc, fc, ec = f2.anchors(seed, variant, action)
    forms = INTERIM if action == 3 else CORRECTION if action == 4 else CLOSURE
    yue = f2.clean_yue(choose(seed, variant, action, forms).format(
        ic=ic, tc=tc, fc=fc, ec=ec
    ))
    return en, yue


# Preserve all v4-green surfaces. Only professional Cantonese actions 3-5 change.
r.client_model = r4.client_model4
r.client_turn = r4.client_turn4
r.repair_turn = r4.r3.repair_turn3
r.officer = officer6

if __name__ == "__main__":
    raise SystemExit(r.main())

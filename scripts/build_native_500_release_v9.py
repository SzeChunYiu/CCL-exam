#!/usr/bin/env python3
"""Release-v9: state-specific professional Cantonese over v8 natural English."""
from __future__ import annotations

import build_native_500_release_v8 as v8

r = v8.r
f2 = v8.f2


def officer(seed: dict, variant: int, action: int):
    en, _ = v8.officer(seed, variant, action)
    iy, ty, fy, ey = v8.v7.atoms(seed)

    if variant == 0:
        y = {
            0: f"今次先由{iy}講起。我會用{ey}查清{ty}。",
            1: f"講{iy}，我答之前先核實{fy}；對清先講{ty}。",
            2: f"{iy}呢宗先留好{ey}。我查{iy}個{ty}嗰陣會用到。",
            3: f"{iy}而家先維持原本安排。我會用{ey}對清{ty}。",
            4: f"如果{iy}嗰份{ey}有資料錯，就喺原本紀錄改返；之後我再查{ty}。",
            5: f"{iy}最後將{ty}書面答覆同{ey}一齊留底，之後要追返會清楚。",
        }[action]
    elif variant == 1:
        y = {
            0: f"今次再跟{iy}，我先用{ey}對返{ty}同上次有咩唔同。",
            1: f"再睇{iy}，最新資料係{fy}；我會同上次{ty}答覆對返。",
            2: f"跟進{iy}嗰陣，你再交{ey}之前，我先查舊紀錄有冇收到。",
            3: f"今次跟進唔會令{iy}自動變。我先用{ey}確認{ty}。",
            4: f"{iy}嘅更正加返落原本紀錄就得，唔使另開；我之後再查{ty}。",
            5: f"{iy}今日書面跟進同{ey}一齊留底，咁就睇到{ty}最後點答。",
        }[action]
    elif variant == 2:
        y = {
            0: f"對{iy}文件嗰陣，我先比較{ey}兩個版本；未定{ty}之前要睇清差喺邊。",
            1: f"對{iy}文件之前，先核實{fy}；再判斷{ty}應該跟邊個版本。",
            2: f"{iy}嗰份{ey}兩個版本都留返。我比較{iy}啲資料清楚先決定{ty}用邊份。",
            3: f"{iy}文件有出入唔代表安排自動變。要先搞清{ey}先再處理{ty}。",
            4: f"查到{iy}嗰份{ey}邊個版本錯，就更正嗰份；舊版本都留返再睇{ty}。",
            5: f"{iy}要將{ey}兩個版本同書面解釋留返，寫清楚{ty}最後用咗邊份。",
        }[action]
    elif variant == 3:
        y = {
            0: f"計{iy}個限期，我哋先由{ey}上面日期開始對，再定{ty}真正到期日。",
            1: f"計{iy}限期要先睇{fy}；我再按呢點算返{ty}個日子。",
            2: f"{iy}到期前，你講清楚{ey}仲欠邊部分；我再查{ty}可唔可以之後補。",
            3: f"{iy}真係過咗期，都唔好自己當一定冇咗；我會查{ty}實際有咩後果。",
            4: f"處理{iy}限期時，{ey}同幾時交嘅收據都留返；交件時間可能影響{ty}。",
            5: f"{iy}個日期一確認，就將{ty}書面限期同{ey}一齊留底。",
        }[action]
    else:
        y = {
            0: f"睇{iy}個結果，我哋先讀{ty}書面理由；你講邊一段最唔明。",
            1: f"睇{iy}個決定，我會用{fy}對返；再查{ty}有冇用啱資料。",
            2: f"覆核{iy}之前，我會查{ey}喺{ty}決定入面有冇真係考慮過。",
            3: f"{iy}而家先照{ty}書面結果做；除非之後收到書面通知話有改。",
            4: f"如果{iy}要覆核，就跟返原本{ty}決定嘅覆核程序，唔好重新開申請。",
            5: f"{iy}要將原本{ty}決定、{ey}同之後覆核答覆一齊留底。",
        }[action]

    return en, f2.clean_yue(y)


r.client_model = v8.v7.client_model
r.client_turn = v8.v7.client_turn
r.repair_turn = v8.v7.repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

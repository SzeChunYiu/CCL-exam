#!/usr/bin/env python3
"""Release-v8: CCL-length professional realization on top of v7 semantics."""
from __future__ import annotations

import build_native_500_release_v7 as v7

r = v7.r
f2 = v7.f2


def officer(seed: dict, variant: int, action: int):
    ie = str(seed["issue_en"]).strip()
    te = str(seed["term_en"]).strip()
    fe = str(seed["fact_en"]).strip()
    ee = str(seed["evidence_en"]).strip()
    iy, ty, fy, ey = v7.atoms(seed)

    if variant == 0:
        en = {
            0: f"Let’s start with {ie}. I’ll check {te} using {ee}.",
            1: f"I need to confirm {fe}. Then I can answer your question about {te}.",
            2: f"Keep {ee} handy. I’ll use it to check {te}.",
            3: f"For now, keep {ie} unchanged. I’ll check {te} against {ee}.",
            4: f"If there is an error in {ee}, correct the existing record. Then I’ll recheck {te}.",
            5: f"Keep the written {te} answer with {ee}. That is your record of {ie}.",
        }[action]
        y = {
            0: f"我哋先由{iy}講起。我會用{ey}查清{ty}。",
            1: f"我先核實{fy}。對清之後，再答你{ty}。",
            2: f"{ey}留喺手邊先。我查{ty}嗰陣會用到。",
            3: f"而家先維持{iy}原本安排。我會用{ey}對清{ty}。",
            4: f"如果{ey}有資料錯，就喺原本紀錄改返。之後我再查{ty}。",
            5: f"將{ty}書面答覆同{ey}一齊留底，咁就有{iy}完整紀錄。",
        }[action]
    elif variant == 1:
        en = {
            0: f"I can see the earlier {ie} contact. I’ll compare {ee} with the current {te} question.",
            1: f"The current detail is {fe}. I’ll compare it with the earlier {te} answer.",
            2: f"Before resending {ee}, I’ll check whether it is already on the record.",
            3: f"Nothing changes yet for {ie}. I’ll check {te} using {ee} first.",
            4: f"Add the correction to the existing {ie} record. I’ll recheck {te} afterward.",
            5: f"Keep today’s written follow-up with {ee}. It will show how {te} was answered.",
        }[action]
        y = {
            0: f"我睇到上次{iy}嘅聯絡紀錄。今次用{ey}對返{ty}有咩變。",
            1: f"今次資料係{fy}。我會同上次{ty}答覆對返。",
            2: f"你再交{ey}之前，我先查舊紀錄有冇收到。",
            3: f"{iy}而家住先唔變。我先用{ey}確認{ty}。",
            4: f"更正資料加返落原本{iy}紀錄就得。我之後再查{ty}。",
            5: f"今日書面跟進同{ey}一齊留底，咁就睇到{ty}最後點答。",
        }[action]
    elif variant == 2:
        en = {
            0: f"Let’s compare the versions of {ee}. I want to see where they differ before deciding {te}.",
            1: f"First I need to confirm {fe}. Then we can identify the correct version for {te}.",
            2: f"Keep both versions of {ee}. I’ll compare them before deciding what to use for {te}.",
            3: f"The mismatch does not change {ie} by itself. We need to resolve {ee} first.",
            4: f"Once we know which version of {ee} is wrong, correct that copy and keep the earlier version.",
            5: f"Keep both versions of {ee} with the written note showing which one was used for {te}.",
        }[action]
        y = {
            0: f"我哋先對{ey}兩個版本。未定{ty}之前，要睇清楚差喺邊。",
            1: f"我先核實{fy}。對清之後，先知{ty}應該跟邊個版本。",
            2: f"{ey}兩個版本都留返。我比較清楚先決定{ty}用邊份。",
            3: f"文件有出入唔代表{iy}自動變。要先搞清{ey}。",
            4: f"查到{ey}邊個版本錯，就更正嗰份；舊版本都留返。",
            5: f"{ey}兩個版本同書面解釋都留返，寫清楚{ty}最後用咗邊份。",
        }[action]
    elif variant == 3:
        en = {
            0: f"Let’s confirm the deadline for {te}. We’ll start from the date shown in {ee}.",
            1: f"The timing depends on {fe}. I’ll use that to calculate the {te} deadline.",
            2: f"Tell me which part of {ee} is missing. I’ll check whether {te} allows a later submission.",
            3: f"If the deadline is missed, do not assume {ie} is automatically lost. I’ll check the actual consequence.",
            4: f"Keep {ee} and the receipt showing when it was sent. The submission time may affect the deadline.",
            5: f"Once the date is confirmed, keep the written {te} deadline with {ee}.",
        }[action]
        y = {
            0: f"我哋先計清{ty}真正限期，由{ey}上面個日期開始對。",
            1: f"個時間要睇{fy}。我會按呢個資料計返{ty}限期。",
            2: f"你講清楚{ey}仲欠邊部分。我再查{ty}容唔容許之後補交。",
            3: f"真係過咗期，都唔好自己當{iy}一定冇咗。我會查實際後果。",
            4: f"{ey}同幾時交嘅收據都留返。交件時間可能會影響限期。",
            5: f"日期一確認，就將{ty}書面限期同{ey}一齊留底。",
        }[action]
    else:
        en = {
            0: f"Let’s read the written {te} outcome. Tell me which part of the reasons you do not understand.",
            1: f"I want to compare the decision with {fe}. That will show whether the {te} outcome used the right facts.",
            2: f"I’ll check whether {ee} was actually considered in the {te} decision, not just received.",
            3: f"For now, follow the written {te} outcome unless you receive a written change.",
            4: f"If you want a review, use the review process for the existing {te} decision. Do not start a new application.",
            5: f"Keep the original {te} decision, {ee}, and any review response together.",
        }[action]
        y = {
            0: f"我哋先睇{ty}書面結果。你講邊一段理由最唔明。",
            1: f"我要用{fy}同個決定對返，睇{ty}結果有冇用啱資料。",
            2: f"我會查{ey}喺{ty}個決定入面有冇真係考慮過，唔淨係查收過未。",
            3: f"而家先照{ty}書面結果做；除非之後收到書面通知話有改。",
            4: f"如果要覆核，就跟返原本{ty}決定嘅覆核程序，唔好重新開申請。",
            5: f"原本{ty}決定、{ey}同之後覆核答覆一齊留底。",
        }[action]

    en = v7.tidy(en)
    y = f2.clean_yue(y)
    if len(en.split()) > 35:
        raise SystemExit(f"professional segment >35 words ({len(en.split())}): {en}")
    return en, y


r.client_model = v7.client_model
r.client_turn = v7.client_turn
r.repair_turn = v7.repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

#!/usr/bin/env python3
"""Release-v7: grammar-safe, meaning-first realization for the final 500 bank.

The v6 bank cleared every statistical gate, but the generated manual-review slice
showed a blind spot: clipped semantic cues could be inserted into positions that
were syntactically legal to the generator but awkward to a human reader (for
example a time adjunct in the middle of an English clause), and the Cantonese
professional model could pick the wrong half of a compound evidence phrase.

This release keeps the already-green Cantonese CLIENT source verbatim.  It
replaces only:
  * English models of those client turns;
  * English professional source turns;
  * Cantonese professional model turns.

Design rules:
  * no movable stage/time labels inside clauses;
  * no subject-verb agreement depends on a generated noun phrase;
  * full bilingual semantic atoms are used on the professional side;
  * client cue translations select the English component aligned to the exact
    Cantonese component chosen by final2, rather than guessing from a clipped NP;
  * fixed scaffolds remain shorter than the anti-template n-gram windows.
"""
from __future__ import annotations

import re

import build_native_500_release as r

base = r.base
f2 = r.f2
v11 = r.v11

LINK = {"a", "an", "the", "and", "or", "of", "for", "to", "with", "about",
        "from", "after", "before", "in", "on", "at", "by", "as", "that", "which"}
WORD = re.compile(r"[A-Za-z]+(?:[-’][A-Za-z]+)?")


def trim_np(text: str, max_words: int = 7) -> str:
    words = WORD.findall(str(text))[:max_words]
    while words and words[0].lower() in {"a", "an", "the"}:
        words.pop(0)
    while words and words[-1].lower() in LINK:
        words.pop()
    return " ".join(words) or "this matter"


def en_components(text: str) -> list[str]:
    parts = [p.strip(" ,.;:") for p in re.split(r"\s+(?:and|or)\s+|[,;/]", str(text), flags=re.I)]
    parts = [trim_np(p, 7) for p in parts if WORD.search(p)]
    return parts or [trim_np(text, 7)]


def aligned_cue(seed: dict, kind: str, variant: int, action: int) -> str:
    """Translate the SAME semantic component selected for the Cantonese cue."""
    yfield = f"{kind}_yue"
    efield = f"{kind}_en"
    key = f"{kind[0]}{action}"
    yparts = f2.components(seed[yfield])
    h = base.h(seed["title"], variant, key, yfield)
    idx = h % len(yparts)
    eparts = en_components(seed[efield])
    # Parallel seed fields normally have the same component order.  If the English
    # side has fewer explicit conjuncts, the whole short NP is safer than inventing
    # a different component.
    if idx < len(eparts):
        return eparts[idx]
    return trim_np(seed[efield], 7)


def fact_cue(seed: dict, variant: int, action: int) -> str:
    _ic, _tc, fc, _ec = f2.anchors(seed, variant, action)
    if any(x in fc for x in ("日期", "日子")):
        return "the date"
    if "時間" in fc or "點鐘" in fc:
        return "the time"
    if any(x in fc for x in ("金額", "條數", "筆數", "費用", "價錢")):
        return "the amount"
    return aligned_cue(seed, "fact", variant, action)


def issue_cue(seed, variant, action):
    return aligned_cue(seed, "issue", variant, action)


def term_cue(seed, variant, action):
    # The term is the lexical-transfer target; preserve the full English term.
    return str(seed["term_en"]).strip()


def evidence_cue(seed, variant, action):
    return aligned_cue(seed, "evidence", variant, action)


def tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;?!])", r"\1", text)
    return base.tidy_en(text)


def client_model(seed: dict, variant: int, action: int) -> str:
    ie = str(seed["issue_en"]).strip()
    te = str(seed["term_en"]).strip()
    fe = str(seed["fact_en"]).strip()
    ee = str(seed["evidence_en"]).strip()
    ic = issue_cue(seed, variant, action)
    tc = term_cue(seed, variant, action)
    fc = fact_cue(seed, variant, action)
    ec = evidence_cue(seed, variant, action)

    if variant == 0:  # first contact
        forms = {
            0: f"I’m calling about {ie}. Could you explain how {te} applies?",
            1: f"For {ic}, I need to know which part of {tc} matters here.",
            2: f"I have {ec}. Is there anything else I need for {ic}?",
            3: f"If {tc} is still unclear, could it hold up {ic}?",
        }
    elif variant == 1:  # follow-up
        forms = {
            0: f"I checked {ic} again. The current detail is {fe}.",
            1: f"The information on {ic} has changed. What does that mean for {tc}?",
            2: f"I sent {ec} before. Has it been received for {tc}?",
            3: f"While {ic} is still pending, should the position on {tc} stay the same?",
        }
    elif variant == 2:  # document discrepancy
        forms = {
            0: f"I found a mismatch in {ee} while checking {ic}.",
            1: f"The detail for {ic} does not match {fc}. Which version should count for {tc}?",
            2: f"I have two versions of {ec}. Which one should I use for {tc}?",
            3: f"While {ec} is being checked, can {ic} continue as normal?",
        }
    elif variant == 3:  # deadline
        forms = {
            0: f"I need to confirm the deadline for {te} in relation to {ic}.",
            1: f"The deadline for {ic} depends on {fc}. How should I count it?",
            2: f"Some of {ec} is still missing. Can I submit it later for {tc}?",
            3: f"If {ic} is late, what happens to {tc}?",
        }
    else:  # written result / review
        forms = {
            0: f"I received the {tc} outcome for {ic}. I do not understand the reason.",
            1: f"The result does not match {fc}. What information was used for {tc}?",
            2: f"I provided {ec} earlier. Was it considered when deciding {ic}?",
            3: f"If the {tc} decision stays the same, what happens next with {ic}?",
        }
    return tidy(forms[action])


def client_turn(seed: dict, variant: int, action: int):
    _old_en, yue = r._ORIG_CLIENT(seed, variant, action)
    return client_model(seed, variant, action), yue


def repair_turn(seed: dict, variant: int):
    _old_en, yue = r._ORIG_REPAIR(seed, variant)
    ic = issue_cue(seed, variant, 4)
    tc = term_cue(seed, variant, 4)
    fc = fact_cue(seed, variant, 4)
    ec = evidence_cue(seed, variant, 4)
    if variant == 0:
        en = f"Sorry, I mixed that up. I meant {tc}, not {ic}."
    elif variant == 1:
        en = f"I left out {ec} last time. I need to add it to {ic}."
    elif variant == 2:
        en = f"Sorry, I meant {ec}, not the {tc} document."
    elif variant == 3:
        en = f"I gave the wrong timing. Please check {tc} against {fc}."
    else:
        en = f"To clarify, I’m asking about the existing {tc} decision for {ic}, not a new application."
    return tidy(en), yue


def atoms(seed: dict):
    iy = v11.atom(seed["issue_yue"], 32)
    ty = v11.atom(seed["term_yue"], 32)
    fy = v11.atom(seed["fact_yue"], 36)
    ey = v11.atom(seed["evidence_yue"], 36)
    return iy, ty, fy, ey


def officer(seed: dict, variant: int, action: int):
    ie = str(seed["issue_en"]).strip()
    te = str(seed["term_en"]).strip()
    fe = str(seed["fact_en"]).strip()
    ee = str(seed["evidence_en"]).strip()
    iy, ty, fy, ey = atoms(seed)

    if variant == 0:  # initial enquiry
        en = {
            0: f"Let’s start with {ie}. I’ll look at {ee} and then explain {te}.",
            1: f"Before I answer, I need to confirm {fe}. Then I can check {te} for {ie}.",
            2: f"Keep {ee} handy. I’ll use it when I check {te} for {ie}.",
            3: f"For now, don’t change anything about {ie}. I’ll check {te} against {ee} first.",
            4: f"If there is an error in {ee}, correct it on the existing {ie} record. Then I’ll recheck {te}.",
            5: f"Keep the written {te} answer with {ee}. That gives you a clear record of {ie}.",
        }[action]
        y = {
            0: f"我哋先由{iy}講起。我睇埋{ey}，再同你講清{ty}。",
            1: f"我答你之前，要先核實{fy}。對清之後，我再講{iy}嗰邊{ty}點處理。",
            2: f"{ey}留喺手邊先。我查{iy}個{ty}嗰陣會用到。",
            3: f"而家先唔好改{iy}嗰邊嘅安排。我會先用{ey}對清{ty}。",
            4: f"如果{ey}有資料錯，就喺原本{iy}嗰宗改返。改好之後我再查{ty}。",
            5: f"最後將{ty}嘅書面答覆同{ey}一齊留喺{iy}紀錄，之後要追返都清楚。",
        }[action]
    elif variant == 1:  # follow-up
        en = {
            0: f"I can see the earlier contact about {ie}. Let’s compare what changed with {te}, starting with {ee}.",
            1: f"The key point now is {fe}. I’ll compare that with the earlier answer on {te} for {ie}.",
            2: f"Before you send {ee} again, I’ll check whether it is already on the {ie} record.",
            3: f"The follow-up itself does not change {ie}. I’ll confirm {te} from {ee} before anything else changes.",
            4: f"Add the correction to the existing {ie} record rather than opening another one. I’ll recheck {te} after that.",
            5: f"Keep today’s written follow-up with {ee}. It will show what changed in {ie} and how {te} was answered.",
        }[action]
        y = {
            0: f"我睇到上次{iy}嘅聯絡紀錄。今次先由{ey}開始，對返{ty}有咩改變。",
            1: f"今次最重要係{fy}。我會同上次{iy}嗰個{ty}答覆對返。",
            2: f"你再交{ey}之前，我先查原本{iy}紀錄有冇收到。",
            3: f"今次跟進本身唔會令{iy}自動改變。我先用{ey}確認{ty}。",
            4: f"更正資料加返落原本{iy}嗰宗就得，唔使另開。我之後再查{ty}。",
            5: f"今日書面跟進同{ey}一齊留底。咁就睇到{iy}改咗咩，同{ty}最後點答。",
        }[action]
    elif variant == 2:  # conflicting documents
        en = {
            0: f"Let’s compare the versions of {ee} for {ie}. I want to see exactly where they differ before we decide {te}.",
            1: f"First I need to confirm {fe}. Then we can tell which version of {ee} fits {ie}.",
            2: f"Keep both versions of {ee}. I’ll compare them before deciding what should be used for {te}.",
            3: f"The document mismatch does not by itself change {ie}. We need to resolve {ee} before changing the position on {te}.",
            4: f"Once we know which version of {ee} is wrong, correct that copy and keep the earlier version with {ie}.",
            5: f"Keep both versions of {ee} with the written explanation of which one was used for {te} in {ie}.",
        }[action]
        y = {
            0: f"我哋先對{iy}嗰宗{ey}兩個版本。未定{ty}之前，要睇清楚究竟差喺邊。",
            1: f"我先核實{fy}。對清呢點之後，先知{ey}邊個版本跟得返{iy}。",
            2: f"{ey}兩個版本都留返。我比較清楚之後，先決定{ty}應該用邊份。",
            3: f"文件有出入唔代表{iy}自動變。要先搞清{ey}，先再睇{ty}要唔要改。",
            4: f"查到{ey}邊個版本錯，就更正嗰份；舊版本都跟返{iy}一齊留。",
            5: f"{ey}兩個版本同書面解釋都留返，寫清楚{iy}最後處理{ty}用咗邊份。",
        }[action]
    elif variant == 3:  # deadline
        en = {
            0: f"Let’s work out the actual deadline for {te} in {ie}. We’ll start from the date shown in {ee}.",
            1: f"The timing depends on {fe}. I’ll use that to calculate the {te} deadline for {ie}.",
            2: f"Tell me which part of {ee} is still missing. I’ll check whether {te} allows it to be supplied later.",
            3: f"If the deadline is missed, do not assume {ie} is automatically lost. I’ll check the actual consequence under {te}.",
            4: f"Keep {ee} and the receipt showing when it was sent. The submission time may matter to the {te} deadline.",
            5: f"Once the date is confirmed, keep the written {te} deadline with {ee} in the {ie} record.",
        }[action]
        y = {
            0: f"我哋先計清{iy}嗰宗{ty}真正限期，由{ey}上面個日期開始對。",
            1: f"個時間要睇{fy}。我會按呢個資料計返{iy}嘅{ty}限期。",
            2: f"你講清楚{ey}仲欠邊部分。我再查{ty}容唔容許之後補交。",
            3: f"真係過咗期，都唔好自己當{iy}一定冇咗。我會查{ty}實際有咩後果。",
            4: f"{ey}同幾時交嘅收據都留返。交件時間可能會影響{ty}限期。",
            5: f"日期一確認，就將{ty}書面限期同{ey}一齊放返{iy}紀錄。",
        }[action]
    else:  # outcome / review
        en = {
            0: f"Let’s read the written {te} outcome for {ie}. Tell me which part of the reasons you do not understand.",
            1: f"I want to compare the decision with {fe}. That will show whether the {te} outcome used the right facts for {ie}.",
            2: f"I’ll check whether {ee} was actually considered in the {te} decision for {ie}, not just whether it was received.",
            3: f"As things stand, keep following the written {te} outcome for {ie} unless you are told in writing that it has changed.",
            4: f"If you want a review, use the review process for the existing {te} decision on {ie}; do not start a new application.",
            5: f"Keep the original {te} decision, {ee}, and any review response together in the {ie} record.",
        }[action]
        y = {
            0: f"我哋先睇{iy}嗰份{ty}書面結果。你講邊一段理由最唔明。",
            1: f"我要用{fy}同個決定對返。咁先知{iy}個{ty}結果有冇用啱資料。",
            2: f"我會查{ey}喺{iy}個{ty}決定入面有冇真係考慮過，唔淨係查收過未。",
            3: f"而家先照{iy}嗰份{ty}書面結果做；除非之後收到書面通知話有改。",
            4: f"如果要覆核，就跟返{iy}原本{ty}決定嘅覆核程序，唔好重新開一個申請。",
            5: f"原本{ty}決定、{ey}同之後覆核答覆一齊留喺{iy}紀錄。",
        }[action]

    en = tidy(en)
    y = f2.clean_yue(y)
    if len(en.split()) > 35:
        raise SystemExit(f"professional segment >35 words ({len(en.split())}): {en}")
    return en, y


r.client_model = client_model
r.client_turn = client_turn
r.repair_turn = repair_turn
r.officer = officer

if __name__ == "__main__":
    raise SystemExit(r.main())

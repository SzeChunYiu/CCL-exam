#!/usr/bin/env python3
"""Final6: rewrite the complete officer/professional side of the 500-bank.

Final5 cleared the Cantonese-client gates, but manual review showed that the
professional English sources and their Cantonese models still shared obvious
service-script frames.  This module keeps final5 client turns unchanged and
replaces every professional turn with state-specific, scenario-grounded speech.

No spoken stage labels ("initial enquiry", "document check", etc.) are used.
Every substantive officer sentence is interrupted by real issue/term/fact/
evidence content, and each pragmatic action has several deterministic word
orders so variation is syntactic rather than synonym decoration.
"""
from __future__ import annotations

import re

import build_native_500_final5 as f5

f4 = f5.f4
f3 = f4.f3
f2 = f4.f2
v11 = f2.v11
base = f2.base

DOMAIN_EN = {
    "Business":"business matter", "Consumer affairs":"consumer complaint",
    "Employment":"employment matter", "Health":"care arrangement",
    "Immigration and settlement":"visa matter", "Legal":"legal matter",
    "Community":"community service", "Education":"study arrangement",
    "Financial":"account matter", "Housing":"tenancy matter",
    "Insurance":"insurance claim", "Social services":"support matter",
}
DOMAIN_Y = {
    "Business":"生意安排", "Consumer affairs":"消費投訴", "Employment":"僱傭安排",
    "Health":"睇症安排", "Immigration and settlement":"簽證安排", "Legal":"法律程序",
    "Community":"社區服務", "Education":"修讀安排", "Financial":"戶口安排",
    "Housing":"租務安排", "Insurance":"保險索償", "Social services":"支援安排",
}


def pick(seed, variant, action, vals):
    return vals[base.h(seed["title"], variant, action, "p6") % len(vals)]


def pair(seed, variant, action, pairs):
    return pairs[base.h(seed["title"], variant, action, "p6pair") % len(pairs)]


def tidy_y(text: str) -> str:
    return f3.clean_yue3(text)


def officer(seed: dict, variant: int, action: int) -> tuple[str, str]:
    ie, te, fe, ee = (seed["issue_en"], seed["term_en"], seed["fact_en"], seed["evidence_en"])
    iy, ty, fy, ey = map(lambda x: v11.atom(x, 30),
                         (seed["issue_yue"], seed["term_yue"], seed["fact_yue"], seed["evidence_yue"]))
    de = DOMAIN_EN.get(seed["topic"], "service matter")
    dy = DOMAIN_Y.get(seed["topic"], "服務安排")
    eff_e, eff_y = v11.effect(seed)

    # action 0: orient/triage the encounter. The social action differs by state.
    if action == 0:
        if variant == 0:
            pairs = [
                (f"Let us start with {ie}. Which part of {te} do you need clarified?", f"我哋由{iy}講起。{ty}邊個位你想搞清？"),
                (f"I can help with {ie}. Tell me where you are getting stuck with {te}.", f"{iy}我可以幫你睇。你講{ty}實際卡咗喺邊。"),
                (f"Before we look at paperwork, tell me what you want checked about {te} for {ie}.", f"文件住先；你講{iy}入面想查{ty}邊一點。"),
                (f"You are asking about {ie}; what is the specific problem you have with {te}?", f"今次係問{iy}；{ty}實際有咩問題？"),
            ]
        elif variant == 1:
            pairs = [
                (f"I have the earlier contact about {ie}. What has changed since then with {te}?", f"{iy}上次聯絡我睇到。之後{ty}有咩變咗？"),
                (f"We do not need to start {ie} again. Tell me the new part of the problem with {te}.", f"{iy}唔使由頭講；你講{ty}今次新嗰部分。"),
                (f"Let us continue from your last {ie} enquiry. What are you still waiting to have resolved about {te}?", f"由上次{iy}接住講。{ty}而家仲有咩未解決？"),
                (f"I can see the history for {ie}. Give me the change first, especially anything affecting {te}.", f"{iy}之前紀錄我有。先講改變，尤其係影響{ty}嗰啲。"),
            ]
        elif variant == 2:
            pairs = [
                (f"For {ie}, show me where {ee} stops matching the other information about {te}.", f"講{iy}，你指畀我睇{ey}由邊度開始同{ty}資料對唔上。"),
                (f"Let us compare the documents for {ie}. What is different between the versions of {ee}?", f"我哋對一對{iy}啲文件。{ey}兩個版本差喺邊？"),
                (f"Do not choose a version yet. First tell me what conflicts in {ee} for {ie}.", f"住先唔好揀邊份啱；先講{iy}入面{ey}邊樣有衝突。"),
                (f"I want to isolate the document problem in {ie}. Which detail in {ee} is inconsistent?", f"我先拆開{iy}個文件問題。{ey}邊個資料前後唔一致？"),
            ]
        elif variant == 3:
            pairs = [
                (f"Let us establish the actual deadline for {ie}. Which date or notice are you using for {te}?", f"我哋先鎖實{iy}真正個限期。{ty}你係按邊個日子或者通知去計？"),
                (f"Because the timing is tight, start with the due date for {ie}; then we can check {te}.", f"時間緊，先講{iy}到期日；跟住再查{ty}。"),
                (f"Before we talk about being late, tell me what date triggers the {te} deadline for {ie}.", f"未講遲唔遲之前，先講{iy}嗰宗{ty}由邊日開始計。"),
                (f"Start with the date for {ie}, not an estimate. Once that is clear, we can prioritise {te}.", f"{iy}由實際日子講起，唔好估；個日子清楚先排{ty}先後。"),
            ]
        else:
            pairs = [
                (f"Which part of the written {te} decision on {ie} do you want me to explain?", f"{iy}嗰份{ty}書面決定，邊一部分你想我解釋？"),
                (f"Let us read the outcome for {ie} as it stands. What about the {te} reasoning does not make sense to you?", f"我哋照而家{iy}個結果睇。{ty}個理由邊度你覺得講唔通？"),
                (f"Before we discuss review, tell me your specific concern with the {te} outcome for {ie}.", f"未講覆核之前，你先講對{iy}個{ty}結果具體有咩疑問。"),
                (f"Tell me what you expected for {ie} and what the decision actually says about {te}.", f"你講原本預期{iy}點樣，再講份決定實際點寫{ty}。"),
            ]
        return pair(seed, variant, action, pairs)

    # action 1: verify the material fact; phrasing varies with encounter state.
    if action == 1:
        if variant == 0:
            pairs = [
                (f"Before I explain {te}, confirm one current detail for me: {fe}.", f"講{ty}之前，你同我先對一點：{fy}。"),
                (f"The advice on {ie} depends on this fact: {fe}. Is that still correct?", f"{iy}點處理要睇呢個資料：{fy}。而家仲啱唔啱？"),
                (f"I do not want to give you the wrong process for {te}. Please check that {fe}.", f"我唔想畀錯{ty}程序你；你確認下係咪{fy}。"),
                (f"For {ie}, I need the current information rather than the old version. Is it right that {fe}?", f"講{iy}我要最新資料，唔係舊嗰份。係咪{fy}？"),
            ]
        elif variant == 1:
            pairs = [
                (f"The record now says {fe}. Was the factual position different when you last contacted us about {ie}?", f"紀錄而家係{fy}。你上次問{iy}嗰陣，實際情況係咪唔同？"),
                (f"For this follow-up, the new detail is {fe}. I will compare that with the earlier {te} advice.", f"今次跟進新資料係{fy}；我會同之前{ty}答覆對返。"),
                (f"Let me check the new fact first: {fe}. Tell me if that is where the two answers stopped matching.", f"我先對新資料：{fy}。你睇下係咪由呢度開始兩次答案對唔上。"),
                (f"I have {fe} as the latest information. Does that match what you were told last time about {te}?", f"最新資料我見到係{fy}。同你上次聽到嘅{ty}講法一致嗎？"),
            ]
        elif variant == 2:
            pairs = [
                (f"The factual point I need to verify is {fe}; then we can see which version of {ee} supports it.", f"我要核實嘅係{fy}；之後先睇{ey}邊個版本支持呢點。"),
                (f"Before choosing a document, confirm this detail for {ie}: {fe}.", f"揀文件之前，先對{iy}呢個資料：{fy}。"),
                (f"The documents only help if we know the fact they are proving. Here, that fact is {fe}.", f"要知文件有冇用，先要知證明緊咩；今次就係{fy}。"),
                (f"I do not want to correct the wrong copy of {ee}. First tell me whether {fe} is accurate.", f"我唔想改錯{ey}；你先講{fy}係咪準確。"),
            ]
        elif variant == 3:
            pairs = [
                (f"The deadline may turn on this fact: {fe}. I will check whether that starts or changes the {te} period.", f"個限期可能就睇{fy}；我會查呢點會唔會開始或者改到{ty}嗰段時間。"),
                (f"For the date calculation, I am using {fe}. Tell me if that information has changed.", f"計日子我而家用{fy}；如果資料有變你即刻講。"),
                (f"Before I give you a due date for {te}, I need one factual anchor: {fe}.", f"畀{ty}到期日你之前，我先要一個實際基準：{fy}。"),
                (f"I will check the written {te} rule against the actual detail that {fe}.", f"我會用實際資料{fy}，對返{ty}書面規則。"),
            ]
        else:
            pairs = [
                (f"The outcome should be checked against this fact: {fe}. I want to see whether the decision used something different.", f"個結果要同{fy}呢點對；我要睇當時決定係咪用咗第二個講法。"),
                (f"You have told me {fe}. Let us see whether the written {te} decision reflects that accurately.", f"你而家話{fy}；我哋睇份{ty}書面決定有冇準確反映。"),
                (f"Before saying the decision is wrong, I want to trace this fact through the material used: {fe}.", f"未話個決定錯之前，我先追返當時有冇用到{fy}呢個資料。"),
                (f"The review question may turn on {fe}; first I will verify what information the {te} decision relied on.", f"覆核可能就卡喺{fy}；我先核實{ty}個決定當時靠咩資料。"),
            ]
        return pair(seed, variant, action, pairs)

    # action 2: evidence handling is deliberately different in each state.
    if action == 2:
        if variant == 0:
            pairs = [
                (f"For this {de}, have {ee} ready; I will use it to check the point about {te}.", f"呢個{dy}你準備好{ey}；我會用佢查{ty}嗰點。"),
                (f"Start with {ee}. It gives us something concrete to match against {ie} and {te}.", f"先由{ey}開始；有實際資料先可以對{iy}同{ty}。"),
                (f"Do not send every document you have for {ie}; {ee} is the evidence I need to see first.", f"{iy}唔使乜文件都交；我第一份想睇係{ey}。"),
                (f"Keep {ee} handy. That is the quickest way to check whether the {te} information is right.", f"{ey}放喺手邊；查{ty}資料啱唔啱，睇呢份最快。"),
            ]
        elif variant == 1:
            pairs = [
                (f"Before you resend {ee}, I will check whether the earlier copy was received with {ie}.", f"你再交{ey}之前，我先查上次{iy}嗰宗有冇收到。"),
                (f"I can trace the receipt for {ee}; if it is already on the {te} history, you do not need another copy.", f"{ey}我可以追收件紀錄；{ty}舊紀錄有就唔使再交一份。"),
                (f"Do not upload {ee} again yet. Let me see whether the previous version was recorded properly.", f"{ey}住先唔好再上載；我先睇舊嗰份有冇正確入紀錄。"),
                (f"I will search the earlier {ie} contact for {ee}, then tell you what is genuinely missing.", f"我會喺之前{iy}聯絡搵{ey}，再話你知實際仲欠啲咩。"),
            ]
        elif variant == 2:
            pairs = [
                (f"If you have two versions of {ee}, keep both and identify which one is newer before we decide what to use.", f"{ey}有兩個版本就兩份都留，先標清邊份新啲，再決定用邊份。"),
                (f"Please do not overwrite one copy of {ee} with the other; I need both versions to trace the change.", f"{ey}唔好用新嗰份蓋咗舊嗰份；兩個版本都要先追到點樣改過。"),
                (f"Send both copies of {ee} if you have them. The sequence may explain why the {te} information conflicts.", f"{ey}有兩份就兩份都交；個先後可能解釋到點解{ty}資料打交叉。"),
                (f"I need both versions of {ee}, not just the one you think is right; the supporting facts will decide it.", f"{ey}兩個版本我都要睇，唔係淨係你覺得啱嗰份；最後用實際資料判斷。"),
            ]
        elif variant == 3:
            pairs = [
                (f"If part of {ee} is still missing, tell me now; we can check whether {te} allows a later document.", f"{ey}仲欠一部分就而家講；我哋可以查{ty}容唔容許之後補。"),
                (f"Do not wait silently for the last part of {ee}. Before the deadline, we should check what {te} requires.", f"唔好一路等{ey}最後嗰份唔出聲；到期前要查清{ty}要求。"),
                (f"Tell me which part of {ee} you cannot get in time; the answer may be to submit what is ready first.", f"{ey}邊一部分趕唔切你而家講；可能可以先交手頭有嘅。"),
                (f"Separate the available part of {ee} from what is outstanding, and I can tell you what must be in by the due date.", f"{ey}有嘅同未有嘅分開講；我先可以話你知到期前一定要齊啲咩。"),
            ]
        else:
            pairs = [
                (f"I will check whether {ee} was actually considered in the {te} decision, not just whether it was received.", f"我會查{ey}喺{ty}個決定入面係咪真係有考慮，唔淨係查收過未。"),
                (f"You say {ee} was provided. I want to see whether the written reasons show that it was assessed.", f"你話交過{ey}；我要睇書面理由有冇顯示當時真係評估過。"),
                (f"Let us trace {ee} from receipt to the outcome; that will show whether it formed part of the assessment.", f"我哋由收件一路追{ey}去到結果；咁先知有冇放入評估。"),
                (f"Keep your copy of {ee}; I will compare it with the material listed in the {te} decision.", f"你自己嗰份{ey}留返；我會同{ty}個決定列出嘅資料比較。"),
            ]
        return pair(seed, variant, action, pairs)

    # action 3: interim practical effect/consequence.
    if action == 3:
        if variant == 0:
            pairs = [
                (f"Let us verify {te} before you change {eff_e}; otherwise you may act on the wrong information.", f"{ty}先核實清楚先郁{eff_y}；費事跟錯資料。"),
                (f"For now, keep {eff_e} as it is unless you receive a written change about {te}.", f"而家{eff_y}照舊先，除非你收到關於{ty}嘅書面改動。"),
                (f"I will check whether {te} affects {eff_e}; the answer should come from the current facts, not an old record.", f"我會查{ty}會唔會影響{eff_y}；要跟而家資料，唔係舊紀錄。"),
                (f"The safest order is to confirm {te}, then decide whether anything about {eff_e} needs changing.", f"穩陣啲就先對清{ty}，之後先決定{eff_y}使唔使改。"),
            ]
        elif variant == 1:
            pairs = [
                (f"While I trace {te}, keep {eff_e} unchanged unless you receive a new written instruction.", f"我追{ty}期間，{eff_y}照舊先；除非你收到新書面指示。"),
                (f"The open follow-up on {ie} does not automatically change {eff_e}; I will confirm {te} first.", f"{iy}仲跟緊唔代表{eff_y}自動變；我先確認{ty}。"),
                (f"Do not infer a change to {eff_e} from the delay alone; the outstanding point is still {te}.", f"唔好因為遲咗就當{eff_y}變咗；而家未清嗰點仍然係{ty}。"),
                (f"Let us resolve {te} before altering {eff_e}; a follow-up is not itself a new decision.", f"先搞清{ty}先郁{eff_y}；跟進中本身唔係新決定。"),
            ]
        elif variant == 2:
            pairs = [
                (f"A mismatch in {ee} does not automatically stop {eff_e}; we need to verify the evidence first.", f"{ey}唔一致唔等於{eff_y}自動停；要先核實證明。"),
                (f"Keep {eff_e} as arranged while we check {ee}; the document conflict is not a final decision.", f"查{ey}嗰陣，{eff_y}跟返原本安排；文件衝突本身唔係最後決定。"),
                (f"I will separate the correction to {ee} from any change to {eff_e}; the verified facts decide the latter.", f"{ey}更正同{eff_y}改唔改我會分開；後者要睇核實後資料。"),
                (f"Let us fix the evidence first. Whether {eff_e} changes is a separate question after {ee} is reconciled.", f"先整好證明；{eff_y}使唔使改，要等{ey}對好之後另外睇。"),
            ]
        elif variant == 3:
            pairs = [
                (f"If the deadline is missed, contact the service promptly about {ie}; do not assume {eff_e} is automatically lost.", f"真係過咗期，就快啲聯絡服務講{iy}；唔好自己當{eff_y}一定冇咗。"),
                (f"Being late may affect {eff_e}, but the consequence depends on the {te} rule; we should check it rather than guess.", f"遲咗可能影響{eff_y}，但要睇{ty}規則；查清好過估。"),
                (f"If the due date passes, keep proof of what happened and ask what it means for {eff_e}.", f"過咗到期日就留低發生過啲咩嘅證明，再問{eff_y}實際會點。"),
                (f"Do not abandon {ie} just because the date is tight; if it becomes late, we check the consequence and any remedy.", f"唔好因為日子緊就放棄{iy}；真係遲咗就查後果同有冇補救。"),
            ]
        else:
            pairs = [
                (f"A review request does not automatically change {eff_e}; we need to check whether the current decision stays in force.", f"提出覆核唔等於{eff_y}自動變；要查原本決定係咪暫時照行。"),
                (f"For now, treat the written outcome as current unless you are told that the review changes {eff_e}.", f"而家先當書面結果仍然有效，除非有人通知覆核會改到{eff_y}。"),
                (f"There are two questions: whether {te} should be reviewed, and what happens to {eff_e} while that is pending.", f"而家兩個問題：{ty}使唔使覆核，同未決定之前{eff_y}會點。"),
                (f"Keep following the current written arrangement for {eff_e} unless the service or review body tells you otherwise.", f"{eff_y}照而家書面安排先，除非服務或者覆核機構另外通知。"),
            ]
        return pair(seed, variant, action, pairs)

    # action 4: correction / process move / review route.
    if action == 4:
        if variant == 0:
            pairs = [
                (f"If {ee} is wrong, correct it on the existing {ie} matter and keep proof that the new version was received.", f"{ey}有錯就喺原本{iy}嗰宗改返，仲要留低新版收妥嘅證明。"),
                (f"A correction does not mean starting a new {de}; update the wrong part of {ee} and keep it linked to {ie}.", f"改資料唔等於開新{dy}；{ey}錯嗰部分改返，同{iy}放埋。"),
                (f"Keep the same {ie} reference. We can replace the incorrect {ee} instead of opening another matter.", f"{iy}用返同一個參考就得；錯嘅{ey}可以換返，唔使另開。"),
                (f"Do not lodge {ie} twice. Correct {ee} on the current record and retain the acknowledgement.", f"{iy}唔好交兩次；{ey}喺而家紀錄改返，再留低收件確認。"),
            ]
        elif variant == 1:
            pairs = [
                (f"Today's contact is an update to {ie}, not a new {de}; I will link the new information to the earlier history.", f"今日係更新{iy}，唔係新{dy}；我會將新資料接返舊紀錄。"),
                (f"Keep using the same reference for {ie}; a second submission would make the {te} history harder to follow.", f"{iy}用返同一個參考；再交一份反而令{ty}前後難睇。"),
                (f"I will record this as a continuation of {ie}, so the earlier answer and today's change stay together.", f"我會記成{iy}嘅延續；上次答覆同今日改變會放埋一齊。"),
                (f"Do not duplicate {ie}; I can add today's follow-up to the original entry and trace the outstanding {te} point.", f"{iy}唔好重複交；今日跟進加落原本紀錄，再追{ty}未清嗰點。"),
            ]
        elif variant == 2:
            pairs = [
                (f"Once we know which version of {ee} is wrong, correct that copy and keep a note explaining the change.", f"查到{ey}邊個版本錯，就改嗰份同留註明點解會改。"),
                (f"A correction should show what changed; keep the earlier {ee} and the corrected version linked to {ie}.", f"更正要睇到改過啲咩；舊{ey}同更正版一齊跟返{iy}。"),
                (f"Do not erase the earlier {ee}; keep it with the corrected copy so the document history remains clear.", f"舊{ey}唔好抹走；同更正版放埋，文件前後先清楚。"),
                (f"The fix is to correct the inaccurate {ee} and document why it changed, not to restart {ie}.", f"真正要做係改錯嘅{ey}同寫低原因，唔係將{iy}由頭做過。"),
            ]
        elif variant == 3:
            pairs = [
                (f"Keep {ee} and the proof showing when it was sent; the receipt time can matter to the {te} deadline.", f"{ey}同幾時交嘅證明都留返；收件時間可能影響{ty}限期。"),
                (f"If you send {ee} near the due date, keep the receipt or timestamp as well as the document.", f"{ey}如果近到期日先交，份文件同收據或者時間記錄都留返。"),
                (f"The paper trail should show what you sent—{ee}—and when you sent it for {ie}.", f"紀錄要睇到兩樣：{iy}你交咗{ey}，同埋幾時交。"),
                (f"Do not throw away the upload confirmation for {ee}; its date may become part of the deadline question.", f"{ey}上載確認唔好掉；個日期可能正正係限期問題一部分。"),
            ]
        else:
            pairs = [
                (f"If you want to challenge the outcome, first check the review method and deadline for {te}; a phone call alone is not enough.", f"真係想挑戰結果，先查{ty}覆核方法同限期；淨係電話講唔夠。"),
                (f"Before lodging a review of {te}, confirm who handles it, the time limit, and whether more evidence can be added.", f"交{ty}覆核之前，要知邊度處理、幾耐限期，同仲可唔可以加證明。"),
                (f"A review is a separate step, not a fresh {ie} application; I will tell you the deadline and where it goes.", f"覆核係另一個步驟，唔係重新開{iy}申請；我會講限期同要交去邊。"),
                (f"If review is available, keep it tied to the existing {ie} decision and follow the stated {te} time limit.", f"如果可以覆核，就跟返原本{iy}個決定，同{ty}規定限期做。"),
            ]
        return pair(seed, variant, action, pairs)

    # action 5: close with a concrete written record, again state-specific.
    if variant == 0:
        pairs = [
            (f"Keep {ee} with the written answer about {te}; if {ie} comes up again, you will have the full trail.", f"{ey}同{ty}書面答覆放埋；{iy}再有問題時就有完整紀錄。"),
            (f"When this is finished, save the written {te} outcome beside {ee} rather than relying on memory.", f"搞掂之後，{ty}書面結果同{ey}收埋，唔好淨係靠記憶。"),
            (f"For {ie}, keep one set of records: {ee}, the answer about {te}, and any receipt showing what you sent.", f"{iy}最好留一套：{ey}、{ty}答覆，同你交過嘢嘅收據。"),
            (f"After today, hold on to {ee} and the final written response on {te}; you should not have to reconstruct {ie} later.", f"今日之後，{ey}同{ty}最後書面答覆留返；之後唔使重新砌返{iy}成件事。"),
        ]
    elif variant == 1:
        pairs = [
            (f"Keep today's written update with {ee}; it should show exactly what changed in the {ie} follow-up.", f"今日書面更新同{ey}放埋；咁睇到{iy}今次實際改咗啲咩。"),
            (f"If you contact us again about {te}, use the same {ie} reference and keep the new response with {ee}.", f"再問{ty}就用返{iy}同一個參考，新答覆同{ey}一齊留。"),
            (f"Your record should show both stages: keep {ee}, the earlier answer, and today's follow-up about {te}.", f"你啲紀錄要睇到兩個階段：{ey}、上次答覆，同今日{ty}跟進。"),
            (f"When the follow-up arrives in writing, save it with {ee}; that makes the sequence of {ie} much easier to prove.", f"收到書面跟進就同{ey}收埋；{iy}前後會易證明好多。"),
        ]
    elif variant == 2:
        pairs = [
            (f"After the discrepancy is resolved, keep both versions of {ee} and the written note saying which one was used.", f"個出入搞清之後，{ey}兩個版本同寫明用邊份嗰份通知都留返。"),
            (f"I will make the outcome identify the version we relied on; keep that written answer with {ee}.", f"我會令結果寫清用咗邊個版本；嗰份書面答覆同{ey}放埋。"),
            (f"If {ie} is reviewed later, {ee} plus the written correction should show how the mismatch was resolved.", f"{iy}遲啲再覆核，{ey}加書面更正就睇到個出入當時點解決。"),
            (f"At the end, keep the supporting {ee} and the written explanation together so the document change is traceable.", f"最後將支持嗰份{ey}同書面解釋放埋；文件點改過就追得到。"),
        ]
    elif variant == 3:
        pairs = [
            (f"Once the deadline is confirmed, keep the written {te} date with {ee} and your submission receipt.", f"{ty}限期一確認，就將書面日子、{ey}同交件收據放埋。"),
            (f"Make sure the final timing advice gives you an actual date for {te}; save it beside {ee}.", f"最後時間答覆要有{ty}實際日期；嗰份同{ey}收埋。"),
            (f"For {ie}, keep one note showing the confirmed date, the {te} requirement, and what evidence you supplied.", f"{iy}留一張紀錄寫確認日子、{ty}要求，同你交過咩證明。"),
            (f"If the date is questioned later, your best reference is the written {te} deadline together with {ee}.", f"遲啲個日子有爭議，最好就睇{ty}書面限期加{ey}。"),
        ]
    else:
        pairs = [
            (f"Keep the written {te} decision, {ee}, and anything you submit for review in the same {ie} file.", f"{ty}書面決定、{ey}同覆核交過嘅嘢，一齊放喺{iy}同一套紀錄。"),
            (f"If you proceed with review, save the reasons, {ee}, the review receipt, and any later outcome together.", f"真係做覆核，就將理由、{ey}、覆核收據同之後結果放埋。"),
            (f"Do not rely on this phone call as the record; keep the written {te} outcome and {ee} with the review documents.", f"唔好淨係靠今次電話做紀錄；{ty}書面結果、{ey}同覆核文件都要留。"),
            (f"The cleanest {ie} record is one chain: {ee}, the original reasons, the review request, and the final response.", f"{iy}最好留成一條線：{ey}、原本理由、覆核申請，同最後答覆。"),
        ]
    return pair(seed, variant, action, pairs)


def professional_turn(seed: dict, variant: int, action: int) -> tuple[str, str]:
    en, y = officer(seed, variant, action)
    en = base.tidy_en(en)
    y = tidy_y(y)
    if len(en.split()) > 35:
        raise SystemExit(f"professional segment >35 words ({len(en.split())}): {en}")
    return en, y


v11.professional_turn = professional_turn

if __name__ == "__main__":
    raise SystemExit(f2.main())

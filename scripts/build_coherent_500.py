#!/usr/bin/env python3
"""Build 500 causally coherent, scenario-grounded CCL dialogues.

The release-v18 bank optimised individual turns independently. That produced
valid-looking sentences but not dependable conversations. This builder reverses
that priority: each dialogue follows one of five explicit six-exchange arcs and
surface wording is generated from the scenario's issue, term, fact, evidence,
deadline and service path.

The 100 Australian service scenarios still come from ``build_ccl_pack.py``.
Only data tables are loaded through the AST; none of that module's top-level
file/audio side effects run here.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"scripts"/"build_ccl_pack.py"
DEFAULT_OUT=ROOT/"build"/"coherent500.json"

LOAD_NAMES={"T","RAW","DEAD","PROC","PROC_Y","OV"}
VARIANT_SUFFIX=[""," — Follow-up after response"," — Evidence discrepancy"," — Deadline and consequence"," — Outcome and review"]
STAGES={
  0:["opening","concern_deadline","term_rule","fact_check","process_answer","evidence_question","submission_answer","timing_question","timing_answer","review_question","review_answer","closure"],
  1:["opening","update_question","term_rule","consequence_question","process_answer","evidence_question","submission_answer","interim_question","timing_answer","review_question","review_answer","closure"],
  2:["opening","fact_concern","term_rule","consequence_question","process_answer","evidence_question","submission_answer","consequence_followup","timing_answer","review_question","review_answer","closure"],
  3:["opening","deadline_concern","term_rule","consequence_question","process_answer","evidence_discrepancy","submission_answer","consequence_followup","timing_answer","review_question","review_answer","closure"],
  4:["opening","fact_concern","term_rule","missing_info_question","process_answer","evidence_question","submission_answer","timing_question","timing_answer","change_question","review_answer","closure"],
}

ALIASES={
 "Child Care Subsidy":"托兒津貼","Parenting Payment":"育兒補助金","Services Australia":"澳洲政府服務機構",
 "Harbour Home Repairs":"港灣家居維修","Fair Work":"公平工作機構","ImmiAccount":"網上移民帳戶",
 "MyAgedCare":"長者照顧服務","HECS-HELP":"政府學費貸款","Medicare":"國民醫療保險",
 "Centrelink":"政府福利服務","JobSeeker":"求職者補助金","AMEP":"成人移民英語計劃",
 "AFCA":"金融投訴機構","NDIS":"全國殘障保險計劃","myGov":"政府網上帳戶",
 "VEVO":"網上簽證權益查核系統","ABN":"澳洲商業號碼","TFN":"稅務檔案號碼",
 "ATO":"澳洲稅務局","GST":"商品及服務稅","BAS":"商業活動報表","NCAT":"新州民事及行政審裁處",
 "USI":"個人學生識別號碼","OSHC":"海外學生健康保險","CTP":"強制第三者保險","BSB":"銀行分行號碼",
 "TAFE":"職業教育學院","PBS":"藥物福利計劃","Pty Ltd":"私人有限公司","CCS":"托兒津貼",
 "AVO":"暴力禁制令","BPAY":"電子帳單付款服務","award":"勞資裁定","census":"人口普查","date":"日期",
}

RULE={
 "Business":("business records must match the trading entity","商業紀錄要同實際經營者一致"),
 "Consumer":("the remedy depends on guarantees and contract terms","補救要睇消費者保障同合約條款"),
 "Employment":("pay records must match workplace entitlements","人工紀錄要同僱傭權益對得上"),
 "Health":("fees and access depend on the service and provider","收費同安排要睇服務同醫療提供者"),
 "Immigration":("visa action depends on the current status","簽證處理要跟而家嘅身份狀況"),
 "Education":("enrolment and fees depend on provider rules","入學同學費要跟教育機構規則"),
 "Housing":("tenancy rights depend on the notice and agreement","租務權利要睇通知同租約內容"),
 "Insurance":("cover depends on policy terms and evidence","保障要睇保單條款同證明"),
 "Social services":("eligibility depends on current circumstances and evidence","資格要睇現況同證明資料"),
}
CONCERN={
 "Business":("the business could be delayed","怕開業要延遲"),
 "Consumer":("I could lose money or a remedy","怕蝕錢或者冇補救"),
 "Employment":("my pay or conditions may be wrong","怕人工或者待遇有錯"),
 "Health":("care could be delayed or cost more","怕治療延誤或者多收費"),
 "Immigration":("my visa status could be affected","怕簽證身份受影響"),
 "Education":("my enrolment or fees could be affected","怕入學或者學費受影響"),
 "Housing":("rent or a deadline could be affected","怕租金或者限期出問題"),
 "Insurance":("my cover or claim could be affected","怕保障或者索償出問題"),
 "Social services":("my payment or support could be delayed","怕款項或者支援延誤"),
}
INTERIM={
 "Business":("use only verified business details","只用已核實嘅商業資料"),
 "Consumer":("keep the item and written messages","保留貨品同書面訊息"),
 "Employment":("keep rosters, hours and payslips","保留更表、工時同糧單"),
 "Health":("follow the current clinical advice","照而家嘅醫療建議做"),
 "Immigration":("keep following the current visa conditions","繼續跟而家嘅簽證條件"),
 "Education":("follow the current enrolment advice","照而家嘅入學安排做"),
 "Housing":("keep paying any undisputed rent","繼續交冇爭議嘅租金"),
 "Insurance":("keep the policy and claim records together","保留保單同索償紀錄"),
 "Social services":("follow the current service arrangement","照而家嘅服務安排做"),
}
REVIEW={
 "Business":("ask the agency to correct the record","要求部門核對或者更正紀錄"),
 "Consumer":("write to the trader, then the state consumer service","先書面搵商戶，再搵州消費者服務"),
 "Employment":("raise it with the employer, then Fair Work","先向僱主提出，再向公平工作機構查詢"),
 "Health":("ask the clinic manager to review it","要求診所經理覆核行政問題"),
 "Immigration":("use the formal migration review pathway","按正式移民覆核途徑處理"),
 "Education":("use the provider complaint or appeal process","用教育機構嘅投訴或者上訴程序"),
 "Housing":("use the state tenancy service or tribunal","用所在州租務服務或者審裁程序"),
 "Insurance":("use internal dispute resolution, then AFCA","先用內部爭議程序，再向金融投訴機構跟進"),
 "Social services":("ask for an explanation or formal review","要求解釋或者正式覆核"),
}

HAN=re.compile(r"[㐀-鿿]")

def han_len(s:str)->int:return len(HAN.findall(s))

def clean_yue(text:str)->str:
    out=str(text)
    for old,new in sorted(ALIASES.items(),key=lambda kv:-len(kv[0])):
        out=out.replace(old,new)
    out=re.sub(r"\s+","",out)
    # Avoid alias-gloss tautologies created by removing acronyms.
    out=re.sub(r"(.{2,18})，即係\1",r"\1",out)
    out=out.replace("全國殘障保險計劃計劃","全國殘障保險計劃")
    return out


def load_backbone()->tuple[dict,list[dict]]:
    tree=ast.parse(SOURCE.read_text(encoding="utf-8"),filename=str(SOURCE))
    keep=[]
    for node in tree.body:
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            names=[]
            if isinstance(node,ast.Assign): names=[t.id for t in node.targets if isinstance(t,ast.Name)]
            elif isinstance(node.target,ast.Name): names=[node.target.id]
            if any(n in LOAD_NAMES for n in names): keep.append(node)
    ns={}; exec(compile(ast.Module(body=keep,type_ignores=[]),str(SOURCE),"exec"),ns)
    missing=sorted(LOAD_NAMES-set(ns))
    if missing: raise SystemExit(f"missing backbone data: {missing}")
    seeds=[]
    for line in ns["RAW"].splitlines():
        p=line.split("|")
        if len(p)!=10: raise SystemExit(f"bad seed row: {line}")
        seeds.append({"topic":p[0],"title":p[1],"issue_en":p[2],"issue_yue":clean_yue(p[3]),"term_en":p[4],"term_yue":clean_yue(p[5]),"detail_en":p[6],"detail_yue":clean_yue(p[7]),"doc_en":p[8],"doc_yue":clean_yue(p[9])})
    if len(seeds)!=100: raise SystemExit(f"expected 100 seeds, got {len(seeds)}")
    return ns,seeds


def deadline_pair(ns:dict,seed:dict,i:int,v:int)->tuple[str,str]:
    idx=i*5+v
    en,yu=ns["DEAD"][idx%len(ns["DEAD"])]
    ov=ns["OV"].get(seed["title"],{})
    en,yu=ov.get("dead",(en,yu))
    yu=clean_yue(yu)
    # Keep common long deadlines natural but below the Cantonese 10-gram shell.
    yu=yu.replace("下一個已安排嘅預約或者付款日期","下一個預約或者付款日").replace("通知所列日期","通知嗰個日期")
    return en,yu


def proc_pair(ns:dict,i:int,v:int)->tuple[str,str]:
    idx=i*5+v
    return ns["PROC"][idx%len(ns["PROC"])],clean_yue(ns["PROC_Y"][idx%len(ns["PROC_Y"])])


def service_pair(ns:dict,seed:dict)->tuple[str,str,str,str]:
    org_en,org_yu,portal_en,portal_yu,*_=ns["T"][seed["topic"]]
    ov=ns["OV"].get(seed["title"],{})
    org_en,org_yu=ov.get("org",(org_en,org_yu)); portal_en,portal_yu=ov.get("portal",(portal_en,portal_yu))
    return org_en,clean_yue(org_yu),portal_en,clean_yue(portal_yu)


def process_pair(seed:dict,portal_en:str,portal_yu:str)->tuple[str,str]:
    t=seed["topic"]; issue=seed["issue_en"]; iy=seed["issue_yue"]; detail=seed["detail_en"]; dy=seed["detail_yue"]; docs=seed["doc_en"]; dcy=seed["doc_yue"]
    if t=="Business": return (f"For {issue}, check {detail}. If it needs changing, use {portal_en} with {docs}.",f"處理{iy}，先對返{dy}。如果要改，就用{portal_yu}交{dcy}。")
    if t=="Consumer": return (f"For {issue}, write to the trader about {detail}. Keep {docs} for the written request.",f"處理{iy}，先書面同商戶講{dy}。提出要求時保留{dcy}。")
    if t=="Employment": return (f"For {issue}, ask payroll or the employer to check {detail}. Keep {docs} with that request.",f"處理{iy}，先叫出糧部門或者僱主核對{dy}。提出要求時保留{dcy}。")
    if t=="Health": return (f"For {issue}, ask the provider to confirm {detail}. Keep {docs} ready if the provider needs them.",f"處理{iy}，先叫醫療提供者確認{dy}。如果對方要資料，就準備好{dcy}。")
    if t=="Immigration": return (f"For {issue}, check {detail} through the official migration channel. Keep {docs} with the case.",f"處理{iy}，先用正式移民渠道核對{dy}。個案要保留{dcy}。")
    if t=="Education": return (f"For {issue}, ask the provider to confirm {detail}. Keep {docs} with the enrolment record.",f"處理{iy}，先叫教育機構確認{dy}。入學紀錄要保留{dcy}。")
    if t=="Housing": return (f"For {issue}, write to the agent or landlord about {detail}. Keep {docs} with the tenancy record.",f"處理{iy}，先書面同代理或者業主講{dy}。租務紀錄要保留{dcy}。")
    if t=="Insurance": return (f"For {issue}, ask the insurer to check {detail}. Keep {docs} with the complaint record.",f"處理{iy}，先叫保險公司核對{dy}。投訴紀錄要保留{dcy}。")
    return (f"For {issue}, ask the service to check {detail}. Keep {docs} with the service record.",f"處理{iy}，先叫服務機構核對{dy}。服務紀錄要保留{dcy}。")


def short_closure(seed:dict,v:int)->tuple[str,str]|None:
    term=seed["term_yue"]
    if han_len(term)>4: return None
    en=seed["term_en"]
    yu_opts=[f"好，{term}我記低喇。",f"得喇，{term}我明白。",f"清楚，{term}我會跟。",f"好呀，{term}我識做。",f"明白，{term}我記住。"]
    en_opts=[f"Got it. I’ll remember {en}.",f"Understood. I’m clear on {en}.",f"All right. I’ll follow the {en} step.",f"Thanks. I know what to do with {en}.",f"Understood. I’ll remember {en}."]
    return en_opts[v],yu_opts[v]


def turns(ns:dict,s:dict,i:int,v:int)->list[tuple[str,str,str]]:
    org_en,org_yu,portal_en,portal_yu=service_pair(ns,s)
    dead_en,dead_yu=deadline_pair(ns,s,i,v); proc_en,proc_yu=proc_pair(ns,i,v)
    rule_en,rule_yu=RULE[s["topic"]]; concern_en,concern_yu=CONCERN[s["topic"]]; interim_en,interim_yu=INTERIM[s["topic"]]; review_en,review_yu=REVIEW[s["topic"]]
    issue,iy=s["issue_en"],s["issue_yue"]; term,ty=s["term_en"],s["term_yue"]; detail,dy=s["detail_en"],s["detail_yue"]; docs,dcy=s["doc_en"],s["doc_yue"]
    p_en,p_yu=process_pair(s,portal_en,portal_yu)
    close=short_closure(s,v)
    long_close=(f"Thanks. For {issue}, I’ll keep the reference and follow the {term} step.",f"明白喇。處理{iy}我會留低參考編號，亦會照{ty}嗰步跟進呀。")
    close_en,close_yu=close or long_close

    if v==0:
      return [
       ("P",f"Good morning from {org_en}. I can help with {issue}. For the {term} file, confirm your name and reference.",f"早晨，呢度係{org_yu}。你係問{iy}，係咪呀？我開{ty}紀錄前，先對返你個名同編號。"),
       ("C",f"Yes. With {issue}, I’m worried that {concern_en}. I’d like the {term} question settled before {dead_en}.",f"係呀，{iy}我係{concern_yu}。關於{ty}，我想喺{dead_yu}之前搞清楚喎。"),
       ("P",f"For {term}, {rule_en}. I’ll compare {detail} with the record for {issue}.",f"講到{ty}，{rule_yu}。我會用{dy}對返{iy}嘅紀錄。"),
       ("C",f"My {term} information says {detail}. For {issue}, can you confirm whether that fact is still current?",f"我份{ty}資料寫住{dy}。講返{iy}，呢個細節而家仲啱唔啱呀？"),
       ("P",f"The {issue} record agrees with {detail}. {p_en}",f"{iy}份紀錄同{dy}對得上。{p_yu}"),
       ("C",f"I have {docs} for {issue}. Which parts should I send first? For {term}, do you need originals or readable copies?",f"{iy}嗰邊我有{dcy}。我應該先交邊份呀？講到{ty}，要正本定清楚副本呢？"),
       ("P",f"Send {docs} through {portal_en} for {issue}. Keep the receipt under {term}; the service can ask if anything else is needed.",f"{iy}要經{portal_yu}交{dcy}。用{ty}嗰份參考編號留底；真係欠資料，服務機構會再問。"),
       ("C",f"For {issue}, when should I expect an update? Because {concern_en}, I want to know when the {term} matter needs follow-up.",f"{iy}通常幾時先有消息呢？我係{concern_yu}，所以想知{ty}幾時先需要再跟進呀。"),
       ("P",f"For {issue}, allow about {proc_en}. While {term} is pending, {interim_en}; after that period, follow up on the same reference.",f"{iy}預大約{proc_yu}。等{ty}期間，{interim_yu}；過咗呢段時間，就用原本編號跟進。"),
       ("C",f"If the {issue} outcome still looks wrong, who should I contact first? For {term}, I want the reason before I challenge anything.",f"如果{iy}個結果仲係唔對路，我應該先搵邊個呀？講到{ty}，我想先知原因，先再決定點處理。"),
       ("P",f"For {issue}, get the reason in writing and {review_en}. Keep that dated note with the {term} record.",f"{iy}先攞書面原因，再{review_yu}。有日期嗰份紀錄要同{ty}資料放埋一齊。"),
       ("C",close_en,close_yu),
      ]
    if v==1:
      return [
       ("P",f"Thanks for calling {org_en} about {issue}. Before I reopen the {term} record, confirm your name and reference.",f"多謝你再聯絡{org_yu}跟進{iy}。我重開{ty}紀錄前，先對返你個名同編號。"),
       ("C",f"Today’s {issue} update mentions {term}. Does that change what I should do about {detail}?",f"今日{iy}個更新提到{ty}。咁{dy}會唔會令我下一步有唔同呀？"),
       ("P",f"For {term}, {rule_en}. The current {issue} record still shows {detail}.",f"就{ty}嚟講，{rule_yu}。而家{iy}份紀錄仍然寫住{dy}。"),
       ("C",f"So you mean {detail} still applies to {issue}? I need that clear before {dead_en} because {concern_en}.",f"即係你意思係{dy}對{iy}仲適用，係咪呀？我想喺{dead_yu}之前搞清楚，因為我{concern_yu}。"),
       ("P",f"Yes, {detail} is the current {issue} record. If the {term} information is wrong, use the service process to correct it.",f"係，{iy}而家紀錄係{dy}。如果{ty}資料有錯，就用服務程序更正。"),
       ("C",f"I’ve gathered {docs} for {issue}. Which items should go with the {term} follow-up? Can I send them online?",f"跟進{iy}我已經有{dcy}。{ty}呢次應該先交邊啲呀？可唔可以網上交呢？"),
       ("P",f"For {issue}, send {docs} through {portal_en}. Keep the {term} submission reference so later updates stay on the same record.",f"{iy}經{portal_yu}交{dcy}。記低{ty}嗰個提交編號，之後更新先可以對返同一份紀錄。"),
       ("C",f"While {issue} is being checked, what should I do about {term}? I’m worried that {concern_en} before {dead_en}.",f"{iy}仲核對緊時，{ty}我應該點做先好呢？我{concern_yu}，尤其係{dead_yu}之前喎。"),
       ("P",f"The {issue} guide is about {proc_en}. While the {term} record is open, {interim_en} and watch the official messages.",f"{iy}一般預大約{proc_yu}。{ty}紀錄未完之前，{interim_yu}，亦要留意正式訊息。"),
       ("C",f"If the final {issue} decision is negative, can I ask why before challenging it? I want the {term} reason explained first.",f"如果{iy}最後結果對我不利，我可唔可以先問清楚原因呀？關於{ty}，我想明白咗先再考慮覆核。"),
       ("P",f"Yes. Get the {issue} decision in writing, then {review_en}. Keep the written reason with the {term} record.",f"可以。先攞{iy}嘅書面決定，再{review_yu}。嗰份理由要同{ty}紀錄一齊留低。"),
       ("C",close_en,close_yu),
      ]
    if v==2:
      return [
       ("P",f"I’m following up {issue} with {org_en}. Before checking the {term} status, confirm your name and reference.",f"我係喺{org_yu}跟進{iy}。查{ty}進度前，先對返你個名同編號。"),
       ("C",f"For {issue}, I was told {detail}. I’m worried that {concern_en} while the {term} record is checked.",f"講返{iy}，我收到嘅資料係{dy}。核對{ty}期間，我係{concern_yu}呀。"),
       ("P",f"The {term} point matters because {rule_en}. That rule is what we use for the {issue} record.",f"{ty}重要，因為{rule_yu}。{iy}份紀錄就係按呢個原則去睇。"),
       ("C",f"If {issue} is not sorted before {dead_en}, what happens next? I don’t want the {term} process to create another problem.",f"如果{iy}去到{dead_yu}都未搞掂，之後會點呀？我唔想{ty}個程序又帶出另一個問題。"),
       ("P",f"Don’t guess the {issue} outcome. {p_en}",f"{iy}個結果唔好估住先。{p_yu}"),
       ("C",f"For {issue}, I have {docs}. Should I send those first? If {term} needs more evidence, can you ask me later?",f"{iy}我手頭有{dcy}。呢啲可唔可以先交呀？如果{ty}仲要證明，你哋之後再問我得唔得呢？"),
       ("P",f"Start the {issue} check with {docs} through {portal_en}. If the {term} record lacks something relevant, the officer can ask for it.",f"{iy}先經{portal_yu}交{dcy}開始核對。{ty}紀錄真係欠相關資料，職員會再要求補充。"),
       ("C",f"For {issue}, how do I prove when {docs} were received? Is the {term} reference enough if a deadline is disputed?",f"即係話，{iy}收到{dcy}嗰日，我點樣證明呀？如果之後爭議限期，{ty}個參考編號夠唔夠呢？"),
       ("P",f"Keep the {issue} electronic receipt and allow about {proc_en}. While the {term} check runs, {interim_en}.",f"{iy}要留低電子收據，再預大約{proc_yu}。{ty}仲核對緊時，{interim_yu}。"),
       ("C",f"If {issue} still has no update after that, should I submit again? Or should I ask about the existing {term} reference?",f"如果{iy}過咗嗰段時間都冇更新，我使唔使再交一次呀？定係直接查返現有{ty}編號好啲呢？"),
       ("P",f"Follow up the existing {issue} reference instead of duplicating it. If the {term} outcome is disputed, {review_en}.",f"{iy}應該跟返原本編號，唔好重複提交。之後如果{ty}結果有爭議，就{review_yu}。"),
       ("C",close_en,close_yu),
      ]
    if v==3:
      return [
       ("P",f"You asked {org_en} to explain {issue}. Before we go through the {term} deadline, confirm your name and reference.",f"你之前叫{org_yu}解釋{iy}。講{ty}個限期前，先對返你個名同編號。"),
       ("C",f"For {issue}, I can see {detail}. How does that fact affect the {term} step I need to take now?",f"即係{iy}而家見到{dy}。呢個細節同{ty}下一步點樣扣連呀？"),
       ("P",f"For {term}, {rule_en}. We use that rule when deciding the next {issue} step.",f"就{ty}嚟講，{rule_yu}。決定{iy}下一步，就會用呢個原則。"),
       ("C",f"I need {issue} dealt with before {dead_en}. Otherwise, I’m worried that {concern_en} because of {term}.",f"{iy}我想喺{dead_yu}之前處理呀。唔係嘅話，我怕{ty}搞唔清，仲會{concern_yu}。"),
       ("P",f"For the {issue} deadline, {p_en}",f"趕住處理{iy}個限期，{p_yu}"),
       ("C",f"I have {docs} for {issue}, but one detail differs from an older record. Should I explain that difference with the {term} evidence?",f"{iy}我有{dcy}，不過有一個細節同舊紀錄唔同。交{ty}證明時，我係咪應該一齊解釋呀？"),
       ("P",f"Yes. Send {docs} through {portal_en} for {issue}, and explain the genuine difference. Keep the {term} receipt after submission.",f"係。{iy}經{portal_yu}交{dcy}時，簡單講清楚真實差異。之後保留{ty}嗰份收據。"),
       ("C",f"While {issue} is checked, could {term} cause an extra fee or another consequence? I want to plan before {dead_en}.",f"核對{iy}期間，{ty}會唔會帶來額外費用或者其他後果呀？我想喺{dead_yu}之前預先有準備。"),
       ("P",f"For {issue}, allow about {proc_en}. While {term} is pending, {interim_en}; keep using the same reference for updates.",f"{iy}預大約{proc_yu}。{ty}未完之前，{interim_yu}；有更新就用返同一個編號。"),
       ("C",f"If the written {issue} decision still looks wrong, what is the proper challenge route? I want the {term} dispute recorded clearly.",f"如果{iy}書面決定仲係有問題，我應該用咩程序挑戰呀？{ty}呢個爭議我想留返清楚紀錄。"),
       ("P",f"Keep the {issue} decision and evidence by date, then {review_en}. Put the result with the {term} record.",f"{iy}嘅決定同證明按日期放好，再{review_yu}。最後結果要同{ty}紀錄放埋一齊。"),
       ("C",close_en,close_yu),
      ]
    return [
       ("P",f"Let’s check the {issue} outcome with {org_en}. Before opening the {term} record, confirm your name and reference.",f"我哋而家喺{org_yu}睇{iy}個結果。打開{ty}紀錄前，先對返你個名同編號。"),
       ("C",f"For {issue}, I was previously told {detail}. I’m still worried that {concern_en} while the {term} outcome is reviewed.",f"之前講{iy}時，有人話{dy}。而家覆核{ty}個結果，我仲係{concern_yu}喎。"),
       ("P",f"For {term}, {rule_en}. That is how we read {detail} in the {issue} record.",f"講到{ty}，{rule_yu}。所以{iy}份紀錄會按{dy}去睇。"),
       ("C",f"Is anything missing for {issue}? I’d rather provide it before {dead_en} than find a gap in the {term} record later.",f"{iy}我仲欠唔欠資料呀？我寧願喺{dead_yu}之前補交，都唔想之後先發現{ty}紀錄有缺口。"),
       ("P",f"For the {issue} review, {p_en}",f"覆核{iy}嗰陣，{p_yu}"),
       ("C",f"I have {docs} for {issue}. Can I send them now? For {term}, will the service confirm the submission time?",f"{iy}我已經準備咗{dcy}。而家交得唔得呀？{ty}嗰邊會唔會確認提交時間呢？"),
       ("P",f"Yes. Send {docs} through {portal_en} for {issue}. Keep the electronic receipt with the {term} record and check the files are readable.",f"可以。{iy}經{portal_yu}交{dcy}。電子收據要同{ty}紀錄放埋一齊，亦要睇清楚文件讀唔讀到。"),
       ("C",f"After I send the {issue} documents, when should I follow up? I don’t want the {term} response to be missed.",f"交咗{iy}啲文件之後，我幾時先應該跟進呢？我唔想錯過{ty}嗰邊嘅回覆呀。"),
       ("P",f"For {issue}, allow about {proc_en}. During the {term} review, {interim_en} and check the official contact channel.",f"{iy}預大約{proc_yu}。覆核{ty}期間，{interim_yu}，亦要睇住正式聯絡渠道。"),
       ("C",f"If my contact details change before {issue} is finished, what should I do? I don’t want the {term} notice going to the wrong place.",f"如果{iy}未完之前我聯絡資料有變，應該點做呀？我唔想{ty}個通知去錯地方喎。"),
       ("P",f"Update any {issue} contact change promptly and keep proof. If the final {term} decision is disputed, {review_en}.",f"{iy}嘅聯絡資料有變就快啲更新，仲要留證明。如果最後{ty}決定有爭議，就{review_yu}。"),
       ("C",close_en,close_yu),
    ]


def make_dialogue(ns:dict,s:dict,i:int,v:int)->dict:
    did=f"D{v*100+i+1:03d}"; raw=turns(ns,s,i,v); stages=STAGES[v]
    if len(raw)!=12: raise SystemExit(f"{did}: expected 12 turns")
    segs=[]
    for n,((role,en,yu),stage) in enumerate(zip(raw,stages),1):
        en=en.replace("'","’"); yu=clean_yue(yu)
        if len(en.split())>35: raise SystemExit(f"{did} S{n:02d}: {len(en.split())} words > 35: {en}")
        want="P" if n%2 else "C"
        if role!=want: raise SystemExit(f"{did} S{n:02d}: role {role} != {want}")
        lang="en" if role=="P" else "yue"; src=en if lang=="en" else yu; model=yu if lang=="en" else en
        segs.append({"n":n,"role":role,"source_lang":lang,"source":src,"model":model,"en":en,"yue":yu,"wc":len(en.split()),"stage":stage})
    return {"id":did,"topic":s["topic"],"title":s["title"]+VARIANT_SUFFIX[v],"term":s["term_en"],"term_yue":s["term_yue"],"segments":segs,"total":sum(x["wc"] for x in segs),"maxseg":max(x["wc"] for x in segs),"difficulty":"Medium","logic_version":"coherent-v2","encounter_variant":v}


def build()->list[dict]:
    ns,seeds=load_backbone(); bank=[]
    for v in range(5):
        for i,s in enumerate(seeds): bank.append(make_dialogue(ns,s,i,v))
    if [d["id"] for d in bank]!=[f"D{i:03d}" for i in range(1,501)]: raise SystemExit("ID coverage/order is not D001..D500")
    if sum(len(d["segments"]) for d in bank)!=6000: raise SystemExit("segment coverage is not 6000")
    return bank


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--out",default=str(DEFAULT_OUT)); ap.add_argument("--promote",action="store_true"); args=ap.parse_args()
    bank=build(); out=ROOT/"data/dialogues.json" if args.promote else Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(out),"dialogues":500,"segments":6000,"max_segment_words":max(d["maxseg"] for d in bank),"logic_version":"coherent-v2"},indent=2,ensure_ascii=False)); return 0

if __name__=="__main__": raise SystemExit(main())

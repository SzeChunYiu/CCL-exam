#!/usr/bin/env python3
"""Release-candidate architecture: each long scenario atom is used once.

The v11 diagnostics showed that even good Cantonese becomes synthetic when a
rich fact/evidence phrase is repeated through several turns or through all five
variants of one scenario.  Real service conversation does the opposite: state a
long referent once, then use short anaphora and new information.

V12 therefore assigns the four rich seed atoms to different encounters:

* initial enquiry      -> full issue once
* follow-up            -> full factual detail once
* evidence discrepancy-> full evidence once
* deadline             -> full official/technical term once
* outcome/review       -> no repeated long seed atom; uses short discourse keys

Within each dialogue, no long seed atom is intentionally repeated in client
source.  Later client turns carry fresh generated state (status, date, amount,
missing-item count, wait period, consequence) plus short natural references.
This is grounded expansion from the repo's CCL material, not five paraphrases of
the same script.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_native_500_v10 as base
import build_native_500_v11 as prev

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9+&./'-]*(?:\s+[A-Za-z][A-Za-z0-9+&./'-]*)*")

# Extend the exam-source lexical map before base.load_seeds() parses RAW.
base.REPL.update({
    "BVA": "A類過橋簽證", "BVB": "B類過橋簽證", "BVC": "C類過橋簽證",
    "CCS": "托兒津貼", "FWO": "公平工作監察機構", "USI": "唯一學生識別碼",
    "TAFE": "技術及持續教育學院", "OSHC": "海外學生醫療保險",
    "HECS-HELP": "高等教育貸款計劃", "FEE-HELP": "高等教育學費貸款",
    "NBN": "全國寬頻網絡", "NSW": "新州", "VIC": "維州", "QLD": "昆州",
})

STAGE_Y = ["第一次問", "再跟進", "補文件", "趕限期", "睇結果"]
STAGE_E = ["initial enquiry", "follow-up", "document check", "deadline check", "outcome review"]

MONTHS_Y = ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]
MONTHS_E = ["January","February","March","April","May","June","July","August","September","October","November","December"]
DIGITS = "零一二三四五六七八九"

STATUS = {
    "Business": [("仲等緊登記", "registration is still pending"),("資料顯示已收", "the material shows as received"),("個地址未改", "the address has not been updated"),("個名稱要再查", "the business name needs another check")],
    "Consumer affairs": [("投訴仲處理緊", "the complaint is still being handled"),("退款未入帳", "the refund has not arrived"),("維修紀錄未齊", "the repair record is incomplete"),("商戶仲未覆", "the trader has not replied")],
    "Employment": [("糧務紀錄未改", "the payroll record has not changed"),("僱主仲未覆", "the employer has not replied"),("更表仲係舊版", "the roster is still the old version"),("假期紀錄未入", "the leave record has not been entered")],
    "Health": [("預約仲未確定", "the appointment is not yet confirmed"),("轉介仲處理緊", "the referral is still being processed"),("收費紀錄未改", "the fee record has not changed"),("報告仲未到", "the report has not arrived")],
    "Immigration and settlement": [("申請仲處理緊", "the application is still being processed"),("身份資料未改", "the identity details have not changed"),("文件顯示已收", "the document shows as received"),("簽證紀錄未更新", "the visa record has not changed yet")],
    "Legal": [("個案仲排緊期", "the matter is still awaiting a date"),("通知仲未送達", "the notice has not been served"),("書面回覆未到", "the written response has not arrived"),("紀錄仲未更正", "the record has not been corrected")],
    "Community": [("預約仲未確認", "the booking is not yet confirmed"),("地址紀錄未改", "the address record has not changed"),("收集安排未定", "the collection arrangement is not set"),("申請仲等批", "the request is still awaiting approval")],
    "Education": [("入學紀錄未改", "the enrolment record has not changed"),("課堂仲未確認", "the class is not confirmed"),("學費紀錄未入", "the fee record has not been entered"),("學生資料未齊", "the student record is incomplete")],
    "Financial": [("交易仲處理緊", "the transaction is still pending"),("戶口紀錄未改", "the account record has not changed"),("款項仲未入", "the payment has not arrived"),("月結單未反映", "the statement does not show it yet")],
    "Housing": [("維修仲未安排", "the repair has not been arranged"),("租務紀錄未改", "the tenancy record has not changed"),("通知仲未確認", "the notice is not yet confirmed"),("按金紀錄未入", "the bond record has not been entered")],
    "Insurance": [("索償仲處理緊", "the claim is still being processed"),("評估報告未到", "the assessment report has not arrived"),("保單紀錄未改", "the policy record has not changed"),("賠款仲未批", "the payment is not yet approved")],
    "Social services": [("支援申請未批", "the support request is not yet approved"),("付款紀錄未改", "the payment record has not changed"),("收入資料未入", "the income information is not entered"),("個案仲等緊覆", "the case is still awaiting a response")],
}

DOC_STATE_Y = ["仲欠一份", "有一份模糊", "日期對唔上", "地址唔一致", "個數唔相同", "少咗簽名", "舊版仲喺度", "新嗰份未入"]
DOC_STATE_E = ["one item is still missing", "one copy is unclear", "the dates do not match", "the addresses differ", "the figures do not match", "a signature is missing", "the old version is still on file", "the new copy is not recorded"]

SHORTS = ["係呀。","明喇。","咁點算？","我知喇。","唔該。","好呀。","等陣先。","係咩？","原來咁。","咁就好。","我記低。","得呀。","我驚搞錯。","你講吓。","咁我明。","我聽住。","係喎。","好彩啫。"]
PARTS = [("呀",20),("喇",17),("呢",13),("㗎",12),("喎",8),("啫",7),("嘛",5),("囉",4),("嘞",4),("添",3),("啩",3),("咩",2),("吖",2)]
QPARTS = [("呀",24),("呢",18),("㗎",14),("咩",10),("吖",8),("啩",6),("喎",5),("嘛",5),("啫",4),("囉",3),("喇",3)]
CONNECTIVES = ["其實","咁","不過","所以","跟住","即係","但係","原來","仲有","反而"]

SPOKEN_REPL = [
    ("收入申報", "報收入"),("申報期", "報資料嗰期"),("申報資料", "所報資料"),("申報變更", "報返變更"),("申報", "報返"),
    ("憂心", "擔心"),("狀況", "情況"),("確保", "睇清楚"),("實體店舖", "門市"),("實體店", "門市"),("實體", "實際"),
    ("予以", "畀"),("加以", "再"),("方可", "先可以"),("應當", "應該"),("事宜", "安排"),
    ("我唔肯定", "我唔係好知"),("處理好", "搞掂"),("下一步", "跟住點做"),("更新", "改返"),("細節", "資料"),("確認", "對清"),
    ("相關英文項目類過橋簽證", "A類過橋簽證"),("托兒津貼即係相關英文項目", "托兒津貼"),
]


def h(*parts): return base.h(*parts)

def pick(seed, variant, key, vals): return vals[h(seed["title"],variant,key)%len(vals)]

def zh_int(n:int)->str:
    if n<10: return DIGITS[n]
    if n<20: return "十"+(DIGITS[n%10] if n%10 else "")
    if n<100: return DIGITS[n//10]+"十"+(DIGITS[n%10] if n%10 else "")
    q,r=divmod(n,100); return DIGITS[q]+"百"+(zh_int(r) if r else "")

def clean(text:str)->str:
    out=base.tidy_yue(text)
    for a,z in SPOKEN_REPL: out=out.replace(a,z)
    out=out.replace("即係，","即係").replace("，，","，")
    return out

def clean_seed(seed):
    s=dict(seed)
    for k in ("issue_yue","term_yue","fact_yue","evidence_yue"): s[k]=clean(s[k])
    return s

def key(text:str, width:int=7)->str:
    s=clean(text).strip("。！？ ，；（）()")
    # Prefer the last semantic phrase after connective punctuation.
    for sep in ("，","；","即係","、"):
        if sep in s:
            parts=[p.strip() for p in s.split(sep) if p.strip()]
            if parts: s=parts[-1]
    hs=HAN.findall(s)
    if len(hs)<=width: return "".join(hs)
    return "".join(hs[-width:])

def weighted(items,value):
    n=value%sum(w for _,w in items); a=0
    for item,w in items:
        a+=w
        if n<a:return item
    return items[-1][0]

def particle(sentence,seed,variant,k,rate=61):
    s=clean(sentence); punct="？" if s.endswith("？") else "。"; body=s.rstrip("。！？")
    pchars=set("呀喇呢㗎喎啫嘛囉嘞添啩咩吖")
    if body and body[-1] not in pchars and h(seed["title"],variant,k,"on")%100<rate:
        body+=weighted(QPARTS if punct=="？" else PARTS,h(seed["title"],variant,k,"p"))
    return body+punct

def maybe_conn(sentence,seed,variant,k):
    if h(seed["title"],variant,k,"c")%100<45:
        return pick(seed,variant,k+"-c",CONNECTIVES)+"，"+sentence
    return sentence

def short(seed,variant,k): return pick(seed,variant,k,SHORTS)

def ctx(seed,idx,variant):
    m=(idx*5+variant*3)%12; d1=2+((idx*7+variant*5)%25); d2=2+((d1+4+variant*2)%25)
    amount=140+((idx*173+variant*419)%9300); wait=3+((idx+variant*2)%8); count=2+((idx*3+variant)%6)
    st=STATUS.get(seed["topic"],[("紀錄仲處理緊","the record is still being processed")])
    sy,se=st[h(seed["title"],variant,"status")%len(st)]
    j=h(seed["title"],variant,"docstate")%len(DOC_STATE_Y)
    return {
      "date1_y":f"{MONTHS_Y[m]}{zh_int(d1)}號","date1_e":f"{d1} {MONTHS_E[m]}",
      "date2_y":f"{MONTHS_Y[m]}{zh_int(d2)}號","date2_e":f"{d2} {MONTHS_E[m]}",
      "amount_y":f"{zh_int(amount)}蚊","amount_e":f"${amount:,}",
      "wait_y":f"{zh_int(wait)}個工作日","wait_e":f"{wait} business days",
      "count_y":f"{zh_int(count)}份","count_e":f"{count} documents",
      "status_y":sy,"status_e":se,"docstate_y":DOC_STATE_Y[j],"docstate_e":DOC_STATE_E[j],
    }

def effect(seed): return prev.SHORT_EFFECT.get(seed["topic"],("the current arrangements","而家安排"))


def medium(seed,idx,variant,action):
    c=ctx(seed,idx,variant); ik=key(seed["issue_yue"]); tk=key(seed["term_yue"]); ek=key(seed["evidence_yue"])
    eff_e,eff_y=effect(seed)
    # Each encounter owns one full long seed atom; all other references are short.
    if variant==0:
        if action==0:
            y=f"{seed['issue_yue']}，我想問{tk}應該點搞？"; e=f"I am calling about {seed['issue_en']}; how should I deal with {seed['term_en']} in this situation?"
        elif action==1:
            y=f"{c['date1_y']}{ik}{c['status_y']}，我今日先見到。"; e=f"On {c['date1_e']}, the {ik} record showed that {c['status_e']}; I only noticed it today."
        elif action==2:
            y=f"{ek}我手頭有{c['count_y']}，其中{c['docstate_y']}。"; e=f"I have {c['count_e']} relating to the evidence, but {c['docstate_e']}."
        else:
            y=f"{ik}未清楚，{eff_y}去到{c['date2_y']}會唔會受影響？"; e=f"If this issue is still unclear by {c['date2_e']}, could it affect {eff_e}?"
    elif variant==1:
        if action==0:
            y=f"我上次漏咗一樣：{seed['fact_yue']}。"; e=f"I left out one detail last time: {seed['fact_en']}."
        elif action==1:
            y=f"{c['date1_y']}再查{tk}，而家{c['status_y']}。"; e=f"I checked {seed['term_en']} again on {c['date1_e']}; now {c['status_e']}."
        elif action==2:
            y=f"{ek}{c['date2_y']}先收到，我想知可唔可以補落舊紀錄。"; e=f"I did not receive the evidence until {c['date2_e']}; can I add it to the existing record?"
        else:
            y=f"再等{c['wait_y']}先問{tk}，會唔會太遲？"; e=f"Would waiting another {c['wait_e']} before following up on {seed['term_en']} be too late?"
    elif variant==2:
        if action==0:
            y=f"我而家對緊{seed['evidence_yue']}，但{c['docstate_y']}。"; e=f"I am checking {seed['evidence_en']}, but {c['docstate_e']}."
        elif action==1:
            y=f"{c['amount_y']}嗰個數同{ik}紀錄唔同，我唔敢自己改。"; e=f"The {c['amount_e']} figure does not match the record for this issue, so I do not want to change it myself."
        elif action==2:
            y=f"{tk}如果跟新嗰份，舊嗰份要唔要一齊留低？"; e=f"If {seed['term_en']} follows the newer document, should I keep the older one as well?"
        else:
            y=f"{ek}未對清之前，{eff_y}可唔可以照舊？"; e=f"Until the evidence discrepancy is resolved, can {eff_e} remain unchanged?"
    elif variant==3:
        if action==0:
            y=f"我想趕喺{c['date2_y']}前搞掂{seed['term_yue']}。"; e=f"I want to sort out {seed['term_en']} before {c['date2_e']}."
        elif action==1:
            y=f"{ik}由{c['date1_y']}開始計，我驚自己記錯日子。"; e=f"The timing for this issue starts from {c['date1_e']}, and I am worried I have remembered the date incorrectly."
        elif action==2:
            y=f"{ek}仲有{c['count_y']}要整理，限期前係咪一定要齊？"; e=f"I still have {c['count_e']} of the evidence to organise; must everything be ready before the deadline?"
        else:
            y=f"萬一遲過{c['date2_y']}先補到，{eff_y}會點？"; e=f"If I can only add the material after {c['date2_e']}, what could happen to {eff_e}?"
    else:
        if action==0:
            y=f"{ik}個結果寫住{c['amount_y']}，我想知點解係呢個數。"; e=f"The outcome for this issue shows {c['amount_e']}; I want to know why that figure was used."
        elif action==1:
            y=f"{ek}{c['docstate_y']}，我想知個決定有冇睇到呢點。"; e=f"The evidence has a problem because {c['docstate_e']}; I want to know whether the decision considered that point."
        elif action==2:
            y=f"{tk}如果維持原決定，我可唔可以先攞書面理由？"; e=f"If the original decision on {seed['term_en']} remains, can I first ask for the reasons in writing?"
        else:
            y=f"未決定覆核住，我想知{eff_y}跟住要點安排。"; e=f"Before deciding whether to seek review, I want to know what happens next with {eff_e}."
    y=particle(maybe_conn(y,seed,variant,f"m{action}"),seed,variant,f"m{action}",60)
    return base.tidy_en(e),clean(y)


def repair(seed,idx,variant):
    c=ctx(seed,idx,variant); ik=key(seed["issue_yue"]); tk=key(seed["term_yue"]); ek=key(seed["evidence_yue"])
    if variant==0:
        y=f"等陣，{c['date1_y']}先係我見到{ik}嗰日。"; e=f"Wait, {c['date1_e']} was the day I first noticed the issue."
    elif variant==1:
        y=f"唔係{c['date1_y']}，我收到{ek}其實係{c['date2_y']}。"; e=f"It was not {c['date1_e']}; I actually received the evidence on {c['date2_e']}."
    elif variant==2:
        y=f"唔係講新嗰份，我頭先係指{ek}舊紀錄。"; e=f"I was not referring to the new document; I meant the older evidence record."
    elif variant==3:
        y=f"我講反咗，{tk}個限期係{c['date2_y']}先啱。"; e=f"I reversed the dates; the deadline for {seed['term_en']} is {c['date2_e']}."
    else:
        y=f"我更正返，今次係問{tk}個決定，唔係重開一宗。"; e=f"Let me correct that: I am asking about the decision on {seed['term_en']}, not opening a new matter."
    return base.tidy_en(e),particle(y,seed,variant,"repair",58)+short(seed,variant,"repair-short")+f"{ik}我記住。"


def professional(seed,idx,variant,action):
    # Reuse v11's already state+seed-specific professional source/model, but clean
    # lexical placeholders with the enhanced map before output.
    seed2=clean_seed(seed); en,y=prev.professional_turn(seed2,variant,action)
    return en,clean(y)

LAYOUTS=prev.LAYOUTS

def addseg(segs,n,role,en,y):
    en=base.tidy_en(en); y=clean(y); w=len(en.split())
    if w>35: raise SystemExit(f"segment >35 words: {w} {en}")
    lang="en" if role=="P" else "yue"
    segs.append({"n":n,"role":role,"source_lang":lang,"wc":w,"en":en,"yue":y,"source":en if lang=="en" else y,"model":y if lang=="en" else en})

def make_dialogue(seed,idx,variant):
    seed=clean_seed(seed); layout=LAYOUTS[h(seed["title"],variant,"layout-v12")%len(LAYOUTS)]; segs=[]
    for n,(role,action) in enumerate(layout,1):
        if role=="P": en,y=professional(seed,idx,variant,action)
        elif action==4: en,y=repair(seed,idx,variant)
        elif action==5:
            y=pick(seed,variant,"close-y",["明喇。","好，唔該。","得，我記住。","咁就好。","我知喇。","好呀。","清楚喇。","得喇。"])
            en=pick(seed,variant,"close-e",["Okay, I understand.","All right, thank you.","I will remember that.","That is clear now.","Okay, I know what to do.","Good, thank you.","That makes sense.","All right."])
        else:
            en,y=medium(seed,idx,variant,action); y+=short(seed,variant,f"s{action}")
        addseg(segs,n,role,en,y)
    did=f"D{variant*100+idx:03d}"; stage=base.STAGES[variant][0]
    return {"id":did,"topic":seed["topic"],"title":seed["title"] if variant==0 else f"{seed['title']} — {stage}","term":seed["term_en"],"term_yue":seed["term_yue"],"segments":segs,"total":sum(s["wc"] for s in segs),"maxseg":max(s["wc"] for s in segs),"difficulty":["Medium","Medium","Hard","Hard","Hard"][variant]}

def meaningful(text): return [p.strip() for p in re.split(r"[。！？]",text) if len(HAN.findall(p.strip()))>=6]
def validate(ds):
    errs=[]; seen={}
    if len(ds)!=500:errs.append(f"dialogues={len(ds)}")
    for d in ds:
        if len(d["segments"])!=12:errs.append(f"{d['id']}: segment count")
        if d["maxseg"]>35:errs.append(f"{d['id']}: maxseg={d['maxseg']}")
        for s in d["segments"]:
            if s["source_lang"]=="yue" and LATIN.search(s["source"]):errs.append(f"{d['id']} S{s['n']}: Latin")
            for p in meaningful(s["yue"]):
                if p in seen and seen[p]!=d["id"]:errs.append(f"exact {seen[p]}/{d['id']}: {p}")
                seen[p]=d["id"]
    return errs

def main():
    seeds=base.load_seeds(); ds=[make_dialogue(seed,i,v) for v in range(5) for i,seed in enumerate(seeds,1)]
    errs=validate(ds); BANK.write_text(json.dumps(ds,ensure_ascii=False,indent=1)+"\n",encoding="utf-8"); base.write_support(ds)
    print(json.dumps({"dialogues":500,"segments":sum(len(d['segments']) for d in ds),"mean_words":round(sum(d['total'] for d in ds)/500,1),"min_words":min(d['total'] for d in ds),"max_words":max(d['total'] for d in ds),"max_segment":max(d['maxseg'] for d in ds),"local_errors":errs[:100]},ensure_ascii=False,indent=2))
    return 1 if errs else 0
if __name__=="__main__": raise SystemExit(main())

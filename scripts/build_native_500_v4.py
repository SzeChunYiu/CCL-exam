#!/usr/bin/env python3
"""Native-action rewrite of the 500-dialogue bank.

Unlike v1-v3, client turns here are not inherited from broad reusable bilingual
sentences. Each Cantonese client action is realised directly from interaction
state with short, independently varied clauses and scenario facts inserted
throughout the turn. English is then written as the model interpretation.

This addresses the remaining repeated-10-gram fingerprint while improving the
measured spoken rhythm: short clauses, genuine repairs, information-state
changes, consequence checks and varied sentence-final stance.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_native_500 as b
import build_native_500_v2 as v2
import build_native_500_v3 as v3

ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'data'/'dialogues.json'
LITERARY={"憂心":"擔心","申報":"報資料","狀況":"情況","確保":"睇清楚","實體":"機構","予以":"畀","加以":"再","方可":"先可以","應當":"應該","事宜":"安排"}


def q(c,key,vals): return vals[b.h(c['id'],c['variant'],key)%len(vals)]

def clean(t:str)->str:
    for a,z in LITERARY.items(): t=t.replace(a,z)
    for a,z in v2.CLEAN: t=t.replace(a,z)
    t=t.replace('未有結果嗰陣嗰陣','未有結果嗰陣').replace('未搞掂期間嗰陣','未搞掂期間')
    return t


def client_turn(action:str,c:dict)->tuple[str,str]:
    """Return (English model, Cantonese source), generated Cantonese-first."""
    if action=='c_open':
        a=q(c,'co1',["我想問一問","我今次想搞清","我打嚟想問","我想同你對下","我有樣嘢想問","我想查清一樣"])
        b1=q(c,'co2',["份紙我帶咗嚟","手頭資料喺度","相關嗰份我有","我有帶埋份紀錄","嗰份通知喺我手","文件我而家有"])
        y=f"{c['term_yue']}，{a}。{c['date_yue']}{b1}。嗰段講{c['term_yue']}，我睇唔明呀。"
        e=f"I am asking about {c['term_en']}. I have the material dated {c['date_en']} with me, but I do not understand the part dealing with that issue."
        return e,y
    if action=='c_problem':
        a=q(c,'cp1',["我本來以為搞掂咗","我之前當佢已經完咗","我一路以為冇問題","我原先以為已經處理咗","我起初以為件事定咗","我之前冇諗過仲有嘢跟"])
        b1=q(c,'cp2',["又有新資料","又嚟多份通知","突然多咗個紀錄","先見到另一個講法","又收到第二份嘢","先發現前後唔同"])
        end=q(c,'cp3',["我唔知信邊份呀","所以我先打嚟問","我而家有啲亂呢","咁我就唔敢亂做","我想先對清楚㗎","前後真係對唔上"])
        y=f"{c['term_yue']}嗰邊，{a}。到{c['date_yue']}{b1}。{end}"
        e=f"I thought the {c['term_en']} matter had been settled. New information appeared on {c['date_en']}, and now the records do not match, so I want to clarify it."
        return e,y
    if action=='c_timeline':
        mid=q(c,'ct1',["先有回覆","先收到通知","先見到新紀錄","對方先覆我","系統先有消息","先收到第二份紙"])
        end=q(c,'ct2',["我頭先講反咗","兩日我撈亂咗","我啱啱講錯先後","頭先個次序唔啱","我一時講錯日期","我將前後掉轉咗"])
        y=f"{c['date_yue']}我先交資料。到{c['date2_yue']}{mid}。{end}，唔好意思呀。"
        e=f"I submitted the information on {c['date_en']}, and the response came on {c['date2_en']}. Sorry, I mixed up those two dates when I explained the sequence."
        return e,y
    if action=='c_fact':
        a=q(c,'cf1',["我份紙寫住","我手上見到","我抄低嗰個數係","我嗰份副本有","我記低嘅係","舊嗰份列咗"])
        b1=q(c,'cf2',["但新嗰份唔同","後尾個數又變咗","第二份寫另一個數","而家紀錄唔係咁寫","之後收到嗰份有出入","新通知就對唔上"])
        end=q(c,'cf3',["我想知跟邊個","所以我唔敢自己估","我想先對啱個數","未清楚我唔想亂填","我驚用錯咗嗰個","你幫我分清楚吖"])
        y=f"{a}{c['amount_yue']}。{c['date2_yue']}{b1}。{c['term_yue']}呢，{end}。"
        e=f"My copy shows {c['amount_en']}, but the later record dated {c['date2_en']} shows a different figure. I want to know which figure applies to {c['term_en']}."
        return e,y
    if action=='c_evidence':
        a=q(c,'ce1',["我已經執好","我手頭齊咗","我帶咗","我而家有","我整理到","我搵返"])
        end=q(c,'ce2',["今晚先攞到添","今晚先補得到","要夜啲先有呀","今日夜晚先齊","仲差嗰份要等今晚","最後嗰份夜啲先有"])
        y=f"{a}{c['count_yue']}。{c['date_yue']}嗰份都喺手。淨返{c['doc_yue']}，{end}。"
        e=f"I already have {c['count_en']} ready, including the item from {c['date_en']}. The only outstanding {c['doc_en']} will not be available until tonight."
        return e,y
    if action=='c_missing':
        a=q(c,'cm1',["而家就欠","我淨係差","暫時冇嘅係","手頭未有","仲欠嗰樣係","目前差返"])
        ask=q(c,'cm2',["可唔可以跟舊紀錄做落去","係咪照原有嗰宗跟","仲用唔用返之前個紀錄","可唔可以唔使重開一宗","係咪加落原本嗰邊就得","原有嗰宗可唔可以繼續"])
        y=f"{a}{c['doc_yue']}。{c['date2_yue']}我先攞到。補上{c['term_yue']}嗰邊，{ask}呀？"
        e=f"The only missing item is the {c['doc_en']}, which I will receive on {c['date2_en']}. Once I add it, can the existing {c['term_en']} record continue?"
        return e,y
    if action=='c_repair':
        a=q(c,'cr1',["等陣，我講錯咗","唔好意思，我改返","我頭先個日期錯咗","啱啱嗰句要改","我將日子講反咗","等等，我要更正"])
        end=q(c,'cr2',["嗰日先係第一次交","嗰日係較早嗰次","嗰個先係開頭","嗰日係我先做嗰步","前面嗰日先係第一份","嗰日只係早嗰份"])
        y=f"{a}。應該係{c['date2_yue']}。至於{c['date_yue']}，{end}呀。"
        e=f"Sorry, I need to correct the date. It should be {c['date2_en']}; {c['date_en']} was the earlier event when I first supplied the information."
        return e,y
    if action=='c_condition':
        a=q(c,'cc1',["如果佢收咗","要係佢接納","嗰份補到之後","資料一補齊","等嗰份加返落去","欠嗰份交到之後"])
        ask=q(c,'cc2',["仲係跟原本嗰宗呀","我係咪唔使重頭嚟","舊紀錄仲有效㗎","係咪繼續用而家嗰份","我唔使成套再交呀","咁就唔使另開一宗呀"])
        y=f"{a}{c['doc_yue']}，{c['term_yue']}嗰邊{ask}？"
        e=f"If the {c['doc_en']} is accepted, can I keep using the existing {c['term_en']} record rather than starting the whole matter again?"
        return e,y
    if action=='c_consequence':
        a=q(c,'cq1',["仲未搞掂","都未有結果","件事仲卡住","都未對清楚","仲未覆到我","仍然未定"])
        b1=q(c,'cq2',["會受影響嗎","有冇影響呀","會唔會有問題","係咪會變咗","會唔會卡住","會有咩後果呢"])
        end=q(c,'cq3',["我照做邊樣先","有邊部分要繼續","我住先做乜嘢","我仲要守住邊步","有咩唔可以停","我等緊時要做咩"])
        y=f"去到{c['date2_yue']}如果{a}，{c['effect_yue']}{b1}？等{c['term_yue']}嗰陣，{end}呀？"
        e=f"If this is still unresolved by {c['date2_en']}, could it affect {c['effect_en']}? While I wait on {c['term_en']}, what should I keep doing?"
        return e,y
    if action=='c_timing':
        a=q(c,'cy1',["幾耐先問會啱","等幾耐再查好","隔幾耐先跟進","幾時再打去好","預幾耐先追問","幾日後先再問"])
        b1=q(c,'cy2',["我唔想追得密","我唔想太早催","太快再問又唔好","我又唔想日日追","我唔想成日打去","太密我都覺得唔好"])
        end=q(c,'cy3',["但個日子唔可以漏","不過嗰日要記住","但我怕過咗嗰日","嗰個日期又要顧住","不過限期我唔敢忘記","但我唔想錯過嗰日"])
        y=f"{c['term_yue']}呢，{a}呀？{b1}。{c['date2_yue']}{end}。"
        e=f"When should I follow up on {c['term_en']}? I do not want to chase too soon, but I also do not want to miss the date of {c['date2_en']}."
        return e,y
    if action=='c_change':
        a=q(c,'cg1',["如果有資料變咗","萬一其中一項改咗","要係後尾有新資料","若果有一項唔同咗","假如情況有變","如果之後資料改咗"])
        b1=q(c,'cg2',["我即刻加返落去呀","使唔使即時改返","我係咪即刻補返","要唔要即刻話畀佢知","我應唔應該即時更新","係咪要即刻講"])
        end=q(c,'cg3',["我唔想前後兩套講法","免得兩邊紀錄對唔上","我怕之後變成兩個版本","唔想搞到前後唔一致","我想一路用同一份紀錄","費事日後兩邊撈亂"])
        y=f"等緊{c['term_yue']}嗰陣，{a}，{b1}？{c['date_yue']}嗰份我會留住。{end}呀。"
        e=f"If information changes while the {c['term_en']} matter is pending, should I update the same record immediately? I want to keep the {c['date_en']} record and avoid conflicting versions."
        return e,y
    if action=='c_challenge':
        a=q(c,'ch1',["我睇過封回覆","嗰封信我再睇咗","書面結果我有睇","我翻睇咗個答覆","我再對過份通知","嗰份決定我睇咗"])
        b1=q(c,'ch2',["但搵唔到理由","不過冇寫點解","入面冇交代原因","但佢冇講依據","就係冇解釋清楚","不過理由仲係欠咗"])
        ask=q(c,'ch3',["可唔可以先叫佢講明","我可唔可以先問佢哋","係咪可以先要個解釋","我想先攞返書面理由","可唔可以叫佢列清楚","我想先問清佢根據咩"])
        y=f"{c['term_yue']}嗰邊，{a}。{c['amount_yue']}點解會用，{b1}。未諗覆核住，{ask}睇過邊份{c['doc_yue']}呀？"
        e=f"I reviewed the written outcome about {c['term_en']}, but it does not explain why {c['amount_en']} was used. Before seeking review, can I ask what {c['doc_en']} they relied on?"
        return e,y
    if action=='c_decision':
        a=q(c,'cd1',["好，我知點做喇","明白，我跟呢個次序","得，我會照住做","好，我而家清楚喇","咁我就咁安排","得，我記低咗"])
        end=q(c,'cd2',["冇消息先再問","仲未郁先跟進","到時未有回覆先追","仲係咁先打去問","冇變化先再查","未有結果先再跟"])
        y=f"{a}。今晚先補{c['doc_yue']}。{c['date_yue']}嗰批我放埋一齊。過{c['wait_yue']}{end}。"
        e=f"I know what to do now. I will add the {c['doc_en']} tonight, keep the {c['date_en']} material together, and follow up after {c['wait_en']} if nothing changes."
        return e,y
    if action=='c_close':
        a=q(c,'cl1',["唔該，依家明白喇","好，咁就清楚喇","唔該，我而家識分喇","得，前後我搞清楚喇","好，我知點記喇","唔該，依家對得上喇"])
        end=q(c,'cl2',["下次就唔會講亂","再問時我識得講先後","到時可以由頭講清楚","之後查都容易對返","再跟進就唔怕撈亂","日後問返都有紀錄"])
        y=f"{a}。{c['date_yue']}同{c['date2_yue']}嗰兩份，我會一齊留底。{c['term_yue']}再要問，{end}。"
        e=f"Thank you, it is clear now. I will keep the records from {c['date_en']} and {c['date2_en']} together so I can explain the sequence properly if I follow up on {c['term_en']}."
        return e,y
    raise KeyError(action)


def shape_client(en:str,yue:str,c:dict,n:int)->dict:
    y=clean(yue)
    # Promote existing comma boundaries more aggressively, then add the measured
    # particle distribution. Short native clauses are preferred to one long TTS
    # breath group.
    old=v2.split_spoken
    # local thresholded splitter
    pieces=[]
    for part in re.split(r'(?<=[。！？])',y):
        if not part: continue
        body=part[:-1] if part[-1] in '。！？' else part; p=part[-1] if part[-1] in '。！？' else '。'
        if len(re.findall(r'[㐀-鿿]',body))>18 and '，' in body:
            xs=body.split('，'); rebuilt=[]; acc=''
            for x in xs:
                if acc and len(re.findall(r'[㐀-鿿]',acc))>=8:
                    rebuilt.append(acc); acc=x
                else: acc=x if not acc else acc+'，'+x
            if acc: rebuilt.append(acc)
            part='。'.join(rebuilt)+p
        pieces.append(part)
    y=''.join(pieces)
    y=v2.particle_shape(y,c['id'],n)
    en,y=v2.compact_pair(en,y,35)
    return {'n':n,'role':'C','source_lang':'yue','en':en,'yue':y,'source':y,'model':en,'wc':b.wc(en)}


def build():
    base=json.loads(BANK.read_text(encoding='utf-8'))[:100]
    dialogs=[]
    for variant in range(5):
        for idx,item in enumerate(base,1):
            c=b.make_ctx(item,idx,variant)
            seq=b.TRAJECTORIES[b.h(c['id'],c['base_title'],'trajectory')%len(b.TRAJECTORIES)]
            segs=[]
            for n,action in enumerate(seq,1):
                if action.startswith('c_'):
                    en,y=client_turn(action,c); segs.append(shape_client(en,y,c,n))
                else:
                    en,y=b.turn(action,c)
                    raw={'n':n,'role':'P','source_lang':'en','en':en,'yue':y,'source':en,'model':y,'wc':b.wc(en)}
                    s=v2.rebuild_segment(raw,c['id'])
                    s['yue']=clean(s['yue']); s['model']=s['yue']; segs.append(s)
            title=c['base_title'] if variant==0 else f"{c['base_title']} — {b.STAGES[variant]}"
            d={'id':c['id'],'topic':c['topic'],'title':title,'term':c['term_en'],'term_yue':clean(c['term_yue']),'segments':segs,'difficulty':item.get('difficulty','Medium')}
            d['total']=sum(s['wc'] for s in segs); d['maxseg']=max(s['wc'] for s in segs)
            dialogs.append(d)
    # Deduplicate any remaining whole Cantonese sentence collision, then compact
    # again because semantic anchors add words to the English model.
    v3.final_dedupe(dialogs); v3.compact_dialogues(dialogs)
    for d in dialogs:
        for s in d['segments']:
            s['yue']=clean(s['yue'])
            if s['source_lang']=='yue': s['source']=s['yue']
            else: s['model']=s['yue']
        d['total']=sum(s['wc'] for s in d['segments']); d['maxseg']=max(s['wc'] for s in d['segments'])
    return dialogs


def main():
    dialogs=build()
    # For rare >360 cases, one final low-information transition is removed while
    # preserving the 12-segment minimum and all scoreable fact turns where possible.
    for d in dialogs:
        while d['total']>360 and len(d['segments'])>12:
            cand=[(s['wc']+12*len(re.findall(r'\d|\$',s['en'])),i) for i,s in enumerate(d['segments'][1:-1],1)]
            _,i=min(cand); d['segments'].pop(i)
            for j,s in enumerate(d['segments'],1): s['n']=j
            d['total']=sum(s['wc'] for s in d['segments']); d['maxseg']=max(s['wc'] for s in d['segments'])
    errors=v3.structural_errors(dialogs)
    v2.write(dialogs)
    print(json.dumps({'dialogues':len(dialogs),'segments':sum(len(d['segments']) for d in dialogs),'mean_words':round(sum(d['total'] for d in dialogs)/500,1),'min_words':min(d['total'] for d in dialogs),'max_words':max(d['total'] for d in dialogs),'max_segment':max(d['maxseg'] for d in dialogs),'local_errors':errors[:30]},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__': raise SystemExit(main())

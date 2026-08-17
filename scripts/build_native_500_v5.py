#!/usr/bin/env python3
"""Discourse-reference and rhythm pass for the action-native 500 bank.

Natural conversation does not repeat a long institutional name or document
bundle in every turn. V5 keeps the full scoreable Cantonese term at first client
mention, then uses context-appropriate short references. It also shortens the
few remaining action phrases whose fixed wording was >=10 Han characters.
"""
from __future__ import annotations
import json,re
from pathlib import Path
import build_native_500 as b
import build_native_500_v2 as v2
import build_native_500_v3 as v3
import build_native_500_v4 as v4

ROOT=Path(__file__).resolve().parents[1]
H=re.compile(r'[㐀-鿿]')
REFS=['呢宗嘢','嗰邊','呢個安排','呢件事','而家嗰宗','頭先講嗰樣','手上呢宗','嗰個問題']
DOCS={
 '更表糧單或者書面申請':['更表同糧單','僱傭文件','相關嗰份證明','手頭工作文件'],
 '轉介信預約或者醫療文件':['轉介同預約資料','醫療文件','相關醫療證明','手頭嗰份醫療紙'],
 '租約通知或者維修紀錄':['租約同維修資料','租務文件','相關維修紀錄','手頭租務證明'],
 '通知陳述書或者法院文件':['法院文件','通知同陳述書','相關法律文件','手頭法院資料'],
 '索償發票或者評估文件':['索償同發票資料','保險文件','相關評估資料','手頭索償證明'],
 '身份收入或者證明文件':['身份同收入資料','支援證明文件','相關收入證明','手頭身份文件'],
 '地址或者預約文件':['地址同預約資料','社區服務文件','相關預約證明','手頭地址資料'],
 '入學或者修讀文件':['入學文件','修讀資料','相關學校證明','手頭學生文件'],
 '月結單或者付款紀錄':['月結單同付款紀錄','金融文件','相關付款證明','手頭交易資料'],
 '理賠發票或者評估文件':['索償同發票資料','保險文件','相關評估資料','手頭索償證明'],
}
PHRASES={
 '之後收到嗰份有出入':['嗰份對唔上','新嗰份有出入','後尾寫法唔同','新資料唔一致','嗰個數唔同'],
 '咁就唔使另開一宗呀':['咁咪唔使重開呀','即係唔使另開呀','咁就沿用舊嗰宗呀','即係照原有嗰宗呀'],
 '仲係跟原本嗰宗呀':['照舊嗰宗跟呀','沿用原有嗰宗呀','繼續跟嗰份呀','用返舊紀錄呀'],
 '我唔使成套再交呀':['唔使成套再交呀','即係唔使重交呀','咁唔使由頭交呀','舊嗰套唔使再交呀'],
 '嗰日係我先做嗰步呀':['嗰日先係開頭呀','我嗰日先做第一步','前面係嗰日先啱呀','最先嗰步係嗰日呀'],
 '前面嗰日先係第一份呀':['嗰日先係第一份呀','第一份係嗰日呀','前面其實係嗰日呀','開頭嗰份係嗰日呀'],
 '我唔想前後兩套講法':['我唔想前後唔同','我想一路講法一致','費事兩邊唔對','我怕前後撈亂'],
 '未諗覆核住':['覆核住先唔諗','我未決定覆核','覆核我遲啲先諗','我住先唔做覆核'],
}

def pick(did,n,key,vals): return vals[b.h(did,n,key)%len(vals)]

def strip_alias(term:str)->str:
    t=term
    if '即係' in t:
        a=t.split('即係',1)[0].rstrip('，、（() ')
        if len(H.findall(a))>=2: t=a
    # common generated self-explanations
    for a,z in [('商品及服務稅商品及服務稅','商品及服務稅'),('私人有限公司私人有限公司','私人有限公司')]: t=t.replace(a,z)
    return t

def rewrite_dialogue(d:dict)->None:
    raw_term=d.get('term_yue','')
    term=strip_alias(raw_term)
    d['term_yue']=term
    client_seen=0
    for s in d['segments']:
        y=s['yue']; e=s['en']; n=s['n']
        if s['source_lang']=='yue':
            client_seen+=1
            if raw_term and raw_term!=term: y=y.replace(raw_term,term)
            # Full scoreable term is retained at first client mention. Afterwards
            # use anaphora, mirroring it in the English model where practical.
            if client_seen>1 and term and term in y:
                ref=pick(d['id'],n,'ref',REFS)
                y=y.replace(term,ref)
                english_term=str(d.get('term') or '')
                if english_term and english_term in e:
                    e=e.replace(english_term,pick(d['id'],n,'eref',['this matter','it','this issue','the current matter']))
            for old,vals in DOCS.items():
                if old in y: y=y.replace(old,pick(d['id'],n,'doc'+old,vals))
            for old,vals in PHRASES.items():
                if old in y: y=y.replace(old,pick(d['id'],n,'phrase'+old,vals))
            # The measured median target is 12 Han chars. Promote comma boundaries
            # once a clause reaches ~7 chars; particles are re-shaped afterwards.
            rebuilt=[]
            for part in re.split(r'(?<=[。！？])',y):
                if not part: continue
                punct=part[-1] if part[-1] in '。！？' else '。'; body=part[:-1] if part[-1] in '。！？' else part
                if len(H.findall(body))>14 and '，' in body:
                    xs=body.split('，'); out=[]; acc=''
                    for x in xs:
                        if acc and len(H.findall(acc))>=7: out.append(acc); acc=x
                        else: acc=x if not acc else acc+'，'+x
                    if acc: out.append(acc)
                    body='。'.join(out)
                rebuilt.append(body+punct)
            y=''.join(rebuilt)
            y=v2.particle_shape(y,d['id'],n)
            en,y=v2.compact_pair(e,y,32); e=en
            s['en'],s['yue'],s['wc']=e,y,b.wc(e); s['source'],s['model']=y,e
        else:
            if raw_term and raw_term!=term: y=y.replace(raw_term,term)
            for old,vals in DOCS.items():
                if old in y: y=y.replace(old,pick(d['id'],n,'pdoc'+old,vals))
            en,y=v2.compact_pair(e,y,32); e=en
            s['en'],s['yue'],s['wc']=e,y,b.wc(e); s['source'],s['model']=e,y
    d['total']=sum(s['wc'] for s in d['segments']); d['maxseg']=max(s['wc'] for s in d['segments'])

def main():
    dialogs=v4.build()
    for d in dialogs: rewrite_dialogue(d)
    # Dedupe again after anaphora and remove low-information transitions until
    # every dialogue is comfortably within CCL-style scale.
    v3.final_dedupe(dialogs)
    for d in dialogs: rewrite_dialogue(d)
    for d in dialogs:
        while d['total']>350 and len(d['segments'])>12:
            cand=[(s['wc']+15*len(re.findall(r'\d|\$',s['en'])),i) for i,s in enumerate(d['segments'][1:-1],1)]
            _,i=min(cand); d['segments'].pop(i)
            for j,s in enumerate(d['segments'],1): s['n']=j
            d['total']=sum(s['wc'] for s in d['segments']); d['maxseg']=max(s['wc'] for s in d['segments'])
    errors=v3.structural_errors(dialogs)
    v2.write(dialogs)
    print(json.dumps({'dialogues':500,'segments':sum(len(d['segments']) for d in dialogs),'mean_words':round(sum(d['total'] for d in dialogs)/500,1),'min_words':min(d['total'] for d in dialogs),'max_words':max(d['total'] for d in dialogs),'max_segment':max(d['maxseg'] for d in dialogs),'local_errors':errors[:30]},ensure_ascii=False,indent=2))
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())

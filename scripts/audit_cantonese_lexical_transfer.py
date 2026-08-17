#!/usr/bin/env python3
"""Hard CCL lexical-transfer gate for Cantonese source turns.

The bank intentionally uses a stricter rule than everyday HK code-switching:
client-source Cantonese should not hand the candidate English lexical material.
If a concept can be said in Cantonese, it must be said in Cantonese so the
candidate has to interpret it into English.

Default policy: no ASCII letters in role=C/source_lang=yue source text.
Design around opaque alphabetic codes rather than normalising them as English
inside the Cantonese source.
"""
from __future__ import annotations
import argparse, collections, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LATIN=re.compile(r"[A-Za-z]+(?:[A-Za-z0-9+&./'-]*)(?:\s+[A-Za-z][A-Za-z0-9+&./'-]*)*")

# Suggestions are editorial prompts, not blind replacements.
SUGGEST={
    'Facebook':'臉書','ABN':'澳洲商業號碼','TFN':'稅務檔案號碼','ATO':'澳洲稅務局',
    'GST':'商品及服務稅','payroll':'出糧系統／糧務','pending':'待處理／未正式過數',
    'agent':'地產代理','claim':'索償','policy':'保單','excess':'自付額',
    'email':'電郵','SMS':'短訊','upload':'上載','download':'下載',
    'direct debit':'自動扣帳','application':'申請','reference number':'參考編號',
    'lease':'租約','bond':'租屋按金','invoice':'發票／單據（按語境）',
    'award':'行業最低僱傭條件／行業裁定（按語境）','rejected':'被拒絕',
    'approved':'獲批','online':'網上','portal':'網上平台','account':'帳戶',
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('path',nargs='?',default=str(ROOT/'data/dialogues.json'))
    ap.add_argument('--json',action='store_true')
    args=ap.parse_args()
    bank=json.loads(Path(args.path).read_text(encoding='utf-8'))
    hits=[]; tokens=collections.Counter()
    for d in bank:
        for s in d.get('segments',[]):
            if s.get('role')!='C' or s.get('source_lang')!='yue': continue
            text=str(s.get('source',''))
            ms=list(LATIN.finditer(text))
            if not ms: continue
            ts=[m.group(0) for m in ms]
            tokens.update(ts)
            hits.append({
                'dialogue':d.get('id'),'segment':s.get('n'),'title':d.get('title'),
                'tokens':ts,'source':text,
                'suggestions':{t:SUGGEST.get(t) or SUGGEST.get(t.lower()) for t in ts if SUGGEST.get(t) or SUGGEST.get(t.lower())}
            })
    out={'dialogues':len(bank),'violating_segments':len(hits),'latin_tokens':sum(tokens.values()),
         'unique_tokens':len(tokens),'top_tokens':tokens.most_common(50),'violations':hits}
    if args.json: print(json.dumps(out,ensure_ascii=False,indent=2))
    else:
        print('CCL Cantonese lexical-transfer audit')
        print('violating segments:',len(hits))
        print('Latin lexical tokens:',sum(tokens.values()),'unique:',len(tokens))
        print('top:',tokens.most_common(30))
        for x in hits[:100]: print(f"{x['dialogue']} S{x['segment']}: {x['tokens']} :: {x['source']}")
        print('\nVERDICT:', 'PASS' if not hits else 'FAIL')
    return 1 if hits else 0

if __name__=='__main__': raise SystemExit(main())

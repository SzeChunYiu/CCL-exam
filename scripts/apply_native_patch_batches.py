#!/usr/bin/env python3
"""Apply additive native-Cantonese rewrite patch maps to the current bank.

Patch files live under build/rewrite/batch-*-native.json and use keys `Dxxx:n`.
Each value may replace `en`, `yue`, or both. The script then derives source/model,
English word counts, and dialogue totals consistently.

It writes build/rewrite/dialogues.native.candidate.json unless --apply is given.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'data/dialogues.json'
OUT=ROOT/'build/rewrite/dialogues.native.candidate.json'
WORD_RE=re.compile(r"\b[\w’'-]+\b")

def wc(t:str)->int:return len(WORD_RE.findall(t))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    bank=json.loads(BANK.read_text(encoding='utf-8'))
    index={(d['id'],int(s['n'])):(d,s) for d in bank for s in d['segments']}
    files=sorted((ROOT/'build/rewrite').glob('batch-*-native.json'))
    used={}
    for p in files:
        patch=json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(patch,dict): raise SystemExit(f'{p}: expected object patch map')
        for key,repl in patch.items():
            did,ns=key.split(':',1); k=(did,int(ns))
            if k not in index: raise SystemExit(f'{p}: unknown segment {key}')
            if k in used: raise SystemExit(f'{key} patched twice: {used[k]} and {p.name}')
            used[k]=p.name
            d,s=index[k]
            for f in ('en','yue'):
                if f in repl: s[f]=str(repl[f]).strip()
    for d in bank:
        for s in d['segments']:
            lang=s['source_lang']
            s['source']=s['en'] if lang=='en' else s['yue']
            s['model']=s['yue'] if lang=='en' else s['en']
            s['wc']=wc(s['en'])
        d['total']=sum(s['wc'] for s in d['segments'])
        d['maxseg']=max(s['wc'] for s in d['segments'])
    target=BANK if args.apply else OUT
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(bank,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(f'applied {len(used)} segment patches from {len(files)} batch file(s) -> {target}')
    print(f'dialogues={len(bank)} segments={sum(len(d["segments"]) for d in bank)}')
if __name__=='__main__':main()

#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'dialogues.json'


def normalize_bank(bank):
    for d in bank:
        for s in d['segments']:
            role = s.get('role')
            if role == 'P':
                # Australian officer / service professional speaks English.
                s['source_lang'] = 'en'
                s['source'] = s['en']
                s['model'] = s['yue']
            elif role == 'C':
                # Immigrant / community client speaks spoken Cantonese.
                s['source_lang'] = 'yue'
                s['source'] = s['yue']
                s['model'] = s['en']
            else:
                raise ValueError(f"Unexpected speaker role {role!r} in {d.get('id')}")

        # The dialogue must remain a real two-person exchange.
        assert all(s['role'] in ('P', 'C') for s in d['segments'])
        assert all(s['source_lang'] == ('en' if s['role'] == 'P' else 'yue') for s in d['segments'])
    return bank


def write_markdown(bank):
    src = ['# Source Scripts', '', 'Speaker policy: **English = Australian officer/service professional; Cantonese = immigrant/community client.**', '']
    ans = ['# Model Answers', '', 'Speaker policy: **English = Australian officer/service professional; Cantonese = immigrant/community client.**', '']
    for d in bank:
        src += [f"## {d['id']} — {d['title']}", f"Topic: {d['topic']}", '']
        ans += [f"## {d['id']} — {d['title']}", f"Topic: {d['topic']}", '']
        for s in d['segments']:
            direction = 'English → Cantonese' if s['source_lang'] == 'en' else 'Cantonese → English'
            who = 'Officer / professional' if s['role'] == 'P' else 'Immigrant / client'
            src += [f"**S{s['n']} · {who} · {direction}:** {s['source']}", '']
            ans += [f"**S{s['n']} · {who} · {direction}**", f"Source: {s['source']}", f"Model: {s['model']}", '']
    for folder in ('materials', 'practice_pack'):
        (ROOT / folder / 'SOURCE_SCRIPTS.md').write_text('\n'.join(src) + '\n', encoding='utf-8')
        (ROOT / folder / 'MODEL_ANSWERS.md').write_text('\n'.join(ans) + '\n', encoding='utf-8')


def main():
    bank = json.loads(DATA.read_text(encoding='utf-8'))
    bank = normalize_bank(bank)
    text = json.dumps(bank, ensure_ascii=False, indent=2) + '\n'
    DATA.write_text(text, encoding='utf-8')
    (ROOT / 'practice_pack' / 'dialogues_metadata.json').write_text(text, encoding='utf-8')
    write_markdown(bank)

    summary_path = ROOT / 'data' / 'site_summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    summary['speakerPolicy'] = {
        'professional': 'English',
        'client': 'Cantonese',
        'clientContext': 'immigrant/community life in Australia'
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    assert len(bank) == 100
    assert sum(len(d['segments']) for d in bank) == 1412
    assert all(s['source_lang'] == ('en' if s['role'] == 'P' else 'yue') for d in bank for s in d['segments'])
    print('Normalized 100 dialogues: professional=English, immigrant/client=Cantonese')

if __name__ == '__main__':
    main()

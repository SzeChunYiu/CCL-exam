#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, io, tarfile

ROOT = Path(__file__).resolve().parents[1]
parts = sorted((ROOT / 'src').glob('source_bundle.part*'))
if not parts:
    raise SystemExit('missing source bundle parts')
encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
raw = gzip.decompress(base64.b64decode(encoded))
allowed = {
    'app.js',
    'scripts/build_ccl_pack.py',
    'scripts/build_all_content.py',
    'scripts/naturalise_bank.py',
    'scripts/vary_segments.py',
    'scripts/depattern_bank.py',
    'scripts/refine_variants.py',
    'scripts/build_audio_bundles.py',
    'scripts/fetch_cantonese_dict.py',
}
with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as tf:
    members = [m for m in tf.getmembers() if m.isfile()]
    names = {m.name for m in members}
    if names != allowed:
        missing = sorted(allowed - names)
        extra = sorted(names - allowed)
        raise SystemExit(f'unexpected source bundle contents; missing={missing}, extra={extra}')
    for member in members:
        dest = (ROOT / member.name).resolve()
        if ROOT.resolve() not in dest.parents:
            raise SystemExit(f'unsafe path in source bundle: {member.name}')
        src = tf.extractfile(member)
        if src is None:
            raise SystemExit(f'could not read {member.name}')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read())
        print('unpacked', member.name)

#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, io, tarfile, hashlib

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
frags = [SRC / 'source_bundle.part01a', SRC / 'source_bundle.part01b', SRC / 'source_bundle.part01c']
expected_frag_sha = [
    '7dddfe98f667cebb067cf318584ed9cd607e59b04d04ba4b2031442f2946c1af',
    '747284b68c5089c0d2cf90339d7b63571d86e83e15a6f3d2b90132d8b2634268',
    '4168fe511b770985188b8f21682be2a3f99051c306c8115290718c43594a1c6a',
]
for p, expected in zip(frags, expected_frag_sha):
    data = p.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != expected:
        raise SystemExit(f'fragment checksum mismatch {p.name}: {got}')
part01 = ''.join(p.read_text(encoding='utf-8') for p in frags)
if hashlib.sha256(part01.encode()).hexdigest() != '4f364407e7ecde935d413430b97d28fa80e750ef9dc7d81ac9ecec4c5155a596':
    raise SystemExit('part01 reconstruction mismatch')
rest = [SRC / f'source_bundle.part{i:02d}' for i in range(2, 16)]
encoded = part01 + ''.join(p.read_text(encoding='utf-8').strip() for p in rest)
raw = gzip.decompress(base64.b64decode(encoded))
allowed = {
    'app.js', 'scripts/build_ccl_pack.py', 'scripts/build_all_content.py',
    'scripts/naturalise_bank.py', 'scripts/vary_segments.py', 'scripts/depattern_bank.py',
    'scripts/refine_variants.py', 'scripts/build_audio_bundles.py', 'scripts/fetch_cantonese_dict.py',
}
with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as tf:
    members = [m for m in tf.getmembers() if m.isfile()]
    names = {m.name for m in members}
    if names != allowed:
        raise SystemExit(f'unexpected source bundle contents; missing={sorted(allowed-names)}, extra={sorted(names-allowed)}')
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

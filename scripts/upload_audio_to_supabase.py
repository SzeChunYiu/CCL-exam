#!/usr/bin/env python3
import json, os, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('SUPABASE_URL','').rstrip('/')
KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY','')
BUCKET = os.environ.get('SUPABASE_AUDIO_BUCKET','ccl-audio').strip() or 'ccl-audio'
PREFIX = os.environ.get('SUPABASE_AUDIO_PREFIX','v1').strip().strip('/') or 'v1'
if not URL or not KEY:
    raise SystemExit('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required')
if not URL.startswith('https://'):
    raise SystemExit('SUPABASE_URL must be an https URL')
manifest_path = ROOT/'data/audio_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
headers = {'Authorization':f'Bearer {KEY}','apikey':KEY}

def request(method, url, data=None, extra=None, ok=(200,201,204)):
    h = dict(headers); h.update(extra or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            if r.status not in ok:
                raise RuntimeError(f'{method} {url}: HTTP {r.status} {body[:400]!r}')
            return r.status, body, dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read()
        if e.code in ok:
            return e.code, body, dict(e.headers)
        raise RuntimeError(f'{method} {url}: HTTP {e.code} {body[:800].decode("utf-8","replace")}') from e

bucket_url = f'{URL}/storage/v1/bucket'
payload = json.dumps({
    'id': BUCKET, 'name': BUCKET, 'public': True,
    'file_size_limit': 52428800,
    'allowed_mime_types': ['application/octet-stream','audio/mpeg','application/json']
}).encode()
try:
    request('POST', bucket_url, payload, {'Content-Type':'application/json'}, ok=(200,201))
    print('created bucket', BUCKET)
except RuntimeError as e:
    if '409' not in str(e) and 'already exists' not in str(e).lower():
        raise
    print('bucket already exists', BUCKET)

bundles = manifest.get('bundles',{})
if len(bundles) != 4:
    raise SystemExit(f'expected 4 audio bundles, found {len(bundles)}')
for name, meta in bundles.items():
    path = ROOT/'assets/audio-bundles'/name
    if not path.exists(): raise SystemExit(f'missing {path}')
    if path.stat().st_size != meta['bytes']: raise SystemExit(f'size mismatch for {name}')
    obj = urllib.parse.quote(f'{PREFIX}/{name}', safe='/')
    request('POST', f'{URL}/storage/v1/object/{urllib.parse.quote(BUCKET,safe="")}/{obj}', path.read_bytes(),
            {'Content-Type':'application/octet-stream','x-upsert':'true'}, ok=(200,201))
    print('uploaded', name, path.stat().st_size)

# Also publish the manifest beside the bundles for independent inspection/recovery.
man_bytes = manifest_path.read_bytes()
obj = urllib.parse.quote(f'{PREFIX}/audio_manifest.json', safe='/')
request('POST', f'{URL}/storage/v1/object/{urllib.parse.quote(BUCKET,safe="")}/{obj}', man_bytes,
        {'Content-Type':'application/json','x-upsert':'true'}, ok=(200,201))

public_base = f'{URL}/storage/v1/object/public/{urllib.parse.quote(BUCKET,safe="")}/{PREFIX}/'
# The player requires byte ranges. Verify each public bundle responds and exposes enough bytes.
for name, meta in bundles.items():
    req = urllib.request.Request(public_base + urllib.parse.quote(name), headers={'Range':'bytes=0-31'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            sample = r.read(64)
            if r.status not in (200,206) or not sample:
                raise RuntimeError(f'public range check failed for {name}: HTTP {r.status}')
            print('public check', name, 'HTTP', r.status, 'bytes', len(sample))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'public range check failed for {name}: HTTP {e.code}') from e

remote = {
    'version': 1,
    'provider': 'supabase',
    'bucket': BUCKET,
    'prefix': PREFIX,
    'baseUrl': public_base,
    'manifestUrl': public_base + 'audio_manifest.json',
    'uploadedAt': datetime.now(timezone.utc).isoformat(),
    'bundles': bundles,
    'calibration': manifest.get('calibration',{})
}
out = ROOT/'data/audio_remote.json'
out.write_text(json.dumps(remote,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('wrote', out)

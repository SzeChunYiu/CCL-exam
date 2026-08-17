#!/usr/bin/env python3
from pathlib import Path
import base64,gzip
R=Path(__file__).resolve().parents[1]
for src,dst in [('src/app.js.gz.b64','app.js'),('src/build_ccl_pack.py.gz.b64','scripts/build_ccl_pack.py')]:
    raw=gzip.decompress(base64.b64decode((R/src).read_bytes()))
    (R/dst).write_bytes(raw)
    print('unpacked',dst,len(raw))

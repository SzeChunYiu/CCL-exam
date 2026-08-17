#!/usr/bin/env python3
"""Upload one native500 audio batch using an RLS-scoped public client key.

This uploader is intentionally create-only.  The temporary Supabase Storage
policy permits INSERT only under the frozen native500 release prefix.  Existing
objects are accepted only when a full public read-back has the same byte length
and SHA-256 as the local generated MP3, which makes retries safe without UPDATE
or service-role credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_PUBLIC_UPLOAD_KEY", "")
BUCKET = (os.environ.get("SUPABASE_AUDIO_BUCKET") or "ccl-audio").strip()
PREFIX = (os.environ.get("SUPABASE_AUDIO_PREFIX") or "").strip().strip("/")
EXPECTED_PREFIX = "native500-fc50dedc153b"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def public_url(rel: str) -> str:
    obj = urllib.parse.quote(f"{PREFIX}/{rel}", safe="/")
    return f"{URL}/storage/v1/object/public/{urllib.parse.quote(BUCKET, safe='')}/{obj}"


def verify_full(rel: str, expected: bytes) -> None:
    req = urllib.request.Request(public_url(rel), headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=120) as r:
        if r.status != 200:
            raise RuntimeError(f"verify {rel}: HTTP {r.status}")
        got = r.read()
    if len(got) != len(expected) or sha256(got) != sha256(expected):
        raise RuntimeError(
            f"verify {rel}: content mismatch bytes={len(got)}/{len(expected)} "
            f"sha={sha256(got)[:12]}/{sha256(expected)[:12]}"
        )


def upload_once(rel: str, data: bytes) -> None:
    obj = urllib.parse.quote(f"{PREFIX}/{rel}", safe="/")
    url = f"{URL}/storage/v1/object/{urllib.parse.quote(BUCKET, safe='')}/{obj}"
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {KEY}",
            "apikey": KEY,
            "Content-Type": "audio/mpeg",
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            if r.status not in (200, 201):
                raise RuntimeError(f"upload {rel}: HTTP {r.status}")
    except urllib.error.HTTPError as exc:
        # Create-only retries may see 409 when an identical object already landed.
        if exc.code != 409:
            detail = exc.read()[:500].decode("utf-8", "replace")
            raise RuntimeError(f"upload {rel}: HTTP {exc.code}: {detail}") from exc


def upload_and_verify(p: Path, root: Path) -> None:
    rel = p.relative_to(root).as_posix()
    data = p.read_bytes()
    if len(data) < 2000:
        raise RuntimeError(f"{rel}: suspiciously small MP3")
    last: Exception | None = None
    for attempt in range(4):
        try:
            upload_once(rel, data)
            verify_full(rel, data)
            return
        except Exception as exc:  # transient network/storage failures are retried
            last = exc
            time.sleep(1.0 * (2 ** attempt))
    raise RuntimeError(f"{rel}: {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--expected", type=int, default=1200)
    args = ap.parse_args()

    if not URL.startswith("https://") or not KEY:
        raise SystemExit("SUPABASE_URL and SUPABASE_PUBLIC_UPLOAD_KEY are required")
    if PREFIX != EXPECTED_PREFIX:
        raise SystemExit(f"refusing unexpected release prefix {PREFIX!r}")

    root = Path(args.src)
    files = sorted(p for p in root.rglob("S*.mp3") if p.is_file())
    if len(files) != args.expected:
        raise SystemExit(f"expected {args.expected} MP3s, found {len(files)}")

    failures: list[str] = []
    def one(p: Path):
        try:
            upload_and_verify(p, root)
        except Exception as exc:
            failures.append(str(exc))

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, _ in enumerate(ex.map(one, files), 1):
            if i % 100 == 0:
                print(f"uploaded+sha-verified {i}/{len(files)}")

    if failures:
        print(f"{len(failures)} failure(s); first: {failures[0]}")
        return 2
    print(f"uploaded and full-SHA verified {len(files)} objects under {PREFIX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

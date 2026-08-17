#!/usr/bin/env python3
"""Publish v4 per-segment CCL audio to Supabase Storage.

This replaces nothing in place. It writes to a NEW prefix (default ``v4``) and
only rewrites ``data/audio_remote.json`` after every object has been uploaded
AND verified over the public URL. That makes the switch atomic from a learner's
point of view and trivially reversible -- revert the one config file and v3 is
live again, because v3 objects are never touched.

Do not confuse this with ``upload_audio_to_supabase.py``. That script is the
legacy v1 uploader: it pushes four monolithic ``.bin`` bundles and overwrites
``data/audio_remote.json`` with a bundle-shaped config that has no ``mode``
field. Running it against the current site would break the segment player.

Credentials come from the environment and are never logged:

    SUPABASE_URL                 https://<project>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY    service-role key (write access)
    SUPABASE_AUDIO_BUCKET        default: ccl-audio
    SUPABASE_AUDIO_PREFIX        default: v4
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
BUCKET = (os.environ.get("SUPABASE_AUDIO_BUCKET") or "ccl-audio").strip()
PREFIX = (os.environ.get("SUPABASE_AUDIO_PREFIX") or "v4").strip().strip("/")


def public_base() -> str:
    return f"{URL}/storage/v1/object/public/{urllib.parse.quote(BUCKET, safe='')}/{PREFIX}"


def put_object(rel: str, data: bytes, content_type: str) -> int:
    obj = urllib.parse.quote(f"{PREFIX}/{rel}", safe="/")
    url = f"{URL}/storage/v1/object/{urllib.parse.quote(BUCKET, safe='')}/{obj}"
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Authorization": f"Bearer {KEY}",
            "apikey": KEY,
            "Content-Type": content_type,
            # Idempotent: a re-run after a partial upload overwrites cleanly
            # instead of failing on the objects that already landed.
            "x-upsert": "true",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"upload {rel}: HTTP {e.code} {e.read()[:300].decode('utf-8','replace')}") from e


def verify_public(rel: str, expect_bytes: int) -> None:
    url = f"{public_base()}/{urllib.parse.quote(rel, safe='/')}"
    req = urllib.request.Request(url, headers={"Range": "bytes=0-63"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status not in (200, 206):
                raise RuntimeError(f"verify {rel}: HTTP {r.status}")
            head = r.read(64)
            if len(head) < 8:
                raise RuntimeError(f"verify {rel}: empty body")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"verify {rel}: HTTP {e.code}") from e


def collect(src: Path) -> list[Path]:
    files = sorted(p for p in src.rglob("S*.mp3") if p.is_file())
    bad = [p for p in files if p.stat().st_size < 2000]
    if bad:
        raise SystemExit(
            f"{len(bad)} generated file(s) are suspiciously small, refusing to publish; "
            f"first: {bad[0]}"
        )
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default=str(ROOT / "build" / "audio-v4"))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would be published and exit")
    ap.add_argument("--no-config", action="store_true",
                    help="upload objects but leave data/audio_remote.json alone")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_dir():
        raise SystemExit(f"no generated audio at {src} -- run generate_v4_audio.py first")

    files = collect(src)
    if not files:
        raise SystemExit(f"no S*.mp3 found under {src}")

    report_path = src / "_generation_report.json"
    gen = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}

    print(f"{len(files)} objects -> bucket '{BUCKET}' prefix '{PREFIX}'")
    if args.dry_run:
        for p in files[:5]:
            print("  ", p.relative_to(src))
        print(f"   ... ({len(files)} total)  base={public_base()}")
        return 0

    if not URL or not KEY:
        raise SystemExit(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.\n"
            "Put them in a file (e.g. ~/.ccl_supabase_env) and `source` it first."
        )
    if not URL.startswith("https://"):
        raise SystemExit("SUPABASE_URL must be an https URL")

    failures: list[str] = []

    def one(p: Path):
        rel = p.relative_to(src).as_posix()
        try:
            put_object(rel, p.read_bytes(), "audio/mpeg")
        except Exception as exc:
            failures.append(f"{rel}: {exc}")

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, _ in enumerate(ex.map(one, files), 1):
            if i % 100 == 0:
                print(f"  uploaded {i}/{len(files)}")

    if failures:
        print(f"{len(failures)} upload failure(s); first: {failures[0]}", file=sys.stderr)
        return 2

    # Verify a spread of objects publicly rather than trusting the write status.
    sample = files[:: max(1, len(files) // 25)][:25]
    for p in sample:
        verify_public(p.relative_to(src).as_posix(), p.stat().st_size)
    print(f"verified {len(sample)} objects over the public URL")

    if args.no_config:
        print("skipping config rewrite (--no-config)")
        return 0

    cfg_path = ROOT / "data" / "audio_remote.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    previous = cfg.get("baseUrl")
    cfg.update({
        "provider": "supabase",
        "mode": "segments",
        "version": f"{PREFIX}-neural",
        "baseUrl": public_base(),
        "previousBaseUrl": previous,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
    })
    summary = gen.get("summary", {})
    if summary:
        cfg["calibration"] = {
            "referenceSource": "official NAATI CCL practice recordings (6 dialogues)",
            "englishTargetWpm": summary.get("en", {}).get("target"),
            "cantoneseTargetCharsPerSec": summary.get("yue", {}).get("target"),
            "measuredEnglishWpm": summary.get("en", {}).get("median"),
            "measuredCantoneseCharsPerSec": summary.get("yue", {}).get("median"),
            "perVoice": summary.get("per_voice", {}),
        }
    seg = {}
    for s in gen.get("segments", []):
        seg.setdefault(s["voice"], s["rate"])
    if seg:
        cfg["voiceRates"] = seg
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {cfg_path}")
    print(f"previous baseUrl kept as previousBaseUrl for rollback: {previous}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

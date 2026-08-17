#!/usr/bin/env python3
"""Publish the verified 500-dialogue release and audio metadata to Supabase.

This script is intentionally *not* an authoring tool. It only publishes an exact
already-gated `data/dialogues.json` plus an already-generated audio report. Every
mutation is idempotent and followed by a count/identity verification.

Required environment:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  SUPABASE_AUDIO_PREFIX

Optional:
  RELEASE_AUDIO_REPORT   path to merged generation report JSON
  RELEASE_DRY_RUN=1      validate payloads but perform no writes

Safety invariants:
* refuses any bank other than 500 dialogues x 12 segments;
* refuses any audio report other than exactly one asset per final segment;
* dialogue upserts happen before audio metadata, but stale production audio rows
  are deleted only after all 6000 final rows have been upserted and verified;
* no Storage object is touched here. Storage publication is performed separately
  under a new immutable prefix before this script runs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "data" / "dialogues.json"
REPORT_PATH = Path(os.environ.get("RELEASE_AUDIO_REPORT", ROOT / "build" / "audio-release-report.json"))
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
PREFIX = (os.environ.get("SUPABASE_AUDIO_PREFIX") or "").strip().strip("/")
DRY = os.environ.get("RELEASE_DRY_RUN", "0") == "1"


def api(path: str, *, method="GET", body=None, prefer=None, extra=None):
    if not URL or not KEY:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {KEY}",
        "apikey": KEY,
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    if extra:
        headers.update(extra)
    req = urllib.request.Request(f"{URL}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None), dict(r.headers)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"{method} {path}: HTTP {e.code}: {detail}") from e


def batched(rows, n=100):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def load_bank():
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    if len(bank) != 500:
        raise SystemExit(f"refusing release: {len(bank)} dialogues, expected 500")
    ids = [d.get("id") for d in bank]
    if len(set(ids)) != 500 or ids != [f"D{i:03d}" for i in range(1, 501)]:
        raise SystemExit("refusing release: dialogue ids must be exactly D001..D500 in order")
    for d in bank:
        segs = d.get("segments") or []
        if len(segs) != 12 or [s.get("n") for s in segs] != list(range(1, 13)):
            raise SystemExit(f"refusing release: {d['id']} is not exactly S01..S12")
    return bank


def dialogue_rows(bank):
    now = datetime.now(timezone.utc).isoformat()
    return [
        {"id": d["id"], "topic": d["topic"], "title": d["title"], "payload": d, "updated_at": now}
        for d in bank
    ]


def load_audio(bank):
    if not PREFIX:
        raise SystemExit("SUPABASE_AUDIO_PREFIX is required for a release")
    if not REPORT_PATH.exists():
        raise SystemExit(f"audio report not found: {REPORT_PATH}")
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    segs = report.get("segments") or []
    if len(segs) != 6000:
        raise SystemExit(f"refusing audio metadata release: {len(segs)} segments, expected 6000")
    expected = {(d["id"], s["n"]) for d in bank for s in d["segments"]}
    got = set()
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for r in segs:
        rel = str(r.get("path") or "")
        m = re.fullmatch(r"(D\d{3})/S(\d{2})\.mp3", rel)
        if not m:
            raise SystemExit(f"bad audio path in report: {rel!r}")
        did, n = m.group(1), int(m.group(2))
        key = (did, n)
        if key in got:
            raise SystemExit(f"duplicate audio report segment: {did} S{n:02d}")
        got.add(key)
        src = next(s for d in bank if d["id"] == did for s in d["segments"] if s["n"] == n)
        sha = r.get("sha256")
        size = r.get("bytes")
        # The merged release report should normally provide these. Metadata can
        # still be published without a hash/byte count if Storage verification
        # already completed, but missing path/voice/rate/duration is not allowed.
        dur = r.get("seconds")
        if not r.get("voice") or not r.get("rate") or not dur or dur <= 0:
            raise SystemExit(f"incomplete generation metadata for {rel}")
        rows.append({
            "dialogue_id": did,
            "segment_no": n,
            "source_lang": src["source_lang"],
            "voice": r["voice"],
            "rate": r["rate"],
            "storage_path": f"{PREFIX}/{rel}",
            "duration_ms": int(round(float(dur) * 1000)),
            "bytes": int(size) if size is not None else None,
            "sha256": sha,
            "status": "ready",
            "error_text": None,
            "updated_at": now,
        })
    if got != expected:
        missing = sorted(expected - got)[:10]
        extra = sorted(got - expected)[:10]
        raise SystemExit(f"audio coverage mismatch; missing={missing} extra={extra}")
    return rows


def count_table(table: str) -> int:
    _status, rows, headers = api(
        f"/rest/v1/{table}?select=*&limit=1",
        extra={"Range": "0-0", "Prefer": "count=exact"},
    )
    cr = headers.get("Content-Range", "")
    if "/" not in cr:
        raise RuntimeError(f"no exact count for {table}: {cr!r}")
    return int(cr.rsplit("/", 1)[1])


def verify_audio_prefix() -> int:
    enc = urllib.parse.quote(f"{PREFIX}/", safe="")
    # All final storage paths are under one release prefix. PostgREST `like`
    # supports `*` wildcards.
    _st, rows, headers = api(
        f"/rest/v1/ccl_audio_assets?select=dialogue_id&storage_path=like.{enc}*&limit=1",
        extra={"Range": "0-0", "Prefer": "count=exact"},
    )
    cr = headers.get("Content-Range", "")
    return int(cr.rsplit("/", 1)[1]) if "/" in cr else -1


def main() -> int:
    bank = load_bank()
    drows = dialogue_rows(bank)
    arows = load_audio(bank)
    bank_sha = hashlib.sha256(BANK_PATH.read_bytes()).hexdigest()
    print(json.dumps({
        "bank_sha256": bank_sha,
        "dialogues": len(drows),
        "audio_assets": len(arows),
        "audio_prefix": PREFIX,
        "dry_run": DRY,
    }, indent=2))
    if DRY:
        return 0

    for chunk in batched(drows, 50):
        api(
            "/rest/v1/ccl_dialogues?on_conflict=id",
            method="POST", body=chunk,
            prefer="resolution=merge-duplicates,return=minimal",
        )
    if count_table("ccl_dialogues") < 500:
        raise RuntimeError("dialogue verification failed: fewer than 500 rows after upsert")

    for chunk in batched(arows, 100):
        api(
            "/rest/v1/ccl_audio_assets?on_conflict=dialogue_id,segment_no",
            method="POST", body=chunk,
            prefer="resolution=merge-duplicates,return=minimal",
        )
    prefix_count = verify_audio_prefix()
    if prefix_count != 6000:
        raise RuntimeError(f"audio verification failed: prefix has {prefix_count} rows, expected 6000")

    # Only now remove obsolete segment numbers from pre-500 banks. D001..D500
    # S01..S12 have all been verified above, so this cleanup cannot remove a final
    # release asset.
    api("/rest/v1/ccl_audio_assets?segment_no=gt.12", method="DELETE", prefer="return=minimal")

    # Verify the exact public-bank shape, not merely a lower bound.
    dcount = count_table("ccl_dialogues")
    acount = count_table("ccl_audio_assets")
    if dcount != 500 or acount != 6000:
        raise RuntimeError(f"post-release Supabase shape mismatch: dialogues={dcount}, audio={acount}")
    print(json.dumps({"published": True, "dialogues": dcount, "audio_assets": acount}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

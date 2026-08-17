#!/usr/bin/env python3
"""Atomically promote a fully uploaded native-500 audio release into Supabase.

This runs only after all five synthesis/upload batches succeeded. It validates
all 6,000 manifest rows, range-reads every public object, then upserts the 500
text payloads and 6,000 audio metadata rows. Stale >S12 rows from the old 100-bank
are removed only after new coverage is complete. Finally it rewrites the public
static audio config. Any validation failure happens before the production switch.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
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


def request(method: str, path: str, payload=None, extra=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    headers.update(extra or {})
    req = urllib.request.Request(URL + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            return r.status, dict(r.headers), body
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:1000].decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {detail}") from exc


def upsert(table: str, rows: list[dict], conflict: str, batch: int = 250):
    for start in range(0, len(rows), batch):
        part = rows[start:start + batch]
        path = f"/rest/v1/{table}?on_conflict={urllib.parse.quote(conflict, safe=',')}"
        status, _, _ = request(
            "POST", path, part,
            {"Prefer": "resolution=merge-duplicates,return=minimal"},
        )
        if status not in (200, 201, 204):
            raise RuntimeError(f"upsert {table}: HTTP {status}")
        print(f"  {table}: {min(start + len(part), len(rows))}/{len(rows)}")


def get_json(path: str):
    status, _, body = request("GET", path)
    if status != 200:
        raise RuntimeError(f"GET {path}: HTTP {status}")
    return json.loads(body.decode("utf-8"))


def public_url(storage_path: str) -> str:
    return (
        f"{URL}/storage/v1/object/public/{urllib.parse.quote(BUCKET, safe='')}/"
        f"{urllib.parse.quote(storage_path, safe='/')}"
    )


def verify_public(asset: dict):
    req = urllib.request.Request(public_url(asset["storage_path"]), headers={"Range": "bytes=0-63"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status not in (200, 206):
                raise RuntimeError(f"HTTP {r.status}")
            head = r.read(64)
            if len(head) < 8:
                raise RuntimeError("short body")
            cr = r.headers.get("Content-Range", "")
            m = re.search(r"/(\d+)$", cr)
            if m and int(m.group(1)) != int(asset["bytes"]):
                raise RuntimeError(
                    f"size mismatch public={m.group(1)} manifest={asset['bytes']}"
                )
    except Exception as exc:
        raise RuntimeError(f"public verify {asset['storage_path']}: {exc}") from exc


def load_manifests(pattern: str, prefix: str):
    paths = sorted(Path(p) for p in glob.glob(pattern))
    if len(paths) != 5:
        raise SystemExit(f"expected 5 batch manifests, got {len(paths)} from {pattern}")
    assets, summaries = [], []
    for p in paths:
        doc = json.loads(p.read_text(encoding="utf-8"))
        if doc.get("prefix") != prefix:
            raise SystemExit(f"{p}: prefix {doc.get('prefix')} != {prefix}")
        if doc.get("count") != 1200 or len(doc.get("assets", [])) != 1200:
            raise SystemExit(f"{p}: expected 1200 assets")
        assets.extend(doc["assets"])
        summaries.append(doc.get("generation_summary", {}))
    expected = {(f"D{i:03d}", n) for i in range(1, 501) for n in range(1, 13)}
    got = [(a["dialogue_id"], int(a["segment_no"])) for a in assets]
    if len(got) != 6000 or len(set(got)) != 6000 or set(got) != expected:
        missing = sorted(expected - set(got))[:10]
        extra = sorted(set(got) - expected)[:10]
        raise SystemExit(f"manifest coverage invalid: rows={len(got)} missing={missing} extra={extra}")
    for a in assets:
        if a.get("status") != "ready":
            raise SystemExit(f"manifest asset not ready: {a}")
        if not str(a.get("storage_path", "")).startswith(prefix + "/"):
            raise SystemExit(f"storage path outside release prefix: {a.get('storage_path')}")
        if int(a.get("bytes") or 0) < 2000 or not re.fullmatch(r"[0-9a-f]{64}", str(a.get("sha256", ""))):
            raise SystemExit(f"bad manifest metadata: {a}")
    return assets, summaries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dialogues", default=str(ROOT / "data" / "dialogues.json"))
    ap.add_argument("--manifests", required=True, help="glob for the five batch manifest JSON files")
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--public-workers", type=int, default=32)
    args = ap.parse_args()

    if not URL.startswith("https://") or not KEY:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    bank_path = Path(args.dialogues)
    raw = bank_path.read_bytes()
    bank_sha = hashlib.sha256(raw).hexdigest()
    want_prefix = f"native500-{bank_sha[:12]}"
    if args.prefix != want_prefix:
        raise SystemExit(f"prefix must bind to bank hash: expected {want_prefix}, got {args.prefix}")
    bank = json.loads(raw.decode("utf-8"))
    expected_ids = [f"D{i:03d}" for i in range(1, 501)]
    if [d.get("id") for d in bank] != expected_ids:
        raise SystemExit("dialogue bank ids are not exactly D001..D500 in order")
    if any(len(d.get("segments", [])) != 12 for d in bank):
        raise SystemExit("every dialogue must contain exactly 12 segments")

    assets, summaries = load_manifests(args.manifests, args.prefix)
    print("verifying all 6000 uploaded objects over public Storage URLs")
    with ThreadPoolExecutor(max_workers=args.public_workers) as ex:
        for i, _ in enumerate(ex.map(verify_public, assets), 1):
            if i % 500 == 0:
                print(f"  public verify {i}/6000")

    dialogue_rows = [
        {"id": d["id"], "topic": d["topic"], "title": d["title"], "payload": d}
        for d in bank
    ]
    print("publishing dialogue payloads")
    upsert("ccl_dialogues", dialogue_rows, "id", 50)

    print("publishing audio metadata")
    clean_assets = [{k: v for k, v in a.items() if k != "updated_at"} for a in assets]
    upsert("ccl_audio_assets", clean_assets, "dialogue_id,segment_no", 250)

    # Remove the old bank's extra S13+ metadata only after all new S01..S12 rows
    # have been uploaded, publicly verified, and upserted.
    old_ids = ",".join(f"D{i:03d}" for i in range(1, 101))
    filt = urllib.parse.quote(f"({old_ids})", safe="(),")
    stale_path = f"/rest/v1/ccl_audio_assets?select=dialogue_id,segment_no&dialogue_id=in.{filt}&segment_no=gt.12&limit=1000"
    stale = get_json(stale_path)
    if any(not (1 <= int(x["dialogue_id"][1:]) <= 100 and int(x["segment_no"]) > 12) for x in stale):
        raise SystemExit("refusing stale-row deletion: unexpected row set")
    if stale:
        delete_path = f"/rest/v1/ccl_audio_assets?dialogue_id=in.{filt}&segment_no=gt.12"
        status, _, _ = request("DELETE", delete_path, extra={"Prefer": "return=minimal"})
        if status not in (200, 204):
            raise SystemExit(f"stale metadata deletion failed HTTP {status}")
        print(f"removed {len(stale)} legacy S13+ metadata rows")

    # Production read-back is the final DB guard.
    dialog_ids = get_json("/rest/v1/ccl_dialogues?select=id&order=id.asc&limit=600")
    if [x["id"] for x in dialog_ids] != expected_ids:
        raise SystemExit(f"production dialogue read-back invalid: {len(dialog_ids)} rows")
    rows = get_json("/rest/v1/ccl_audio_assets?select=dialogue_id,segment_no,storage_path,status&order=dialogue_id.asc,segment_no.asc&limit=7000")
    if len(rows) != 6000:
        raise SystemExit(f"production audio metadata count {len(rows)} != 6000")
    got = {(x["dialogue_id"], int(x["segment_no"])) for x in rows}
    expected = {(f"D{i:03d}", n) for i in range(1, 501) for n in range(1, 13)}
    if got != expected:
        raise SystemExit("production audio metadata coverage does not equal D001..D500/S01..S12")
    if any(x["status"] != "ready" or not x["storage_path"].startswith(args.prefix + "/") for x in rows):
        raise SystemExit("production audio metadata contains a non-ready or wrong-prefix row")

    base_url = f"{URL}/storage/v1/object/public/{urllib.parse.quote(BUCKET, safe='')}/{args.prefix}"
    cfg_path = ROOT / "data" / "audio_remote.json"
    old_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg = {
        "provider": "supabase",
        "mode": "segments",
        "version": args.prefix + "-neural",
        "cacheVersion": args.prefix,
        "baseUrl": base_url,
        "previousBaseUrl": old_cfg.get("baseUrl"),
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
        "voices": {
            "en": ["en-AU-WilliamNeural", "en-AU-NatashaNeural"],
            "yue": ["zh-HK-WanLungNeural", "zh-HK-HiuMaanNeural"],
        },
        "rates": {
            "en-AU-WilliamNeural": "+0%",
            "en-AU-NatashaNeural": "+22%",
            "zh-HK-WanLungNeural": "+13%",
            "zh-HK-HiuMaanNeural": "+12%",
        },
        "pitch": "+0Hz",
        "speakerPolicy": {
            "professional": "English",
            "client": "Cantonese",
            "clientContext": "immigrant/community life in Australia",
        },
    }
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path = ROOT / "data" / "audio_release_summary.json"
    summary_path.write_text(json.dumps({
        "bankSha256": bank_sha,
        "prefix": args.prefix,
        "dialogues": 500,
        "segments": 6000,
        "publicBaseUrl": base_url,
        "batchCalibration": summaries,
        "publishedAt": cfg["uploadedAt"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "bank_sha256": bank_sha,
        "prefix": args.prefix,
        "dialogues": 500,
        "audio_assets": 6000,
        "public_base": base_url,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

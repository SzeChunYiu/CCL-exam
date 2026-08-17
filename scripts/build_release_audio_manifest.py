#!/usr/bin/env python3
"""Build a hash-verified metadata manifest for one release-audio batch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expected", type=int, default=1200)
    args = ap.parse_args()

    src = Path(args.src)
    report_path = src / "_generation_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    segments = report.get("segments", [])
    rows = []
    seen = set()
    for item in segments:
        rel = str(item["path"])
        p = src / rel
        if not p.is_file() or p.stat().st_size < 2000:
            raise SystemExit(f"missing/small audio: {rel}")
        parts = Path(rel).parts
        if len(parts) != 2 or not parts[0].startswith("D") or not parts[1].startswith("S"):
            raise SystemExit(f"unexpected audio path: {rel}")
        did = parts[0]
        seg = int(Path(parts[1]).stem[1:])
        key = (did, seg)
        if key in seen:
            raise SystemExit(f"duplicate audio row: {did} S{seg}")
        seen.add(key)
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        rows.append({
            "dialogue_id": did,
            "segment_no": seg,
            "source_lang": item["lang"],
            "voice": item["voice"],
            "rate": item["rate"],
            "storage_path": f"{args.prefix}/{rel}",
            "duration_ms": round(float(item.get("seconds") or 0) * 1000),
            "bytes": p.stat().st_size,
            "sha256": h,
            "status": "ready",
            "error_text": None,
        })

    rows.sort(key=lambda r: (r["dialogue_id"], r["segment_no"]))
    files = sorted(src.rglob("S*.mp3"))
    if len(rows) != args.expected or len(files) != args.expected:
        raise SystemExit(
            f"coverage mismatch: report={len(rows)} files={len(files)} expected={args.expected}"
        )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "prefix": args.prefix,
        "count": len(rows),
        "generation_summary": report.get("summary", {}),
        "assets": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"prefix": args.prefix, "assets": len(rows), "output": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

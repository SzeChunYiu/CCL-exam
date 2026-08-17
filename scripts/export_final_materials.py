#!/usr/bin/env python3
"""Export human-readable study materials from the committed final dialogue bank.

`data/dialogues.json` is the source of truth.  The older materials files predate
500-dialogue generation and must never be treated as authoritative.  This tool
asserts the final release shape, then regenerates source scripts, model answers,
and a compact cross-domain/rewrite-state review sample directly from the JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
SOURCE = ROOT / "materials" / "SOURCE_SCRIPTS.md"
MODELS = ROOT / "materials" / "MODEL_ANSWERS.md"
SAMPLES = ROOT / "build" / "release-samples.md"

# Covers all five encounter states (D001/101/201/301/401 etc.) and all major
# domains, plus the historically tricky VEVO/bridging/AVO/social-service rows.
SAMPLE_IDS = [
    "D001", "D031", "D037", "D038", "D039", "D042", "D086", "D099",
    "D101", "D131", "D137", "D138", "D139", "D186", "D199",
    "D201", "D231", "D237", "D238", "D239", "D286", "D299",
    "D301", "D331", "D337", "D338", "D339", "D386", "D399",
    "D401", "D431", "D437", "D438", "D439", "D486", "D499", "D500",
]


def load_bank() -> list[dict]:
    data = json.loads(BANK.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 500, f"expected 500 dialogues, got {len(data)}"
    ids = [d.get("id") for d in data]
    assert len(ids) == len(set(ids)), "duplicate dialogue ids"
    for d in data:
        segs = d.get("segments") or []
        assert len(segs) == 12, f"{d.get('id')}: expected 12 segments, got {len(segs)}"
        assert [s.get("n") for s in segs] == list(range(1, 13)), f"{d.get('id')}: segment numbering"
        for s in segs:
            assert s.get("source_lang") in {"en", "yue"}
            assert s.get("source") and s.get("model")
    return data


def label(s: dict) -> str:
    role = "Officer / professional" if s.get("role") == "P" else "Immigrant / client"
    direction = "English → Cantonese" if s.get("source_lang") == "en" else "Cantonese → English"
    return f"S{s['n']} · {role} · {direction}"


def header(d: dict) -> list[str]:
    return [
        f"## {d['id']} — {d.get('title','')}",
        f"Topic: {d.get('topic','')}",
        f"Difficulty: {d.get('difficulty','')}",
        "",
    ]


def export_sources(data: list[dict]) -> str:
    out = [
        "# Source Scripts",
        "",
        "Generated directly from `data/dialogues.json`. The JSON bank is the release source of truth.",
        "",
        "Speaker policy: **English = Australian officer/service professional; Cantonese = immigrant/community client.**",
        "",
    ]
    for d in data:
        out.extend(header(d))
        for s in d["segments"]:
            out.append(f"**{label(s)}:** {s['source']}")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def export_models(data: list[dict]) -> str:
    out = [
        "# Model Answers",
        "",
        "Generated directly from `data/dialogues.json`. Each answer is the model interpretation for the corresponding source segment.",
        "",
    ]
    for d in data:
        out.extend(header(d))
        for s in d["segments"]:
            out.append(f"**{label(s)}**")
            out.append(f"- Source: {s['source']}")
            out.append(f"- Model: {s['model']}")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def export_samples(data: list[dict]) -> str:
    by_id = {d["id"]: d for d in data}
    missing = [x for x in SAMPLE_IDS if x not in by_id]
    assert not missing, f"sample ids missing: {missing}"
    out = [
        "# Final 500-bank release samples",
        "",
        "This file is a compact manual-review slice generated from the exact committed JSON release candidate.",
        "",
    ]
    for did in SAMPLE_IDS:
        d = by_id[did]
        out.extend(header(d))
        for s in d["segments"]:
            out.append(f"**{label(s)}**")
            out.append(f"- Source: {s['source']}")
            out.append(f"- Model: {s['model']}")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    data = load_bank()
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    SAMPLES.parent.mkdir(parents=True, exist_ok=True)
    SOURCE.write_text(export_sources(data), encoding="utf-8")
    MODELS.write_text(export_models(data), encoding="utf-8")
    SAMPLES.write_text(export_samples(data), encoding="utf-8")
    print(json.dumps({
        "dialogues": len(data),
        "segments": sum(len(d["segments"]) for d in data),
        "source_material": str(SOURCE.relative_to(ROOT)),
        "model_material": str(MODELS.relative_to(ROOT)),
        "sample_file": str(SAMPLES.relative_to(ROOT)),
        "sample_dialogues": len(SAMPLE_IDS),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

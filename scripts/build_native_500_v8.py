#!/usr/bin/env python3
"""Native-rhythm release candidate.

This keeps v6's fact-anchored client language, adds the short acknowledgement
turns found in the official/service corpus, and resolves rare whole-bank exact
sentence collisions without repeatedly lengthening the English side.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_native_500 as b
import build_native_500_v2 as v2
import build_native_500_v4 as v4
import build_native_500_v5 as v5
import build_native_500_v6 as v6

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")

SHORT_CLOSE = [
    ("好，明白喇。", "Okay, I understand."),
    ("得，我記住喇。", "All right, I will remember that."),
    ("哦，原來係咁。", "Oh, I see now."),
    ("咁就清楚喇。", "That is clear now."),
    ("好，唔該晒。", "Okay, thank you very much."),
    ("明白，唔該。", "I understand, thank you."),
    ("得，咁就好喇。", "All right, that is good."),
    ("好，我識做喇。", "Okay, I know what to do."),
    ("嗯，依家明喇。", "Mm, I understand now."),
    ("得，我跟住做。", "All right, I will do that."),
]


def short_close(c: dict, action: str) -> tuple[str, str]:
    y, e = SHORT_CLOSE[b.h(c["id"], c["variant"], action, "short") % len(SHORT_CLOSE)]
    return e, y


def client_action(action: str, c: dict, first_client: bool) -> tuple[str, str]:
    if action in {"c_close", "c_decision"}:
        return short_close(c, action)
    return v6.client_action(action, c, first_client)


def make_dialogue(item: dict, idx: int, variant: int) -> dict:
    c = b.make_ctx(item, idx, variant)
    c["term_yue"] = v6.first_term(c)
    seq = b.TRAJECTORIES[b.h(c["id"], c["base_title"], "trajectory") % len(b.TRAJECTORIES)]
    segs = []
    first_client = True
    for n, action in enumerate(seq, 1):
        if action.startswith("c_"):
            en, yue = client_action(action, c, first_client)
            first_client = False
            en, yue = v2.compact_pair(en, yue, 30)
            segs.append({"n": n, "role": "C", "source_lang": "yue", "en": en, "yue": yue,
                         "source": yue, "model": en, "wc": b.wc(en)})
        else:
            en, yue = b.turn(action, c)
            yue = v4.clean(v5.strip_alias(yue))
            en, yue = v2.compact_pair(en, yue, 30)
            segs.append({"n": n, "role": "P", "source_lang": "en", "en": en, "yue": yue,
                         "source": en, "model": yue, "wc": b.wc(en)})
    title = c["base_title"] if variant == 0 else f"{c['base_title']} — {b.STAGES[variant]}"
    d = {"id": c["id"], "topic": c["topic"], "title": title, "term": c["term_en"],
         "term_yue": c["term_yue"], "segments": segs, "difficulty": item.get("difficulty", "Medium")}
    d["total"] = sum(s["wc"] for s in segs)
    d["maxseg"] = max(s["wc"] for s in segs)
    return d


def sentence_parts(t: str) -> list[str]:
    return [x.strip() for x in re.split(r"[。！？]", t) if len(HAN.findall(x)) >= 6]


def unique_sentences(dialogues: list[dict]) -> None:
    """Resolve exact Cantonese sentence reuse across ALL source/model text.

    Each affected segment receives one compact bilingual factual cue. If more
    than one sentence in that segment collides, the same cue is attached to each
    Cantonese sentence but is stated only once in English, keeping the segment
    below 35 words while preserving the facts in both languages.
    """
    seen: dict[str, str] = {}
    for d in dialogues:
        num = int(d["id"][1:])
        variant = (num - 1) // 100
        base = ((num - 1) % 100) + 1
        dummy = {"topic": d["topic"], "title": d["title"], "term": d["term"], "term_yue": d["term_yue"]}
        c = b.make_ctx(dummy, base, variant)
        cue_y = f"，講緊{c['date_yue']}{c['amount_yue']}嗰項"
        cue_e = f", for {c['amount_en']} on {c['date_en']}"
        for s in d["segments"]:
            y = s["yue"]
            collided = []
            for part in list(sentence_parts(y)):
                owner = seen.get(part)
                if owner and owner != d["id"]:
                    collided.append(part)
                else:
                    seen[part] = d["id"]
            if not collided:
                continue
            for part in collided:
                repl = part + cue_y
                y = y.replace(part, repl, 1)
                seen[repl] = d["id"]
            s["yue"] = y
            s["en"] = s["en"].rstrip(".!?") + cue_e + "."
            s["wc"] = b.wc(s["en"])
            if s["source_lang"] == "yue": s["source"], s["model"] = y, s["en"]
            else: s["source"], s["model"] = s["en"], y


def validate(dialogues: list[dict]) -> list[str]:
    errors = []
    seen = {}
    if len(dialogues) != 500:
        errors.append(f"dialogues={len(dialogues)}")
    for d in dialogues:
        if not 12 <= len(d["segments"]) <= 16:
            errors.append(f"{d['id']}: segments={len(d['segments'])}")
        if d["maxseg"] > 35:
            errors.append(f"{d['id']}: maxseg={d['maxseg']}")
        if d["total"] > 360:
            errors.append(f"{d['id']}: total={d['total']}")
        for s in d["segments"]:
            if s["wc"] > 35:
                errors.append(f"{d['id']} S{s['n']}: wc={s['wc']}")
            if s["source_lang"] == "yue" and LATIN.search(s["source"]):
                errors.append(f"{d['id']} S{s['n']}: Latin={LATIN.findall(s['source'])}")
            for p in sentence_parts(s["yue"]):
                if p in seen and seen[p] != d["id"]:
                    errors.append(f"exact {seen[p]}/{d['id']}: {p}")
                seen[p] = d["id"]
    return errors


def main() -> int:
    base = json.loads(BANK.read_text(encoding="utf-8"))[:100]
    dialogues = [make_dialogue(item, idx, variant)
                 for variant in range(5) for idx, item in enumerate(base, 1)]

    for d in dialogues:
        while d["total"] > 340 and len(d["segments"]) > 12:
            candidates = []
            for i, s in enumerate(d["segments"][1:-1], 1):
                score = s["wc"] + 12 * len(re.findall(r"\d|\$", s["en"]))
                candidates.append((score, i))
            _, i = min(candidates)
            d["segments"].pop(i)
            for j, s in enumerate(d["segments"], 1): s["n"] = j
            d["total"] = sum(s["wc"] for s in d["segments"])
            d["maxseg"] = max(s["wc"] for s in d["segments"])

    unique_sentences(dialogues)
    for d in dialogues:
        d["total"] = sum(s["wc"] for s in d["segments"])
        d["maxseg"] = max(s["wc"] for s in d["segments"])
        while d["total"] > 360 and len(d["segments"]) > 12:
            # Collision cues can add a few words. Remove one transition if needed.
            cand = [(s["wc"], i) for i, s in enumerate(d["segments"][1:-1], 1)]
            _, i = min(cand)
            d["segments"].pop(i)
            for j, s in enumerate(d["segments"], 1): s["n"] = j
            d["total"] = sum(s["wc"] for s in d["segments"])
            d["maxseg"] = max(s["wc"] for s in d["segments"])

    errors = validate(dialogues)
    v2.write(dialogues)
    print(json.dumps({
        "dialogues": len(dialogues), "segments": sum(len(d["segments"]) for d in dialogues),
        "mean_words": round(sum(d["total"] for d in dialogues) / len(dialogues), 1),
        "min_words": min(d["total"] for d in dialogues), "max_words": max(d["total"] for d in dialogues),
        "max_segment": max(d["maxseg"] for d in dialogues), "local_errors": errors[:40]
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

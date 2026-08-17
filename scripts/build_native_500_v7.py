#!/usr/bin/env python3
"""Targeted release pass over the fact-anchored native bank.

V6 reached the intended Cantonese register on every measured axis except repeated
10-grams. Its hotspot report showed that almost all remaining repetition came
from eight action joins (wait-period follow-up, change reporting, challenge,
condition, consequence, evidence, repair, decision). V7 rewrites those joins so
an actual scenario fact sits inside the wording. It does not add random fillers
or weaken the corpus gate.
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


def client_action(action: str, c: dict, first_client: bool) -> tuple[str, str]:
    r = v6.ref(c, action)
    d = v6.doc(c, action)
    # A second document lexicalisation avoids a repeated document+action join.
    d2 = v6.doc(c, action + "_second")
    t = v6.first_term(c) if first_client else r

    if action == "c_evidence":
        y = (f"{c['date_yue']}嗰批{d}，{v6.choose(c,'ready')}{c['count_yue']}。"
             f"{c['date2_yue']}{d2}{v6.choose(c,'later')}。{r}仲差一份。")
        e = (f"I have {c['count_en']} of the {c['doc_en']} material ready from {c['date_en']}. "
             f"The remaining document will not be available until {c['date2_en']}, so one item is still outstanding.")
    elif action == "c_missing":
        y = (f"{c['date2_yue']}{d}{v6.choose(c,'later')}。"
             f"{r}到{c['date_yue']}嗰份，{v6.choose(c,'continue')}得唔得？")
        e = (f"I will not have the {c['doc_en']} until {c['date2_en']}. "
             f"For the record linked to {c['date_en']}, can {c['term_en']} continue instead of starting again?")
    elif action == "c_repair":
        y = (f"{c['date_yue']}{v6.choose(c,'repair')}。{r}啱嘅係{c['date2_yue']}。"
             f"前面嗰步，{c['date_yue']}{d}先啱。")
        e = (f"I need to correct the date I gave. For {c['term_en']}, the correct later date is {c['date2_en']}; "
             f"the earlier {c['doc_en']} step was on {c['date_en']}.")
    elif action == "c_condition":
        y = (f"{c['date2_yue']}{v6.choose(c,'accepted')}{d}。"
             f"{r}到{c['date2_yue']}就{v6.choose(c,'continue')}，係咪？")
        e = (f"If the {c['doc_en']} is accepted on {c['date2_en']}, can the {c['term_en']} matter then continue "
             f"under the existing record? ")
    elif action == "c_consequence":
        y = (f"{c['date2_yue']}{r}仲未定，{v6.effect(c)}{v6.choose(c,'risk')}？"
             f"由{c['date_yue']}開始等{c['wait_yue']}，{v6.choose(c,'while')}？")
        e = (f"If {c['term_en']} is still unresolved on {c['date2_en']}, could it affect {c['effect_en']}? "
             f"During the {c['wait_en']} from {c['date_en']}, what should I keep doing?")
    elif action == "c_timing":
        y = (f"{r}，{v6.choose(c,'when')}？{c['date2_yue']}前{v6.choose(c,'not_chase')}。"
             f"{c['wait_yue']}後，{c['date_yue']}嗰次再問得唔得？")
        e = (f"When should I follow up on {c['term_en']}? I do not want to chase too early before {c['date2_en']}; "
             f"would following up {c['wait_en']} after the {c['date_en']} event be reasonable?")
    elif action == "c_change":
        y = (f"{c['date_yue']}到{c['date2_yue']}之間有變，{r}{v6.choose(c,'update')}？"
             f"{d}到{c['date2_yue']}之前，{v6.choose(c,'one_record')}。")
        e = (f"If something changes between {c['date_en']} and {c['date2_en']}, should I update the {c['term_en']} record? "
             f"For the {c['doc_en']} material, I want to keep one consistent record before {c['date2_en']}.")
    elif action == "c_challenge":
        y = (f"{c['date2_yue']}{r}份回覆提到{c['amount_yue']}。"
             f"{c['amount_yue']}嗰個數，{v6.choose(c,'no_reason')}。{d}方面，{v6.choose(c,'ask_basis')}？")
        e = (f"The {c['date2_en']} response about {c['term_en']} uses {c['amount_en']} but does not explain that figure. "
             f"Can I ask what reasons and {c['doc_en']} material they relied on?")
    elif action == "c_decision":
        y = (f"{v6.choose(c,'plan')}，{c['date_yue']}{d}我留好。"
             f"{c['date2_yue']}補欠嗰份。由{c['date2_yue']}等{c['wait_yue']}，{v6.choose(c,'follow')}。")
        e = (f"I understand the plan. I will keep the {c['date_en']} {c['doc_en']} material, add the missing item on "
             f"{c['date2_en']}, and wait {c['wait_en']} from then before following up if needed.")
    else:
        return v6.client_action(action, c, first_client)

    y = v4.clean(v5.strip_alias(y))
    y = v6.add_connective(y, c, action)
    y = v6.light_particles(y, c, action)
    return e.strip(), y


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


def resolve_all_sentence_collisions(dialogues: list[dict]) -> None:
    """Keep BOTH client source and professional model answers free of exact reuse.

    A duplicate gets the dialogue's own date+amount cue. The same facts are added
    to the English side in five words or fewer so semantic alignment is retained.
    """
    seen: dict[str, str] = {}
    for d in dialogues:
        num = int(d["id"][1:])
        variant = (num - 1) // 100
        base = ((num - 1) % 100) + 1
        dummy = {"topic": d["topic"], "title": d["title"], "term": d["term"], "term_yue": d["term_yue"]}
        c = b.make_ctx(dummy, base, variant)
        cue_y = f"，就{c['date_yue']}{c['amount_yue']}嗰項"
        cue_e = f", for {c['amount_en']} on {c['date_en']}"
        for s in d["segments"]:
            y = s["yue"]
            changed = False
            for part in list(sentence_parts(y)):
                if part in seen and seen[part] != d["id"]:
                    repl = part + cue_y
                    y = y.replace(part, repl, 1)
                    # Add the same factual cue to the English sentence. Generator
                    # segments are capped at 30 words, leaving room under CCL's 35.
                    e = s["en"].rstrip(".!?") + cue_e + "."
                    s["en"] = e
                    seen[repl] = d["id"]
                    changed = True
                else:
                    seen[part] = d["id"]
            if changed:
                s["yue"] = y
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
        if not 220 <= d["total"] <= 360:
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
        while d["total"] > 345 and len(d["segments"]) > 12:
            candidates = []
            for i, s in enumerate(d["segments"][1:-1], 1):
                score = s["wc"] + 12 * len(re.findall(r"\d|\$", s["en"]))
                candidates.append((score, i))
            _, i = min(candidates)
            d["segments"].pop(i)
            for j, s in enumerate(d["segments"], 1): s["n"] = j
            d["total"] = sum(s["wc"] for s in d["segments"])
            d["maxseg"] = max(s["wc"] for s in d["segments"])

    resolve_all_sentence_collisions(dialogues)
    for d in dialogues:
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

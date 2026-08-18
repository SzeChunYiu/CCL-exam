#!/usr/bin/env python3
"""Build 500 coherent CCL dialogues from 100 grounded scenario seeds.

This deliberately replaces the release-v18 action-template architecture.  The
old release generated each turn independently from a local action family; that
made sentences diverse but allowed the 12 turns to orbit the same nouns without
forming one causal conversation.

The semantic backbone here comes from ``build_ccl_pack.py``'s earlier
whole-dialogue generator.  That file contains 100 grounded Australian service
scenarios and five complete encounter arcs.  We selectively load only its data
and ``make_turns`` function through the Python AST, avoiding its top-level audio
and material-generation side effects.

ID mapping remains stable:
  D001-D100  initial enquiry
  D101-D200  follow-up after response
  D201-D300  evidence discrepancy
  D301-D400  deadline and consequence
  D401-D500  outcome and review

Every dialogue follows a fixed six-exchange contract.  The professional source
is English and the client source is Cantonese throughout, matching the site's
speaker policy.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "build_ccl_pack.py"
DEFAULT_OUT = ROOT / "build" / "coherent500.json"

LOAD_NAMES = {
    "T", "RAW", "CONCERN", "ACTION", "DEAD", "PROC", "PROC_Y", "OV",
    "INTERIM", "REVIEW",
}

VARIANT_SUFFIX = [
    "",
    " — Follow-up after response",
    " — Evidence discrepancy",
    " — Deadline and consequence",
    " — Outcome and review",
]

STAGES = {
    0: [
        "opening", "concern_deadline", "term_rule", "fact_check",
        "process_answer", "evidence_question", "submission_answer",
        "timing_question", "timing_answer", "review_question",
        "review_answer", "closure",
    ],
    1: [
        "opening", "update_question", "term_rule", "consequence_question",
        "process_answer", "evidence_question", "submission_answer",
        "interim_question", "timing_answer", "review_question",
        "review_answer", "closure",
    ],
    2: [
        "opening", "fact_concern", "term_rule", "consequence_question",
        "process_answer", "evidence_question", "submission_answer",
        "consequence_followup", "timing_answer", "review_question",
        "review_answer", "closure",
    ],
    3: [
        "opening", "deadline_concern", "term_rule", "consequence_question",
        "process_answer", "evidence_discrepancy", "submission_answer",
        "consequence_followup", "timing_answer", "review_question",
        "review_answer", "closure",
    ],
    4: [
        "opening", "fact_concern", "term_rule", "missing_info_question",
        "process_answer", "evidence_question", "submission_answer",
        "timing_question", "timing_answer", "change_question",
        "review_answer", "closure",
    ],
}


def load_backbone() -> tuple[dict, list[dict]]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    keep: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node.target, ast.Name):
                targets = [node.target.id]
            if any(name in LOAD_NAMES for name in targets):
                keep.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "make_turns":
            keep.append(node)
    ns: dict = {}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(SOURCE), "exec"), ns)
    missing = sorted((LOAD_NAMES | {"make_turns"}) - set(ns))
    if missing:
        raise SystemExit(f"could not load coherent backbone names: {missing}")

    seeds=[]
    for line in ns["RAW"].splitlines():
        p=line.split("|")
        if len(p)!=10:
            raise SystemExit(f"bad seed row ({len(p)} fields): {line}")
        seeds.append({
            "topic":p[0], "title":p[1],
            "issue_en":p[2], "issue_yue":p[3],
            "term_en":p[4], "term_yue":p[5],
            "detail_en":p[6], "detail_yue":p[7],
            "doc_en":p[8], "doc_yue":p[9],
        })
    if len(seeds)!=100:
        raise SystemExit(f"expected 100 scenario seeds, got {len(seeds)}")
    return ns,seeds


WORD = re.compile(r"\b[\w’'-]+\b")
def wc(text: str) -> int:
    return len(WORD.findall(text))


def make_dialogue(ns: dict, seed: dict, seed_index: int, variant: int) -> dict:
    # make_turns chooses its complete encounter arc from i % 5.  Multiplying the
    # scenario index by five keeps scenario-specific rotation deterministic while
    # guaranteeing the requested variant.
    turns = ns["make_turns"](seed, seed_index * 5 + variant)
    if len(turns)!=12:
        raise SystemExit(f"{seed['title']} v{variant}: expected 12 turns, got {len(turns)}")
    stages=STAGES[variant]
    segs=[]
    for n,((role,en,yue),stage) in enumerate(zip(turns,stages),1):
        if role not in {"P","C"}:
            raise SystemExit(f"{seed['title']} v{variant} S{n}: bad role {role}")
        expected_role = "P" if n % 2 else "C"
        if role != expected_role:
            raise SystemExit(f"{seed['title']} v{variant} S{n}: expected {expected_role}, got {role}")
        source_lang = "en" if role=="P" else "yue"
        source = en if source_lang=="en" else yue
        model = yue if source_lang=="en" else en
        segs.append({
            "n":n, "role":role, "source_lang":source_lang,
            "source":source, "model":model, "en":en, "yue":yue,
            "wc":wc(en), "stage":stage,
        })
    did=f"D{variant*100+seed_index+1:03d}"
    maxseg=max(s["wc"] for s in segs)
    if maxseg>35:
        raise SystemExit(f"{did}: max English segment {maxseg} > 35")
    return {
        "id":did,
        "topic":seed["topic"],
        "title":seed["title"]+VARIANT_SUFFIX[variant],
        "term":seed["term_en"],
        "term_yue":seed["term_yue"],
        "segments":segs,
        "total":sum(s["wc"] for s in segs),
        "maxseg":maxseg,
        "difficulty":"Medium",
        "logic_version":"coherent-v1",
        "encounter_variant":variant,
    }


def build() -> list[dict]:
    ns,seeds=load_backbone()
    bank=[]
    for variant in range(5):
        for i,seed in enumerate(seeds):
            bank.append(make_dialogue(ns,seed,i,variant))
    expected=[f"D{i:03d}" for i in range(1,501)]
    if [d["id"] for d in bank] != expected:
        raise SystemExit("ID coverage/order is not D001..D500")
    if sum(len(d["segments"]) for d in bank)!=6000:
        raise SystemExit("segment coverage is not exactly 6000")
    return bank


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--promote", action="store_true",
                    help="write tracked data/dialogues.json instead of only build output")
    args=ap.parse_args()
    bank=build()
    out=ROOT/"data/dialogues.json" if args.promote else Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "output":str(out), "dialogues":len(bank), "segments":6000,
        "max_segment_words":max(d["maxseg"] for d in bank),
        "logic_version":"coherent-v1",
    },indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

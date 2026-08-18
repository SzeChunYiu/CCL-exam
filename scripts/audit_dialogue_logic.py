#!/usr/bin/env python3
"""Audit causal and bilingual logic across the 500-dialogue CCL bank.

The older release gates were good at grammar, duplication, Cantonese register and
scoreable fidelity, but they did not test whether turn N actually set up turn
N+1. This gate makes the conversation contract explicit.

It rejects:
* broken P/C alternation or language-role policy;
* missing/reordered dialogue stages;
* a question not followed by its expected answer class;
* premature filing/closure before process/timing/review answers;
* v18-style artificial correction loops;
* cross-language scenario-component swaps at the stage where that component is
  contractually required (issue, term, fact, evidence);
* generic acknowledgements pretending to be a substantive answer.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BACKBONE=ROOT/"scripts/build_ccl_pack.py"

STAGES={
    0:["opening","concern_deadline","term_rule","fact_check","process_answer","evidence_question","submission_answer","timing_question","timing_answer","review_question","review_answer","closure"],
    1:["opening","update_question","term_rule","consequence_question","process_answer","evidence_question","submission_answer","interim_question","timing_answer","review_question","review_answer","closure"],
    2:["opening","fact_concern","term_rule","consequence_question","process_answer","evidence_question","submission_answer","consequence_followup","timing_answer","review_question","review_answer","closure"],
    3:["opening","deadline_concern","term_rule","consequence_question","process_answer","evidence_discrepancy","submission_answer","consequence_followup","timing_answer","review_question","review_answer","closure"],
    4:["opening","fact_concern","term_rule","missing_info_question","process_answer","evidence_question","submission_answer","timing_question","timing_answer","change_question","review_answer","closure"],
}

# Full scenario atoms that each whole-dialogue arc explicitly places in fixed
# turns. Checking them there avoids false positives from short generic words
# appearing coincidentally elsewhere, while still catching real bilingual swaps
# such as English "photo ID" paired with Cantonese "tax details".
EXPECTED_COMPONENTS={
    0:{1:"issue",3:"term",4:"detail",6:"doc",7:"doc",12:"term"},
    1:{1:"issue",2:"term",3:"detail",6:"doc",12:"term"},
    2:{1:"issue",2:"detail",3:"term",6:"doc",12:"term"},
    3:{1:"issue",2:"detail",3:"term",6:"doc",12:"term"},
    4:{1:"issue",2:"detail",3:"term",6:"doc",12:"term"},
}
COMP_KEYS={
    "issue":("issue_en","issue_yue"),
    "term":("term_en","term_yue"),
    "detail":("detail_en","detail_yue"),
    "doc":("doc_en","doc_yue"),
}

ANSWER_AFTER={
    "concern_deadline":"term_rule",
    "update_question":"term_rule",
    "fact_check":"process_answer",
    "consequence_question":"process_answer",
    "evidence_question":"submission_answer",
    "evidence_discrepancy":"submission_answer",
    "interim_question":"timing_answer",
    "timing_question":"timing_answer",
    "consequence_followup":"timing_answer",
    "review_question":"review_answer",
    "change_question":"review_answer",
    "missing_info_question":"process_answer",
}

BAD_ARTIFICIAL=[
    re.compile(r"\bwas not the point\b",re.I),
    re.compile(r"\bmy point about .{1,80} was wrong\b",re.I),
    re.compile(r"\bi mixed up .{1,80}; the point\b",re.I),
    re.compile(r"嗰句講錯咗"),
    re.compile(r"先放低；"),
]
BAD_EN=[
    re.compile(r"\b(?:details|records|terms|forecasts) is\b",re.I),
    re.compile(r"\b(?:details|records|terms|forecasts) does\b",re.I),
    re.compile(r"\bcheck [^.?!]{0,80} is[.?!]",re.I),
]
ACK_EN=re.compile(r"^(?:okay|ok|yes|right|good|fine|i see|understood|that makes sense|i understand|all right)[.! ]*$",re.I)


def load_seeds() -> list[dict]:
    tree=ast.parse(BACKBONE.read_text(encoding="utf-8"))
    raw=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="RAW" for t in node.targets):
            raw=ast.literal_eval(node.value)
            break
    if raw is None:
        raise SystemExit("could not load RAW scenario seeds")
    seeds=[]
    for line in raw.splitlines():
        p=line.split("|")
        if len(p)!=10: raise SystemExit(f"bad seed: {line}")
        seeds.append({
            "topic":p[0],"title":p[1],"issue_en":p[2],"issue_yue":p[3],
            "term_en":p[4],"term_yue":p[5],"detail_en":p[6],"detail_yue":p[7],
            "doc_en":p[8],"doc_yue":p[9],
        })
    return seeds


def norm(s:str)->str:
    return re.sub(r"\s+"," ",str(s).lower()).strip(" .?!，。！？；;：:")


def has(hay:str,needle:str)->bool:
    return norm(needle) in norm(hay)


def audit(bank:list[dict]) -> dict:
    seeds=load_seeds()
    failures=[]
    counts={"dialogues":len(bank),"segments":0,"component_checks":0,"answer_links":0}
    if len(bank)!=500:
        failures.append(f"dialogue_count:{len(bank)}")
    expected_ids=[f"D{i:03d}" for i in range(1,501)]
    if [d.get("id") for d in bank]!=expected_ids:
        failures.append("id_order_not_D001_D500")

    for di,d in enumerate(bank):
        did=d.get("id",f"index-{di}")
        variant=di//100
        seed=seeds[di%100]
        segs=d.get("segments",[])
        counts["segments"]+=len(segs)
        if len(segs)!=12:
            failures.append(f"{did}:segment_count={len(segs)}")
            continue
        stages=[s.get("stage") for s in segs]
        if stages!=STAGES[variant]:
            failures.append(f"{did}:stage_sequence={stages}")
        if d.get("encounter_variant")!=variant:
            failures.append(f"{did}:encounter_variant={d.get('encounter_variant')} expected={variant}")
        if d.get("logic_version")!="coherent-v1":
            failures.append(f"{did}:logic_version={d.get('logic_version')}")

        for i,s in enumerate(segs):
            n=i+1
            want_role="P" if n%2 else "C"
            want_lang="en" if want_role=="P" else "yue"
            if s.get("n")!=n or s.get("role")!=want_role or s.get("source_lang")!=want_lang:
                failures.append(f"{did}:S{n:02d}:role/lang/n contract")
            en=str(s.get("en","")); y=str(s.get("yue",""))
            source=en if want_lang=="en" else y
            model=y if want_lang=="en" else en
            if s.get("source")!=source or s.get("model")!=model:
                failures.append(f"{did}:S{n:02d}:source_model_mirror")
            for rx in BAD_ARTIFICIAL:
                if rx.search(en) or rx.search(y):
                    failures.append(f"{did}:S{n:02d}:artificial_repair:{rx.pattern}")
            for rx in BAD_EN:
                if rx.search(en): failures.append(f"{did}:S{n:02d}:malformed_en:{rx.pattern}")

            comp=EXPECTED_COMPONENTS[variant].get(n)
            if comp:
                ek,yk=COMP_KEYS[comp]
                counts["component_checks"]+=1
                if not has(en,seed[ek]) or not has(y,seed[yk]):
                    failures.append(
                        f"{did}:S{n:02d}:missing_paired_{comp}:"
                        f"en={has(en,seed[ek])},yue={has(y,seed[yk])}"
                    )

            # Substantive professional answer stages must not collapse into a bare
            # acknowledgement. This catches dialogue shells that never answer.
            if s.get("stage") in {"process_answer","submission_answer","timing_answer","review_answer","term_rule"}:
                if ACK_EN.match(norm(en)) or len(re.findall(r"[A-Za-z]+",en))<8:
                    failures.append(f"{did}:S{n:02d}:non_substantive_answer:{s.get('stage')}")

        for i,s in enumerate(segs[:-1]):
            stage=s.get("stage")
            if stage in ANSWER_AFTER:
                counts["answer_links"]+=1
                if segs[i+1].get("stage")!=ANSWER_AFTER[stage]:
                    failures.append(f"{did}:S{i+1:02d}:{stage}->expected {ANSWER_AFTER[stage]}")

        if segs[-1].get("stage")!="closure" or segs[-1].get("role")!="C":
            failures.append(f"{did}:bad_closure")

    return {"failures":failures,"metrics":counts,"passed":not failures}


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bank")
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    try:
        bank=json.loads(Path(args.bank).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"could not read bank: {exc}",file=sys.stderr); return 4
    out=audit(bank)
    if args.json:
        print(json.dumps(out,ensure_ascii=False,indent=2))
    else:
        print(json.dumps(out["metrics"],ensure_ascii=False,indent=2))
        if out["failures"]:
            print(f"FAIL {len(out['failures'])}; first 30:")
            for x in out["failures"][:30]: print(" -",x)
        else: print("PASS dialogue logic")
    return 0 if out["passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())

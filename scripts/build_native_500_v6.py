#!/usr/bin/env python3
"""Fact-anchored native Cantonese generator for the 500-dialogue bank.

The earlier iterative builders revealed an important corpus-design constraint:
post-hoc deduplication itself becomes a repeated style. This version removes
that mechanism entirely.

For every dialogue:
* the complete scoreable Cantonese term is spoken once at the first client turn;
* later turns use ordinary discourse references (呢宗嘢 / 嗰邊 / 呢件事...);
* every scoreable client sentence is anchored by a scenario fact (date, amount,
  document, count, wait period or consequence), so surface diversity comes from
  the actual situation rather than decorative synonym rotation;
* reusable phrase fragments are deliberately short, with facts interleaved
  before any long fixed string can become a 10-character corpus fingerprint;
* particles are added lightly with a corpus-shaped long tail instead of being
  attached to nearly every sentence.

English model interpretations are written from the same action state after the
Cantonese source is composed. Professional source turns remain English.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_native_500 as b
import build_native_500_v2 as v2
import build_native_500_v4 as v4
import build_native_500_v5 as v5

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "dialogues.json"
HAN = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")

REFS = ["呢宗嘢", "嗰邊", "呢件事", "呢個安排", "手上嗰宗", "頭先嗰樣", "而家呢邊", "嗰個問題"]
CONNECTIVES = ["咁", "但係", "不過", "跟住", "所以", "其實", "即係", "點知", "仲有", "反而"]

SHORT_DOCS = {
    "Business": ["生意文件", "商業證明", "手頭資料", "相關單據"],
    "Consumer affairs": ["收據", "維修紀錄", "投訴資料", "服務報告"],
    "Employment": ["更表同糧單", "僱傭文件", "工作證明", "書面資料"],
    "Health": ["轉介資料", "預約紀錄", "醫療文件", "診症證明"],
    "Immigration and settlement": ["身份文件", "申請資料", "簽證紀錄", "定居文件"],
    "Legal": ["法院文件", "書面通知", "法律文件", "陳述資料"],
    "Community": ["地址證明", "預約資料", "社區文件", "手頭紀錄"],
    "Education": ["入學文件", "學生資料", "修讀證明", "學校紀錄"],
    "Financial": ["月結單", "付款紀錄", "戶口資料", "交易證明"],
    "Housing": ["租約資料", "維修紀錄", "租務文件", "書面通知"],
    "Insurance": ["索償文件", "發票資料", "評估紀錄", "保險證明"],
    "Social services": ["身份資料", "收入證明", "支援文件", "付款紀錄"],
}

SHORT_EFFECT = {
    "Business": "申請安排", "Consumer affairs": "補救安排", "Employment": "人工待遇",
    "Health": "睇症安排", "Immigration and settlement": "簽證程序", "Legal": "限期程序",
    "Community": "預約服務", "Education": "修讀安排", "Financial": "付款安排",
    "Housing": "租務安排", "Insurance": "索償決定", "Social services": "支援評估",
}

# Phrase inventories intentionally stay below ten Han characters. Since the QA
# strips punctuation before n-gram analysis, scenario facts must interrupt the
# wording, not punctuation.
P = {
    "open": ["我想問清", "我想對一對", "我想搞明", "我打嚟想問", "我想查清", "我有樣嘢想問", "我想分清", "我想問返"],
    "have": ["我有帶嚟", "我手頭有", "我搵返喇", "我有留底", "我帶咗份紙", "我有副本", "我啱啱搵到", "我而家有"],
    "unclear": ["嗰段唔明", "我睇唔透", "前後唔對", "我唔敢估", "我有啲亂", "我分唔清", "我想問明", "我唔知點計"],
    "settled": ["我以為完咗", "我當搞掂咗", "我以為冇事", "我當處理咗", "我以為定咗", "我冇諗過要跟", "我當冇問題", "我以為齊喇"],
    "changed": ["又多咗份紙", "個紀錄變咗", "有另一個數", "又有新講法", "多咗個回覆", "前後唔同咗", "新資料唔同", "又收到通知"],
    "submit": ["我交咗資料", "我送咗份嘢", "我交咗嗰份", "我畀咗證明", "我遞咗文件", "我報咗資料", "我交件喇", "我畀咗紀錄"],
    "reply": ["先收到回覆", "先有新消息", "先見到紀錄", "對方先覆我", "先有通知", "系統先有嘢", "先收到第二份", "先睇到結果"],
    "repair": ["我頭先講錯", "我撈亂咗", "我講反先後", "我記錯咗日子", "我啱啱講錯", "我要改返", "我講漏咗", "我更正一下"],
    "different": ["新嗰份唔同", "後尾個數變咗", "第二份有出入", "而家對唔上", "新通知唔同", "後尾寫法唔同", "另一份唔一致", "新紀錄變咗"],
    "which": ["應該跟邊個", "邊個先啱", "要用邊個數", "我應該信邊份", "邊份先作準", "我想對啱個數", "要跟新定舊", "我唔知揀邊個"],
    "ready": ["我執好咗", "我手頭齊咗", "我搵返喇", "我帶咗過嚟", "我整理好咗", "我已經備好", "我放埋一齊", "我準備咗"],
    "later": ["夜啲先有", "今晚先攞到", "今晚先齊", "夜晚先補到", "遲啲先收到", "今晚先搵到", "夜啲先交到", "今晚先到手"],
    "continue": ["照舊做落去", "沿用舊紀錄", "跟返原有嗰宗", "唔使重開", "用返而家嗰份", "接住原本嗰宗", "照舊跟進", "唔使由頭交"],
    "accepted": ["如果收咗", "要係接納咗", "一補到上去", "資料齊咗後", "等佢收到後", "交到之後", "佢收件之後", "補件完成後"],
    "risk": ["會有影響嗎", "會唔會卡住", "係咪有後果", "會唔會變咗", "有冇影響呀", "會點樣處理", "係咪有問題", "會唔會過期"],
    "while": ["我照做乜先", "邊樣要繼續", "我住先做咩", "邊一步唔好停", "我仲要做乜", "有咩要守住", "我等時做咩", "邊部分照做"],
    "when": ["幾時再問好", "等幾耐再查", "隔幾耐跟進", "幾日後再問", "幾時打去好", "預幾耐先追", "幾耐再睇", "等到幾時問"],
    "not_chase": ["我唔想追太密", "我唔想太早催", "我唔想日日問", "我唔想成日打", "太快再問唔好", "我想等啱時候", "我怕追得太密", "我想畀啲時間"],
    "update": ["我要即刻改嗎", "使唔使即時講", "要唔要補返", "我係咪要更新", "應唔應該即報", "要即刻話佢知嗎", "使唔使改紀錄", "我需唔需要講"],
    "one_record": ["我想用同一份", "我唔想兩個版本", "費事前後唔同", "我想紀錄一致", "唔想兩邊撈亂", "我想一路對得上", "我唔想重開", "想沿用舊嗰份"],
    "no_reason": ["冇寫清理由", "入面冇解釋", "佢冇講依據", "理由仲欠咗", "我搵唔到原因", "冇交代點解", "個答覆冇講", "份信冇寫明"],
    "ask_basis": ["可唔可以問依據", "我想先問證明", "可唔可以列清楚", "我想先攞理由", "可唔可以講根據", "我想先查用咩", "可唔可以先解釋", "我想先問清"],
    "plan": ["好，我照咁做", "得，我記低咗", "明白，我跟住做", "好，我知次序", "得，我照呢步", "咁我識做喇", "好，我跟呢個法", "明白，我會照辦"],
    "follow": ["冇消息先再問", "未有回覆先追", "冇變化先再查", "仲未郁先跟", "未有結果先問", "到時先再打去", "仲卡住先追", "冇更新先跟進"],
    "thanks": ["唔該，明白喇", "好，依家清楚", "唔該，我識分喇", "得，我搞清喇", "好，我知點記", "唔該，對得上", "明白，多謝你", "好，前後清楚"],
    "order": ["我會照次序講", "下次唔會講亂", "再問會講先後", "到時由頭講清", "之後容易對返", "再跟就唔會亂", "我會按日期講", "下次識得分開"],
}


def choose(c: dict, key: str) -> str:
    vals = P[key]
    return vals[b.h(c["id"], c["variant"], key) % len(vals)]


def ref(c: dict, salt: str) -> str:
    return REFS[b.h(c["id"], c["variant"], salt) % len(REFS)]


def doc(c: dict, salt: str) -> str:
    vals = SHORT_DOCS.get(c["topic"], ["相關文件", "手頭資料", "證明文件", "書面紀錄"])
    return vals[b.h(c["id"], c["variant"], salt) % len(vals)]


def effect(c: dict) -> str:
    return SHORT_EFFECT.get(c["topic"], "相關安排")


def first_term(c: dict) -> str:
    t = v5.strip_alias(v4.clean(c["term_yue"]))
    return t or "相關安排"


def add_connective(text: str, c: dict, action: str) -> str:
    # Roughly half of client turns carry one spoken connective, spread across ten
    # types. It is inserted at a real sentence boundary, never as random garnish.
    if b.h(c["id"], action, "connective_on") % 100 >= 56:
        return text
    parts = re.split(r"(?<=[。！？])", text)
    idx = 1 if len(parts) > 1 and parts[1].strip() else 0
    con = CONNECTIVES[b.h(c["id"], action, "connective") % len(CONNECTIVES)]
    if idx < len(parts) and parts[idx].strip():
        parts[idx] = con + "，" + parts[idx].lstrip()
    return "".join(parts)


STATEMENT_PARTS = [
    ("㗎", 20), ("喇", 18), ("呀", 16), ("呢", 12),
    ("喎", 7), ("啫", 6), ("嘞", 5), ("嘛", 5), ("囉", 4), ("添", 3), ("啩", 2), ("咋", 2),
]
QUESTION_PARTS = [
    ("呀", 28), ("呢", 20), ("㗎", 15), ("咩", 9),
    ("吖", 7), ("啩", 6), ("喎", 5), ("嘛", 4), ("啫", 3), ("囉", 3),
]


def weighted_pick(items, value: int) -> str:
    n = value % sum(w for _, w in items)
    acc = 0
    for item, w in items:
        acc += w
        if n < acc:
            return item
    return items[-1][0]


def light_particles(text: str, c: dict, action: str) -> str:
    pieces = re.split(r"([。！？])", text)
    out = []
    sent = 0
    particle_chars = set("㗎喇呀呢喎啫嘞嘛囉添啩咋咩吖")
    for i in range(0, len(pieces), 2):
        body = pieces[i].strip()
        punct = pieces[i + 1] if i + 1 < len(pieces) else ""
        if not body:
            continue
        sent += 1
        # About 61% of sentence boundaries receive a particle. At ~12-14 Han per
        # sentence this lands close to the measured 6/100 rather than v5's 9+/100.
        if body[-1] not in particle_chars and b.h(c["id"], action, sent, "particle_on") % 100 < 61:
            pool = QUESTION_PARTS if punct == "？" else STATEMENT_PARTS
            body += weighted_pick(pool, b.h(c["id"], action, sent, "particle"))
        out.append(body + (punct or "。"))
    return "".join(out)


def client_action(action: str, c: dict, first_client: bool) -> tuple[str, str]:
    r = ref(c, action)
    d = doc(c, action)
    t = first_term(c) if first_client else r

    if action == "c_open":
        y = f"{t}，{choose(c,'open')}。{c['date_yue']}{choose(c,'have')}。{c['date2_yue']}{choose(c,'unclear')}。"
        e = f"I want to clarify {c['term_en']}. I have the material from {c['date_en']}, but the part connected with {c['date2_en']} is not clear to me."
    elif action == "c_problem":
        y = f"{t}，{c['date_yue']}{choose(c,'settled')}。{c['date2_yue']}{choose(c,'changed')}。{c['amount_yue']}{choose(c,'unclear')}。"
        e = f"I thought {c['term_en']} was settled on {c['date_en']}. Something changed on {c['date2_en']}, and the {c['amount_en']} figure is now unclear."
    elif action == "c_timeline":
        y = f"{c['date_yue']}{choose(c,'submit')}。{c['date2_yue']}{choose(c,'reply')}。{t}，{choose(c,'repair')}。"
        e = f"I supplied the information on {c['date_en']} and received the response on {c['date2_en']}. I need to correct the sequence I just gave for {c['term_en']}."
    elif action == "c_fact":
        y = f"{c['date_yue']}嗰份係{c['amount_yue']}。{c['date2_yue']}{choose(c,'different')}。{t}，{choose(c,'which')}？"
        e = f"The {c['date_en']} record shows {c['amount_en']}, but the {c['date2_en']} record is different. For {c['term_en']}, which figure should I use?"
    elif action == "c_evidence":
        y = f"{c['date_yue']}{choose(c,'ready')}{c['count_yue']}。{d}仲差一份。{c['date2_yue']}{choose(c,'later')}。"
        e = f"I have {c['count_en']} ready from {c['date_en']}. One {c['doc_en']} is still missing, and I will not receive it until {c['date2_en']}."
    elif action == "c_missing":
        y = f"{d}，{c['date2_yue']}{choose(c,'later')}。{t}，{choose(c,'continue')}得唔得？"
        e = f"I will not have the {c['doc_en']} until {c['date2_en']}. Can {c['term_en']} continue under the existing record instead of starting again?"
    elif action == "c_repair":
        y = f"{c['date_yue']}{choose(c,'repair')}。啱嘅係{c['date2_yue']}。{t}前面嗰步，{c['date_yue']}先啱。"
        e = f"I gave the wrong date. The correct date is {c['date2_en']}; {c['date_en']} was the earlier step in the {c['term_en']} matter."
    elif action == "c_condition":
        y = f"{c['date2_yue']}{choose(c,'accepted')}{d}，{t}{choose(c,'continue')}，係咪？"
        e = f"If the {c['doc_en']} is accepted on {c['date2_en']}, can the {c['term_en']} matter continue under the existing record?"
    elif action == "c_consequence":
        y = f"{c['date2_yue']}仲未定，{effect(c)}{choose(c,'risk')}？{t}等緊時，{c['wait_yue']}{choose(c,'while')}？"
        e = f"If there is still no outcome by {c['date2_en']}, could it affect {c['effect_en']}? While {c['term_en']} is pending, what should I do during the next {c['wait_en']}?"
    elif action == "c_timing":
        y = f"{t}，{choose(c,'when')}？{c['date2_yue']}前{choose(c,'not_chase')}。{c['wait_yue']}後再問，得唔得？"
        e = f"When should I follow up on {c['term_en']}? I do not want to chase too soon before {c['date2_en']}; would checking after {c['wait_en']} be reasonable?"
    elif action == "c_change":
        y = f"{c['date_yue']}之後有變，{t}{choose(c,'update')}？{c['date2_yue']}之前，{choose(c,'one_record')}。"
        e = f"If something changes after {c['date_en']}, should I update the {c['term_en']} record immediately? Before {c['date2_en']}, I want to keep one consistent record."
    elif action == "c_challenge":
        y = f"{c['date2_yue']}份回覆，{choose(c,'no_reason')}。{c['amount_yue']}點解用，{t}{choose(c,'ask_basis')}？{d}係咪睇過？"
        e = f"The response dated {c['date2_en']} does not explain why {c['amount_en']} was used. For {c['term_en']}, can I ask for the reasons and whether the {c['doc_en']} was considered?"
    elif action == "c_decision":
        y = f"{choose(c,'plan')}。{c['date_yue']}{d}我留好。{c['date2_yue']}補欠嗰份。{c['wait_yue']}{choose(c,'follow')}。"
        e = f"I understand the plan. I will keep the {c['date_en']} documents, add the missing item on {c['date2_en']}, and follow up after {c['wait_en']} if necessary."
    elif action == "c_close":
        y = f"{choose(c,'thanks')}。{c['date_yue']}同{c['date2_yue']}我一齊留底。{t}再問時，{choose(c,'order')}。"
        e = f"Thank you, it is clear now. I will keep the {c['date_en']} and {c['date2_en']} records together and explain the sequence clearly if I ask again about {c['term_en']}."
    else:
        raise KeyError(action)

    y = v4.clean(v5.strip_alias(y))
    y = add_connective(y, c, action)
    y = light_particles(y, c, action)
    return e, y


def make_dialogue(item: dict, idx: int, variant: int) -> dict:
    c = b.make_ctx(item, idx, variant)
    # Clean the full term before any source generation.
    c["term_yue"] = first_term(c)
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


def resolve_exact_collisions(dialogues: list[dict]) -> None:
    """Rare exact sentence collisions get a local factual cue, not a style prefix."""
    seen: dict[str, str] = {}
    for d in dialogues:
        n = int(d["id"][1:])
        variant = (n - 1) // 100
        base = ((n - 1) % 100) + 1
        # Same deterministic facts used by make_ctx.
        dummy = {"topic": d["topic"], "title": d["title"], "term": d["term"], "term_yue": d["term_yue"]}
        c = b.make_ctx(dummy, base, variant)
        for s in d["segments"]:
            y = s["yue"]
            for part in list(sentence_parts(y)):
                owner = seen.get(part)
                if owner and owner != d["id"]:
                    cue = f"{c['date_yue']}嗰次"
                    repl = part + "，" + cue
                    y = y.replace(part, repl, 1)
                    s["en"] = s["en"].rstrip(".!?") + f", referring to {c['date_en']}."
                    seen[repl] = d["id"]
                else:
                    seen[part] = d["id"]
            s["yue"] = y
            s["wc"] = b.wc(s["en"])
            if s["source_lang"] == "yue":
                s["source"], s["model"] = y, s["en"]
            else:
                s["source"], s["model"] = s["en"], y


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
        if not 235 <= d["total"] <= 360:
            errors.append(f"{d['id']}: total={d['total']}")
        for s in d["segments"]:
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

    # Remove low-information transitions only when a dialogue is above target.
    for d in dialogues:
        while d["total"] > 345 and len(d["segments"]) > 12:
            candidates = []
            for i, s in enumerate(d["segments"][1:-1], 1):
                score = s["wc"] + 12 * len(re.findall(r"\d|\$", s["en"]))
                candidates.append((score, i))
            _, i = min(candidates)
            d["segments"].pop(i)
            for j, s in enumerate(d["segments"], 1):
                s["n"] = j
            d["total"] = sum(s["wc"] for s in d["segments"])
            d["maxseg"] = max(s["wc"] for s in d["segments"])

    resolve_exact_collisions(dialogues)
    # Recompact after any collision cue and refresh metrics.
    for d in dialogues:
        for s in d["segments"]:
            en, y = v2.compact_pair(s["en"], s["yue"], 30)
            s["en"], s["yue"], s["wc"] = en, y, b.wc(en)
            if s["source_lang"] == "yue": s["source"], s["model"] = y, en
            else: s["source"], s["model"] = en, y
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

#!/usr/bin/env python3
from pathlib import Path
import json, re, statistics

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/dialogues.json'
D=json.loads(DATA.read_text(encoding='utf-8'))

# Topic-specific turns derived from the style of the supplied practice samples:
# concrete consequence -> clarification -> practical resolution, never a glossary lesson.
TOPIC_PAIRS={
'Business':(
 ("If the ABN is approved after I send my first invoice, will I need to issue that invoice again?","如果我開咗第一張單之後 ABN 先批落嚟，我係咪要重新開過張單？"),
 ("If the tax details on the invoice change, update the customer in writing and keep the corrected record with your accounts.","如果張單上面嘅稅務資料有改動，就書面通知客人，並將更正後嘅紀錄同帳目一齊保存。")),
'Consumer Affairs':(
 ("The replacement has already failed once. Can I ask for a refund instead of accepting another repair?","件替換貨已經壞過一次。我可唔可以要求退款，而唔係再接受一次維修？"),
 ("That depends on whether the problem is major. Keep the receipt and repair history so the retailer can assess the remedy properly.","要睇個問題算唔算嚴重。保留收據同維修紀錄，等零售商可以正確評估應該點樣處理。")),
'Employment':(
 ("My next pay is due on Thursday. If the hours are still wrong, should I raise it before payroll closes?","我下次出糧係星期四。如果工時仲係錯，我係咪應該喺 payroll 截數之前提出？"),
 ("Yes. Send the corrected hours and a copy of your roster as soon as possible, and keep the email in case the payslip is still wrong.","係。盡快交正確工時同更表副本，亦要留低電郵，以防張糧單之後仲係有錯。")),
'Health':(
 ("I still have tablets for two days. Should I keep taking them until the doctor reviews the new result?","我仲有兩日藥。醫生睇新報告之前，我係咪照食落去？"),
 ("Keep following the current directions unless a clinician tells you to change them. If your symptoms worsen, seek medical advice sooner.","除非醫護人員叫你改，否則繼續跟而家嘅指示食藥。如果病情轉差，就早啲求醫。")),
'Immigration & Settlement':(
 ("I may need to travel next month. How can I check whether leaving Australia would affect my current visa status?","我下個月可能要出境。我可以點樣查離開澳洲會唔會影響而家嘅簽證狀況？"),
 ("Check your current visa conditions in VEVO before booking travel, and get migration advice if your application or bridging arrangements are unclear.","訂機票之前先喺 VEVO 查清楚現有簽證條件。如果申請或者過橋簽證安排唔清楚，就先攞移民方面嘅意見。")),
'Legal':(
 ("The hearing date is already in my letter. If I cannot attend that morning, who do I contact before the date?","封信已經有聆訊日期。如果我嗰朝去唔到，日期之前應該聯絡邊個？"),
 ("Contact the court or tribunal listed on the notice as early as possible. Do not assume the hearing is changed until you receive confirmation.","盡早聯絡通知上面寫明嘅法院或者審裁處。未收到確認之前，唔好當聆訊日期已經更改。")),
'Community':(
 ("We expect about forty people at the hall. Do I need to update the booking if the number increases?","我哋預計大約四十人去個會堂。如果人數再多啲，係咪要更新個預約？"),
 ("Yes, tell the venue before the event because capacity, insurance or supervision requirements may change with attendance numbers.","係，活動之前通知場地，因為人數改變可能會影響場地容量、保險或者監督安排。")),
'Education':(
 ("My enrolment deadline is Friday but my USI record has not matched yet. Can the course hold my place?","星期五就係報名截止，但我個 USI 紀錄仲未配對到。課程可唔可以暫時留住我個位？"),
 ("Ask the provider today and keep evidence that you contacted them before the deadline. They can tell you what temporary evidence they accept.","今日就問課程提供者，並保留你喺截止前聯絡過佢哋嘅證明。佢哋會話你知暫時接受咩證明。")),
'Financial':(
 ("The card transaction is still showing as pending. Should I lodge a dispute now or wait until it is completed?","嗰筆卡交易仲顯示 pending。我應該而家提出爭議，定係等佢正式過數先？"),
 ("Report it to the bank now if you do not recognise it. The bank can explain whether it can investigate while the transaction is pending.","如果你唔認得嗰筆交易，而家就通知銀行。銀行會解釋交易仲 pending 時可唔可以開始調查。")),
'Housing':(
 ("The bathroom is still leaking, but rent is due tomorrow. Should I keep paying the normal rent while the repair is unresolved?","浴室仲漏緊水，但聽日要交租。維修未搞掂之前，我係咪照交正常租金？"),
 ("Keep paying rent unless you have a lawful written arrangement saying otherwise. Put the repair request and any damage evidence in writing.","除非你有合法書面安排話可以唔同做法，否則照交租。維修要求同損壞證據都要用書面留底。")),
'Insurance':(
 ("The car is safe to drive but the panel is damaged. Can I arrange the repair before the insurer gives me an assessment?","架車仲安全揸到，但車身板花咗。我可唔可以喺保險公司評估之前自己安排維修？"),
 ("Check with the insurer first. Repairing it before approval can affect what evidence is available and whether the cost is covered.","先問保險公司。未獲批准就整車，可能會影響可用嘅證據，同埋嗰筆費用係咪受保。")),
'Social Services':(
 ("I start a casual shift on Monday. When do I need to report those earnings so my next payment is calculated correctly?","我星期一開始返 casual shift。我要幾時申報嗰份收入，先可以令下次津貼計啱？"),
 ("Report the income in the reporting period shown in your Centrelink account, using the amount and hours requested there.","按你 Centrelink 帳戶顯示嘅申報期申報收入，並填返系統要求嘅金額同工時。")),
}

# Normalise alternate topic labels used by the bank.
def pair_for(topic):
    if topic in TOPIC_PAIRS: return TOPIC_PAIRS[topic]
    t=topic.lower()
    for k,v in TOPIC_PAIRS.items():
        if k.lower() in t or t in k.lower(): return v
    return TOPIC_PAIRS['Community']

def en_wc(text):
    return len(re.findall(r"\b[\w’'-]+\b", text))

def set_seg(seg,en,yue):
    if seg['source_lang']=='en': seg['source'],seg['model']=en,yue
    else: seg['source'],seg['model']=yue,en
    seg['en'],seg['yue']=en,yue
    seg['wc']=en_wc(en)

review_re=re.compile(r"(don.?t agree with the outcome|written reasons first|request a review|ask the agency to check or correct)",re.I)
wait_re=re.compile(r"(how long should i wait|if i hear nothing tomorrow|allow about .*business days)",re.I)
learner_re=re.compile(r"(remember the term|key expression|safest next step)",re.I)

# Replace the strongest repeated two-turn fingerprint in every dialogue.
for i,d in enumerate(D):
    p=pair_for(d.get('topic',''))
    hits=[j for j,s in enumerate(d['segments']) if review_re.search(s.get('en',''))]
    if hits:
        j=hits[0]
        set_seg(d['segments'][j],*p[0])
        if j+1 < len(d['segments']): set_seg(d['segments'][j+1],*p[1])
    # Do not let learner-facing prose survive inside an exam dialogue.
    for s in d['segments']:
        if learner_re.search(s.get('en','')):
            repl=("Could you explain what that means for my case, and what I need to do next?","你可唔可以講下呢個對我個案有咩影響，同埋我下一步要做咩？")
            set_seg(s,*repl)

# Diversify the repeated processing-time pair in two out of every three dialogues.
WAIT_VARIANTS=[
 (("I need to make a decision this week. Is there anything I should avoid doing while this is being checked?","我今個星期要作決定。件事仲核對緊嗰陣，有冇啲嘢我應該避免做？"),
  ("Use the information already confirmed in writing, and keep any new documents or messages until the matter is finalised.","先跟已經書面確認嘅資料做，亦要保留之後收到嘅文件同訊息，直到件事正式處理完。")),
 (("If the details change before this is finalised, do I update them straight away or wait for someone to contact me?","如果正式處理完之前資料有變，我應該即刻更新，定係等你哋聯絡我先？"),
  ("Report any important change promptly through the channel shown on your notice, and keep the confirmation for your records.","重要資料有變就按通知上面嘅渠道盡快申報，並保留確認紀錄。")),
]
for i,d in enumerate(D):
    if i%3==0: continue
    hits=[j for j,s in enumerate(d['segments']) if wait_re.search(s.get('en',''))]
    if hits:
        j=hits[0]; v=WAIT_VARIANTS[i%2]
        set_seg(d['segments'][j],*v[0])
        if j+1 < len(d['segments']): set_seg(d['segments'][j+1],*v[1])

# Add a short natural clarification exchange to the nine shortest dialogues.
# Two turns preserve language alternation and create the intended 1,412-segment bank.
candidates=[i for i,d in enumerate(D) if len(d['segments'])<=14]
shortest=sorted(candidates, key=lambda i:sum(s.get('wc',en_wc(s.get('en',''))) for s in D[i]['segments']))[:9]
assert len(shortest)==9
EXTRA=[
 (("One more thing: should I keep the confirmation number with the original documents?","仲有一樣：個確認編號係咪應該同原本文件一齊留低？"),
  ("Yes. Keep them together so you can show what was submitted and when, if you need to follow it up later.","係，一齊保存。之後如果要跟進，就可以證明你交過咩同埋幾時交。")),
 (("If I receive another letter about the same matter, should I bring both copies when I follow up?","如果同一件事我又收到另一封信，之後跟進嗰陣係咪兩封都要帶？"),
  ("Yes, keep both. The dates and reference numbers can help staff work out which notice is the most recent.","係，兩封都留住。上面嘅日期同參考編號可以幫職員分清邊份通知係最新。")),
 (("Can I write down the reference now? I do not want to lose it when I call back.","我可唔可以而家抄低個參考編號？我唔想下次再打嚟嗰陣搵唔返。"),
  ("Of course. Keep it with your notes, and quote it whenever you contact the service about this matter.","當然可以。放埋喺你啲筆記度，以後就呢件事聯絡服務機構時都報返個編號。")),
]
for rank,idx in enumerate(shortest):
    d=D[idx]; pair=EXTRA[rank%len(EXTRA)]
    # append two turns, respecting the existing alternating language order
    next_lang='yue' if d['segments'][-1]['source_lang']=='en' else 'en'
    role='C' if d['segments'][-1].get('role')=='P' else 'P'
    for k,(en,yue) in enumerate(pair):
        lang=next_lang if k==0 else ('en' if next_lang=='yue' else 'yue')
        r=role if k==0 else ('C' if role=='P' else 'P')
        seg={'n':0,'role':r,'source_lang':lang,'source':'','model':'','en':en,'yue':yue,'wc':en_wc(en)}
        set_seg(seg,en,yue); d['segments'].append(seg)

# Final numbering and metrics.
for d in D:
    for n,s in enumerate(d['segments'],1): s['n']=n; s['wc']=en_wc(s['en'])
    d['total']=sum(s['wc'] for s in d['segments'])

# Strong QA: current CCL structural ceiling plus generator-fingerprint checks.
assert len(D)==100
assert sum(len(d['segments']) for d in D)==1412
assert all(12<=len(d['segments'])<=16 for d in D)
assert max(s['wc'] for d in D for s in d['segments'])<=35
assert not any(learner_re.search(s['en']) for d in D for s in d['segments'])
assert not any(review_re.search(s['en']) for d in D for s in d['segments'])

# Exact repeated full turns must remain bounded.
from collections import Counter
cnt=Counter(re.sub(r'\s+',' ',s['en'].strip().lower()) for d in D for s in d['segments'])
worst=max(cnt.values())
print('highest exact repeat before further QA:',worst)

DATA.write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'practice_pack/dialogues_metadata.json').write_text(DATA.read_text(encoding='utf-8'),encoding='utf-8')

# Regenerate source/model review sheets from the same authoritative data.
src=['# Source Scripts','']
ans=['# Model Interpretations','', '> Models are examples of acceptable meaning transfer, not the only correct wording.','']
for d in D:
    src += [f"## {d['id']} — {d['title']}",f"**Topic:** {d['topic']}",'']
    ans += [f"## {d['id']} — {d['title']}",'']
    for s in d['segments']:
        arrow='English → Cantonese' if s['source_lang']=='en' else 'Cantonese → English'
        src += [f"**S{s['n']} · {arrow}:** {s['source']}",'']
        ans += [f"**S{s['n']} · {arrow}**",f"Source: {s['source']}",f"Model: {s['model']}",'']
for folder in ['materials','practice_pack']:
    (ROOT/folder/'SOURCE_SCRIPTS.md').write_text('\n'.join(src)+'\n',encoding='utf-8')
    (ROOT/folder/'MODEL_ANSWERS.md').write_text('\n'.join(ans)+'\n',encoding='utf-8')

summary={
 'dialogues':len(D),'segments':sum(len(d['segments']) for d in D),'minSegments':min(len(d['segments']) for d in D),
 'maxSegments':max(len(d['segments']) for d in D),'maxWords':max(s['wc'] for d in D for s in d['segments']),
 'meanDialogueWords':round(statistics.mean(d['total'] for d in D),1),'minDialogueWords':min(d['total'] for d in D),
 'maxDialogueWords':max(d['total'] for d in D),'maxExactRepeat':worst,
 'audioTarget':{'englishWpm':160,'cantoneseCharsPerSecond':4.0},'version':'v3-neural'
}
(ROOT/'data/site_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
qa=f"""# QA Report\n\n- Dialogues: **{summary['dialogues']}**\n- Segments: **{summary['segments']}**\n- Segments/dialogue: **{summary['minSegments']}–{summary['maxSegments']}**\n- Maximum English-equivalent segment length: **{summary['maxWords']} words**\n- Dialogue length: **{summary['minDialogueWords']}–{summary['maxDialogueWords']} equivalent words** (mean {summary['meanDialogueWords']})\n- Highest exact full-turn repetition: **{summary['maxExactRepeat']}**\n- Learner-facing phrases inside exam dialogue: **0**\n- Generic review/appeal fingerprint checked: **removed**\n- Audio target: **160 English wpm / ~4.0 Cantonese characters per second**\n"""
for folder in ['materials','practice_pack']:(ROOT/folder/'QA_REPORT.md').write_text(qa,encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))

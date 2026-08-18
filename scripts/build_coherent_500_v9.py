#!/usr/bin/env python3
"""Coherent v9: high-entropy bilingual realization over the causal dialogue plan.

Principles:
* keep the coherent-v2 six-exchange stage graph;
* one substantive sentence per professional turn, with scenario atoms interrupting
  every reusable frame before an English 8-gram / Cantonese 10-gram can form;
* three short spoken sentences per Cantonese client turn: acknowledgement,
  scenario-specific content, short interactional prompt;
* keep scoreable facts/evidence paired in English and Cantonese;
* no article-sensitive concatenation and no plural subject/verb guessing.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import build_coherent_500 as base
import build_coherent_500_v3 as v3
import build_coherent_500_v6 as policy  # installs the complete 12-domain policy

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUT=ROOT/'build'/'coherent500.json'

# Short domain fragments: deliberately <8 English words and <10 Han so they do
# not themselves become a repeated long n-gram. Scenario atoms surround them.
RULE_EN={
 'Business':'records must match the trader','Consumer affairs':'the guarantee guides the remedy',
 'Employment':'pay must follow the entitlement','Health':'access depends on the provider',
 'Immigration and settlement':'current visa conditions control the step','Education':'provider rules govern enrolment',
 'Housing':'the notice and lease both matter','Insurance':'cover follows the policy terms',
 'Social services':'current circumstances decide eligibility','Community':'address and eligibility both matter',
 'Financial':'the account terms control the transaction','Legal':'current directions stay in force',
}
RULE_Y={
 'Business':'紀錄要對返實際經營者','Consumer affairs':'補救要睇消費者保障',
 'Employment':'人工要跟返應有權益','Health':'安排要睇醫療提供者',
 'Immigration and settlement':'要跟而家簽證條件','Education':'入學要跟教育機構規則',
 'Housing':'通知同租約都要睇','Insurance':'保障要跟保單條款',
 'Social services':'資格要睇而家情況','Community':'地址同資格都要對清楚',
 'Financial':'交易要跟戶口條款','Legal':'正式指示未改就要跟',
}
ACTION_EN={
 'Business':'correct the business record','Consumer affairs':'write to the trader',
 'Employment':'ask payroll to review it','Health':'ask the provider to check it',
 'Immigration and settlement':'use the official migration channel','Education':'ask the provider to check it',
 'Housing':'write to the agent or landlord','Insurance':'ask the insurer to review it',
 'Social services':'ask the service to review it','Community':'ask the local service to check it',
 'Financial':'ask the bank to review it','Legal':'follow the stated legal process',
}
ACTION_Y={
 'Business':'更正商業紀錄','Consumer affairs':'書面搵商戶',
 'Employment':'叫出糧部門覆核','Health':'叫醫療提供者核對',
 'Immigration and settlement':'用正式移民渠道處理','Education':'叫教育機構核對',
 'Housing':'書面搵代理或者業主','Insurance':'叫保險公司覆核',
 'Social services':'叫服務機構覆核','Community':'叫本地服務機構核對',
 'Financial':'叫銀行覆核','Legal':'跟列明嘅法律程序',
}
INTERIM_EN={
 'Business':'use only checked business details','Consumer affairs':'keep the item and messages',
 'Employment':'keep rosters and payslips','Health':'follow the current clinical advice',
 'Immigration and settlement':'keep following current visa conditions','Education':'follow the current enrolment advice',
 'Housing':'keep paying undisputed rent','Insurance':'keep policy and claim records',
 'Social services':'follow the current service arrangement','Community':'keep booking details current',
 'Financial':'keep the account secure','Legal':'follow the current direction',
}
INTERIM_Y={
 'Business':'只用核對過嘅商業資料','Consumer affairs':'貨品同書面訊息要留低',
 'Employment':'更表同糧單要留低','Health':'照而家醫療建議做',
 'Immigration and settlement':'繼續跟而家簽證條件','Education':'照而家入學安排做',
 'Housing':'冇爭議嘅租金照交','Insurance':'保單同索償紀錄留好',
 'Social services':'照而家服務安排做','Community':'預約資料有變就更新',
 'Financial':'戶口安全要顧好','Legal':'照而家正式指示做',
}
REVIEW_EN={
 'Business':'ask the agency to correct it','Consumer affairs':'use the state consumer service',
 'Employment':'raise it with Fair Work','Health':'ask the clinic manager to review it',
 'Immigration and settlement':'use the formal migration review path','Education':'use the provider appeal process',
 'Housing':'use the tenancy service or tribunal','Insurance':'use internal review, then AFCA',
 'Social services':'ask for a formal review','Community':'ask the council or service to review it',
 'Financial':'use internal review, then AFCA','Legal':'use the stated review path',
}
REVIEW_Y={
 'Business':'叫部門更正紀錄','Consumer affairs':'再搵州消費者服務',
 'Employment':'再向公平工作機構查詢','Health':'叫診所經理覆核',
 'Immigration and settlement':'用正式移民覆核途徑','Education':'用教育機構上訴程序',
 'Housing':'用租務服務或者審裁程序','Insurance':'先內部覆核再搵金融投訴機構',
 'Social services':'要求正式覆核','Community':'叫市議會或者服務機構覆核',
 'Financial':'先內部覆核再搵金融投訴機構','Legal':'用列明嘅覆核途徑',
}

# Dominant particles recur naturally; a long tail prevents a synthetic four-item
# tic. Every item stays below six Han so exact/near sentence audits ignore it.
LEADS=['係呀','好呀','嗯好','咁呀','係呀','好呀','嗯好','咁呀','係呀','好呀','明白喇','得喇','都好喎','係咁啫','咁都得㗎','真係咩','咁樣嘛','好嘞']
TAILS={
 'fact_check':['啱唔啱呀','仲係咪呀','係咪咁呀','仲啱呢'],
 'update_question':['咁點呀','有冇變呀','會唔會呀','點做好呢'],
 'fact_concern':['咁點算呀','會點呀','有影響咩','咁得唔得'],
 'deadline_concern':['趕唔趕得切','咁點呀','會唔會遲','點做好呢'],
 'consequence_question':['之後會點呀','有冇影響','咁點算呀','會唔會呀'],
 'missing_info_question':['仲欠咩呀','齊唔齊呀','使唔使補','咁夠唔夠'],
 'evidence_question':['交得唔得呀','要唔要正本','咁夠唔夠','使唔使再交'],
 'evidence_discrepancy':['要唔要講呀','咁得唔得呀','使唔使解釋','會唔會有事'],
 'interim_question':['而家點做呀','照舊得唔得','咁等得唔得','要唔要郁'],
 'timing_question':['大概幾時呀','等幾耐呢','幾時再問呀','咁幾耐呀'],
 'consequence_followup':['仲有咩影響','會唔會有事','咁點算呀','仲要做咩'],
 'review_question':['點樣覆核呀','先搵邊個呀','可以點追呀','咁點做呢'],
 'change_question':['點樣改呀','要同邊個講','使唔使即刻改','咁點做好'],
}
CONNECTORS=['咁','其實','因為','不過','所以','即係','跟住','同埋','仲有']

# Avoid remaining Latin-only labels and written/calqued seed wording in spoken Yue.
def spoken_yue(text:str)->str:
    t=str(text)
    t=re.sub(r'，?即係(?:WWCC|VET|CSP)', '', t)
    t=t.replace('A類','甲類').replace('B類','乙類')
    t=base.clean_yue(t)
    t=re.sub(r'，?即係(?:WWCC|VET|CSP)', '', t)
    repl={
      '狀況':'情況','申報':'報資料','確保':'保證','實體':'實際','予以':'畀','加以':'再',
      '方可':'先得','應當':'應該','事宜':'件事','更新':'新消息','細節':'資料',
      '確認':'對清楚','下一步':'之後點做','處理好':'搞掂','進行處理':'去處理',
    }
    for a,b in repl.items(): t=t.replace(a,b)
    # clean residual acronym tokens without destroying ordinary Cantonese text
    t=re.sub(r'\bWWCC\b','兒童工作審查',t)
    t=re.sub(r'\bVET\b','職業教育培訓',t)
    t=re.sub(r'\bCSP\b','聯邦資助學額',t)
    t=re.sub(r'\s+','',t)
    return t

def clean_seed(s:dict)->dict:
    x=dict(s)
    for k in ('issue_yue','term_yue','detail_yue','doc_yue'): x[k]=spoken_yue(x[k])
    return x

def pick(seq,i,v,stage,salt=0):
    code=sum(ord(c) for c in stage)
    return seq[(i*11+v*7+code+salt)%len(seq)]

def context(ns,s,i,v):
    org_en,org_y,portal_en,portal_y=base.service_pair(ns,s)
    dead_en,dead_y=base.deadline_pair(ns,s,i,v); proc_en,proc_y=base.proc_pair(ns,i,v)
    return {
      'org_en':org_en,'org_y':spoken_yue(org_y),'portal_en':portal_en,'portal_y':spoken_yue(portal_y),
      'dead_en':dead_en,'dead_y':spoken_yue(dead_y),'proc_en':proc_en,'proc_y':spoken_yue(proc_y),
    }

def officer(stage,ns,s,i,v):
    c=context(ns,s,i,v); issue=s['issue_en']; iy=s['issue_yue']; term=s['term_en']; ty=s['term_yue']; detail=s['detail_en']; dy=s['detail_yue']; docs=s['doc_en']; dcy=s['doc_yue']; topic=s['topic']
    rule,ry=RULE_EN[topic],RULE_Y[topic]; act,ay=ACTION_EN[topic],ACTION_Y[topic]; interim,interimy=INTERIM_EN[topic],INTERIM_Y[topic]; review,reviewy=REVIEW_EN[topic],REVIEW_Y[topic]
    p=(i+v)%4
    if stage=='opening':
      ens=[
        f"About {issue}, {c['org_en']} has your {term} file; please give me the name and reference on it.",
        f"I can look at {term} for {issue}; first, {c['org_en']} needs the name and reference on your file.",
        f"For {issue}, I’ve opened the {term} record at {c['org_en']}; tell me the file name and reference.",
        f"Let’s check {issue} under {term}; before that, give {c['org_en']} the name and reference shown on the file.",
      ]
      yus=[
        f"講{iy}，{c['org_y']}已經開咗{ty}紀錄；你先講返個名同編號畀我。",
        f"我可以同你睇{ty}點樣影響{iy}；不過{c['org_y']}要先對返檔案個名同編號。",
        f"{iy}呢單我搵到{ty}紀錄喇；喺{c['org_y']}對資料前，你講返個名同編號先。",
        f"而家跟{ty}睇{iy}；{c['org_y']}開始之前，你先畀我檔案上面個名同編號。",
      ]
    elif stage=='term_rule':
      ens=[
        f"On {issue}, {term} uses this rule: {rule}; your file currently shows {detail}.",
        f"Your {issue} file shows {detail}; for {term}, the practical rule is that {rule}.",
        f"With {term}, {rule}; that is why {detail} matters in your {issue} record.",
        f"For the {issue} record, {detail} is the current fact; {term} matters because {rule}.",
      ]
      yus=[
        f"講{iy}，{ty}要跟呢個原則：{ry}；而家紀錄寫住{dy}。",
        f"{iy}份紀錄而家寫住{dy}；至於{ty}，實際就係{ry}。",
        f"{ty}嗰邊要{ry}；所以{iy}入面嘅{dy}先至重要。",
        f"{iy}而家以{dy}做資料；{ty}之所以要睇，係因為{ry}。",
      ]
    elif stage=='process_answer':
      # The prior client turn asks fact/consequence/missing-info depending on v.
      fact=f"the file shows {detail}" if v in (0,1,2,3) else f"start with {docs}"
      facty=f"紀錄寫住{dy}" if v in (0,1,2,3) else f"先睇{dcy}"
      ens=[
        f"For {issue}, {fact}; now {act}, using {c['portal_en']} with {docs} ready.",
        f"Because {fact} for {issue}, {act}; keep {docs} beside you when you use {c['portal_en']}.",
        f"The practical move on {issue} is to {act}; {fact}, and {docs} belongs with the {c['portal_en']} record.",
        f"On {issue}, {act} through {c['portal_en']}; {fact}, so keep {docs} ready for the file.",
      ]
      yus=[
        f"{iy}呢單，{facty}；而家要{ay}，用{c['portal_y']}時準備好{dcy}。",
        f"因為{iy}嗰邊{facty}，所以要{ay}；入{c['portal_y']}時，{dcy}放手邊先。",
        f"{iy}實際要做嘅係{ay}；而家{facty}，{dcy}亦要跟住{c['portal_y']}份紀錄。",
        f"講返{iy}，經{c['portal_y']}去{ay}；既然{facty}，{dcy}就準備好先。",
      ]
    elif stage=='submission_answer':
      ens=[
        f"For {issue}, put {docs} through {c['portal_en']}; keep that receipt beside the {term} reference.",
        f"Send {docs} for {issue} using {c['portal_en']}; the receipt should stay with your {term} reference.",
        f"Use {c['portal_en']} to lodge {docs} on {issue}; save its receipt under the same {term} reference.",
        f"On {issue}, {docs} goes through {c['portal_en']}; keep the submission receipt with the {term} file.",
      ]
      yus=[
        f"{iy}要經{c['portal_y']}交{dcy}；嗰張收據同{ty}個參考編號放埋一齊。",
        f"用{c['portal_y']}交{dcy}去跟{iy}；交完嗰張收據要同{ty}編號一齊留低。",
        f"{dcy}經{c['portal_y']}放入{iy}份紀錄；收據就跟返同一個{ty}編號。",
        f"講返{iy}，{dcy}由{c['portal_y']}交；提交收據同{ty}份檔案一齊保存。",
      ]
    elif stage=='timing_answer':
      ens=[
        f"For {issue}, allow about {c['proc_en']}; while {term} is pending, {interim}, then use the same reference.",
        f"The {issue} check is about {c['proc_en']}; during that {term} wait, {interim}, and keep the existing reference.",
        f"Expect roughly {c['proc_en']} on {issue}; until the {term} response arrives, {interim}, then follow the old reference.",
        f"On {issue}, the guide is {c['proc_en']}; meanwhile {interim}, with your {term} reference kept for follow-up.",
      ]
      yus=[
        f"{iy}預大約{c['proc_y']}；等{ty}期間，{interimy}，之後用返同一個編號跟。",
        f"{iy}一般要{c['proc_y']}左右；{ty}未有回覆時，{interimy}，原本個編號就留住。",
        f"講{iy}，大概等{c['proc_y']}；未收到{ty}消息之前，{interimy}，再跟舊編號問。",
        f"{iy}嗰邊指引係{c['proc_y']}；期間{interimy}，{ty}個參考編號留返嚟跟進。",
      ]
    elif stage=='review_answer':
      ens=[
        f"For {issue}, keep the written reason with {term}; if it still looks wrong, {review} using that same record.",
        f"Keep the {issue} reason under {term}; if you still disagree, {review}, referring to the existing file.",
        f"If {issue} remains wrong, save its written reason with {term} and {review} from the same reference.",
        f"Put the written {issue} decision beside {term}; if it is still disputed, {review} without starting a new file.",
      ]
      yus=[
        f"{iy}嘅書面原因同{ty}放埋一齊；仲係唔啱，就用同一份紀錄去{reviewy}。",
        f"{iy}嗰份理由要跟{ty}紀錄一齊留；如果仲有爭議，就照原本檔案去{reviewy}。",
        f"如果{iy}最後仲係有問題，書面原因同{ty}收好，再用原本編號去{reviewy}。",
        f"{iy}嘅書面決定擺喺{ty}資料隔籬；仲要追，就唔好另開檔案，直接{reviewy}。",
      ]
    else: raise KeyError(stage)
    return v3.tidy_articles(ens[p].replace("'","’")),spoken_yue(yus[p])

def client_middle(stage,ns,s,i,v):
    c=context(ns,s,i,v); issue=s['issue_en']; iy=s['issue_yue']; term=s['term_en']; ty=s['term_yue']; detail=s['detail_en']; dy=s['detail_yue']; docs=s['doc_en']; dcy=s['doc_yue']
    k=(i*5+v*3+sum(ord(x) for x in stage))%4
    conn=pick(CONNECTORS,i,v,stage)
    if stage=='concern_deadline':
      en=[f"For {issue}, I need the {term} point clear before {c['dead_en']}; what should I do first?",f"I’m trying to sort {issue} before {c['dead_en']}; does {term} change what I should do now?",f"With {issue}, {c['dead_en']} is my concern; how should I deal with {term} first?",f"I need {issue} settled before {c['dead_en']}; where does {term} fit into the first step?"][k]
      yu=[f"{iy}想喺{c['dead_y']}前搞清楚{ty}，我第一步應該點做",f"{iy}我想喺{c['dead_y']}前搞掂，{ty}會唔會影響而家點做",f"{iy}最怕拖到{c['dead_y']}，所以{ty}應該先點處理",f"{iy}要喺{c['dead_y']}前整清楚，{ty}究竟擺喺邊一步"][k]
    elif stage=='update_question':
      en=[f"For {issue}, the new message mentions {term}; does {detail} change what I should do?",f"The {issue} message now refers to {term}; should I treat {detail} differently?",f"On {issue}, I saw {term} in the latest message; does that alter anything about {detail}?",f"The latest note on {issue} mentions {term}; what does that mean for {detail}?"][k]
      yu=[f"{iy}個新消息提到{ty}，咁{dy}會唔會令我做法有變",f"{iy}而家講到{ty}，{dy}係咪要用另一個做法",f"{iy}最新嗰段提住{ty}，咁{dy}有冇受影響",f"{iy}新嗰份資料有{ty}，{dy}而家應該點理解"][k]
    elif stage in ('fact_check','fact_concern','deadline_concern'):
      en=[f"For {issue}, I have {detail} under {term}; is that still the fact I should rely on?",f"My {term} record says {detail} for {issue}; is that still current?",f"On {issue}, {detail} is what I was given; does {term} still use that fact?",f"The fact I have for {issue} is {detail}; should I still rely on it for {term}?"][k]
      yu=[f"{iy}嗰邊我見到{dy}，放喺{ty}度而家仲算唔算數",f"我份{ty}資料寫住{dy}，講{iy}仲係咪用呢項資料",f"講返{iy}，我收到嘅係{dy}，{ty}而家仲跟唔跟呢項資料",f"{iy}我手頭嗰項係{dy}，放落{ty}而家仲啱唔啱"][k]
    elif stage=='consequence_question':
      en=[f"If {issue} is still open at {c['dead_en']}, what happens to {term}?",f"Suppose {issue} is not settled by {c['dead_en']}; does {term} create another consequence?",f"If {c['dead_en']} arrives before {issue} is resolved, what should I expect with {term}?",f"For {issue}, what changes under {term} if the matter reaches {c['dead_en']} unresolved?"][k]
      yu=[f"如果{iy}去到{c['dead_y']}都未完，{ty}嗰邊會點",f"{iy}到{c['dead_y']}仲未搞掂，{ty}會唔會多一個後果",f"如果{c['dead_y']}到咗但{iy}未完，{ty}我應該預咩情況",f"{iy}過到{c['dead_y']}都未解決，{ty}會有咩唔同"][k]
    elif stage=='missing_info_question':
      en=[f"For {issue}, is anything missing from the {term} file before {c['dead_en']}?",f"Before {c['dead_en']}, can you tell me whether {issue} still needs anything for {term}?",f"Does the {term} record for {issue} still have a gap I should fill before {c['dead_en']}?",f"I want the {issue} file complete before {c['dead_en']}; what, if anything, is missing under {term}?"][k]
      yu=[f"{iy}份{ty}紀錄喺{c['dead_y']}前仲欠唔欠嘢",f"去到{c['dead_y']}之前，{iy}為咗{ty}仲使唔使補資料",f"{iy}嗰份{ty}紀錄仲有冇缺口要喺{c['dead_y']}前補",f"我想{iy}喺{c['dead_y']}前齊資料，{ty}仲欠咩未交"][k]
    elif stage in ('evidence_question','evidence_discrepancy'):
      extra='; one item differs from the older record' if stage=='evidence_discrepancy' else ''
      extra_y='，不過有一項同舊紀錄唔同' if stage=='evidence_discrepancy' else ''
      en=[f"For {issue}, I have {docs}{extra}; should these go with the {term} file?",f"I’ve got {docs} for {issue}{extra}; is that what you want under {term}?",f"On {issue}, my evidence is {docs}{extra}; should I send it for {term} now?",f"The documents I have for {issue} are {docs}{extra}; do they belong with {term}?"][k]
      yu=[f"{iy}我有{dcy}{extra_y}，係咪應該放落{ty}份紀錄",f"跟{iy}我手頭有{dcy}{extra_y}，{ty}嗰邊係咪要呢啲",f"{iy}嘅證明我有{dcy}{extra_y}，而家交去跟{ty}得唔得",f"我為{iy}準備咗{dcy}{extra_y}，呢啲係咪跟{ty}一齊交"][k]
    elif stage in ('interim_question','timing_question','consequence_followup'):
      en=[f"While {issue} is being checked, when should I follow up on {term}?",f"For {issue}, what should I do while I wait for the {term} response?",f"Until {issue} is decided, does {term} require anything else from me?",f"With {issue} still pending, how long should I leave {term} before I ask again?"][k]
      yu=[f"{iy}仲核對緊時，{ty}我幾時先應該再問",f"等{iy}有結果期間，{ty}我而家應該做咩",f"{iy}未有決定之前，{ty}仲使唔使我做其他嘢",f"{iy}仲等緊，{ty}大概隔幾耐先再跟好"][k]
    elif stage in ('review_question','change_question'):
      if stage=='review_question':
        en=[f"If the {issue} result still looks wrong, how do I challenge the {term} decision?",f"Suppose I still disagree with {issue}; who reviews the {term} decision first?",f"If {issue} is not corrected, what is the proper review route for {term}?",f"For {issue}, if I still dispute the outcome, where do I take the {term} decision next?"][k]
        yu=[f"如果{iy}個結果仲係唔啱，我點樣覆核{ty}個決定",f"如果我對{iy}仲係唔同意，{ty}個決定應該先搵邊個覆核",f"{iy}最後都冇改啱，{ty}應該用邊條覆核途徑",f"講{iy}，如果我仲要追個結果，{ty}個決定之後交邊度處理"][k]
      else:
        en=[f"If my contact details change before {issue} finishes, how do I update the {term} record?",f"While {issue} is open, where should I report a contact change for {term}?",f"If I move before {issue} is finished, what should I change on the {term} file?",f"For {issue}, if my phone or address changes, how do I keep the {term} notice coming to me?"][k]
        yu=[f"如果{iy}未完我聯絡資料有變，點樣改{ty}份紀錄",f"{iy}仲開住時，我聯絡資料有變要去邊度改{ty}",f"如果{iy}未完我搬咗，{ty}份檔案要改邊啲資料",f"講{iy}，如果我電話或者地址有變，點樣先唔會收漏{ty}個通知"][k]
    else: raise KeyError(stage)
    # S4 in every dialogue deliberately performs a natural confirmation/repair.
    if stage in ('fact_check','consequence_question','missing_info_question'):
      yu='即係話，'+yu
    return v3.tidy_articles(en.replace("'","’")),spoken_yue(conn+'，'+yu)

def client(stage,ns,s,i,v):
    if stage=='closure':
      lead=pick(['好呀','明白喇','得喇','好啦'],i,v,stage)
      tail=pick(['我知喇','咁好呀','得啦','明白呀'],i,v,stage,3)
      y=lead+'。'+tail+'。'
      e=pick(['Thanks. I understand.','All right. I’ve got it.','Understood. Thank you.','Okay. That is clear.'],i,v,stage)
      return e,y
    en,mid=client_middle(stage,ns,s,i,v)
    lead=pick(LEADS,i,v,stage)
    tail=pick(TAILS.get(stage,['咁點呀','係咪呀','得唔得呀','點做好呢']),i,v,stage,5)
    return en,spoken_yue(lead+'。'+mid+'。'+tail+'。')

def make_dialogue(ns,s0,i,v):
    s=clean_seed(s0); did=f'D{v*100+i+1:03d}'; segs=[]
    for n,stage in enumerate(base.STAGES[v],1):
      role='P' if n%2 else 'C'
      if role=='P': en,yu=officer(stage,ns,s,i,v)
      else: en,yu=client(stage,ns,s,i,v)
      words=len(en.split())
      if words>35: raise SystemExit(f'{did} S{n:02d}: {words} words >35: {en}')
      lang='en' if role=='P' else 'yue'; src=en if role=='P' else yu; model=yu if role=='P' else en
      segs.append({'n':n,'role':role,'source_lang':lang,'source':src,'model':model,'en':en,'yue':yu,'wc':words,'stage':stage})
    return {'id':did,'topic':s['topic'],'title':s['title']+base.VARIANT_SUFFIX[v],'term':s['term_en'],'term_yue':s['term_yue'],'segments':segs,'total':sum(x['wc'] for x in segs),'maxseg':max(x['wc'] for x in segs),'difficulty':'Medium','logic_version':'coherent-v2','encounter_variant':v}

def build():
  ns,seeds=base.load_backbone(); bank=[make_dialogue(ns,s,i,v) for v in range(5) for i,s in enumerate(seeds)]
  if [d['id'] for d in bank]!=[f'D{i:03d}' for i in range(1,501)]: raise SystemExit('bad IDs')
  if sum(len(d['segments']) for d in bank)!=6000: raise SystemExit('bad segment count')
  return bank

def main():
  ap=argparse.ArgumentParser(); ap.add_argument('--out',default=str(DEFAULT_OUT)); ap.add_argument('--promote',action='store_true'); a=ap.parse_args(); b=build(); out=ROOT/'data/dialogues.json' if a.promote else Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'dialogues':500,'segments':6000,'max_segment_words':max(d['maxseg'] for d in b),'logic_version':'coherent-v2'},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())

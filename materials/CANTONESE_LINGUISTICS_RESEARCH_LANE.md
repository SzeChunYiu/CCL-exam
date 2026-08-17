# Cantonese linguistics research lane

This is a living research note for improving the **spoken Hong Kong Cantonese** used in the English ⇄ Cantonese CCL practice bank. It is deliberately separate from the dialogue bank so script-writing work can use the findings without coupling linguistic research to any one generation pass.

The goal is not to make lines look more "Cantonese" by inserting slang or particles. The goal is to generate utterances whose **syntax, information structure, stance, repair, politeness, lexical choice and turn design** already behave like plausible Hong Kong Cantonese conversation.

## Evidence base

The first saturation pass used several complementary kinds of evidence rather than one textbook or one corpus:

- **HKCanCor / Hong Kong Cantonese Corpus** — about 230,000 words of transcribed Hong Kong Cantonese, including spontaneous conversations and radio speech, with word segmentation, POS tags and LSHK/Jyutping-style pronunciation annotation. This is useful for actual turn construction, discourse markers, particles, ellipsis and repetition.
- **CantoMap** — 768 minutes of connected modern Hong Kong Cantonese from forty speakers in a verbal-only task, useful for clarification, spatial reference, repair and information negotiation.
- **HKCAC and other adult spoken corpora** — spontaneous adult Hong Kong Cantonese useful for conversational frequency and pragmatic comparison.
- **Words.hk** — 53,000+ manually annotated Cantonese lexical entries with usage information, Jyutping, written-Cantonese definitions and example sentences.
- **Cifu** — a frequency lexicon for Hong Kong Cantonese, useful for preferring ordinary spoken lexical choices over rare or literary equivalents.
- **Written-Cantonese classification research** — shows that "Traditional Chinese" is not a sufficient language label: Standard Written Chinese, Written Cantonese and intermediate Hong Kong varieties need to be distinguished linguistically.
- **Sentence-final-particle research** — corpus, discourse and prosodic work on particles such as aa3 and on the wider Cantonese particle system.
- **Conversation-analysis work** — agreement, assessment, repair and stance are built sequentially between speakers, not by isolated sentence templates.
- **Court-interpreting research** — Cantonese utterance particles carry illocutionary force, stance and discourse coherence that cannot simply be translated word-for-word into English.
- **Hong Kong Cantonese-English contact research** — code-mixing is an ordinary feature of Hong Kong bilingual speech, with lexicalised English loanwords and context-sensitive switches.
- **English-loanword database** — 700+ English-derived items documented in Hong Kong Cantonese across roughly 180 years.
- **Modern Cantonese NLP work** — current large-scale Cantonese corpora and evaluation benchmarks still identify colloquial vocabulary, code-switching, orthographic variation and culturally specific language knowledge as difficult areas for language models.

## Saturated findings for script generation

### 1. Spoken Cantonese must be generated directly, not translated from Standard Written Chinese

A major failure mode is a sentence that has correct Cantonese characters but retains Standard Written Chinese syntax and lexical selection.

High-risk translated shapes include habitual use of forms such as:

- `我現在…` instead of natural `我而家…`
- `我沒有…` instead of `我冇…`
- `這個 / 那個` instead of `呢個 / 嗰個`
- `什麼` instead of `乜嘢`
- `哪裡` instead of `邊度`
- `是不是` instead of `係咪`
- `怎麼辦 / 如何處理` where `點算 / 點搞 / 點處理` would fit the register
- `但是 / 因此 / 此外 / 然而` when ordinary speech would more naturally use `但係 / 所以 / 同埋 / 不過 / 咁`
- repeated full formal subjects where Cantonese would omit recoverable material.

These are not absolute bans: an immigrant may read or quote a written notice, form or government letter using formal wording. The surrounding spoken turn should still sound spoken.

### 2. Colloquial markers are structural, not decorative

Real spontaneous speech shows frequent use of devices such as `其實`, `咁`, `即係`, `但係`, `同埋`, `呢`, repetition, reformulation and incomplete-looking fragments. A natural speaker may establish a frame, hesitate, repair it, then supply the important detail.

A useful generation rule is therefore:

> Do not write a polished paragraph and then add particles. Build the utterance as a turn in an interaction: what does the speaker already know, what are they unsure about, what are they correcting, and what response are they trying to obtain?

### 3. Sentence-final particles encode stance and interpersonal work

Cantonese has a rich utterance-/sentence-final particle system. Research on `aa3`, for example, identifies functions including tone-softening, subjective evaluation, politeness, intolerance and emphasis; corpus evidence found softening and subjective evaluation especially frequent.

Other research treats sentence-final particles as **epistemic modulators**: they help speakers continually recalibrate certainty, evidence, shared knowledge and stance while the conversation unfolds.

Generator consequence:

- particles must be selected for the conversational action, not mapped to English punctuation;
- not every Cantonese turn needs a particle;
- do not end every turn with the same `呀` or `㗎`;
- particle clusters should be rare and pragmatically motivated;
- the same proposition can sound cooperative, doubtful, surprised, insistent or corrective depending on particle/prosody;
- model English interpretations should render the **pragmatic force**, not mechanically add an English word for the particle.

### 4. Repair and clarification are central to believable service dialogue

CCL-style scenarios naturally contain names, dates, money, addresses, conditions and procedural language. Real interaction does not transmit all of this perfectly in one pass.

Useful repair architectures include:

- hearing/understanding check: `唔好意思，我頭先聽唔清楚，你話係星期三定星期四呀？`
- meaning check: `即係你意思係，我而家唔使再交多一份表，係咪？`
- self-repair: `唔係，我意思係我收到 email，但係冇收到嗰封信。`
- number confirmation: `等陣，係一千六百五十，唔係一千五百六十，係咪呀？`
- reference repair: `你頭先講嗰個號碼，係 application number 定 customer number？`
- consequence check: `咁如果我聽日先交，係咪就會當逾期呀？`

These should appear when the scenario genuinely creates uncertainty. If every dialogue contains the same clarification template, it becomes another generator fingerprint.

### 5. Cantonese-English mixing is normal, but random English is not

Hong Kong research consistently treats Cantonese-English mixing as a normal bilingual practice. A recent 2026 study of naturalistic Cantonese-English bilingual discourse found that less predictable words were more likely to occur at switching points; other Hong Kong work reports code-switching for conceptual gaps, casualness/solidarity and bilingual identity.

The loanword literature also documents hundreds of established English-derived items in Hong Kong Cantonese.

For this Australian CCL bank, natural code-switch targets include institutional names and labels that an immigrant in Australia would plausibly hear and retain in English:

- `Medicare`, `Centrelink`, `myGov`
- `ABN`, `TFN`, `ATO`
- `bond`, `lease`, `agent`
- `claim`, `policy number`, `excess`
- `reference number`, `application`, `email`, `SMS`
- school/course/program names and workplace acronyms.

Rules:

- keep well-known institutional names/acronyms in English when that is how the client would identify them;
- use Cantonese grammar around the English item;
- do not insert English merely to create "Hong Kong flavour";
- do not translate an English acronym into a long Chinese phrase and then immediately give the acronym again unless a real speaker would need to clarify it;
- older or less English-dominant client personas may code-switch less than younger bilingual professionals.

### 6. Politeness is not just `請問`

A translated script often overuses `請問` because English requests are repeatedly converted into one polite formula. Hong Kong Cantonese has more interactional options:

- `想問下…`
- `我想確認下…`
- `可唔可以麻煩你…`
- `唔好意思，我想問…`
- `咁我而家要點做呀？`
- `你可唔可以幫我睇下…`

`唔該` and `多謝` are also not interchangeable English "thank you" tokens. Research links their pragmatic difference to the kind of beneficial event and what is socially expected. In service encounters, requests and routine assistance, `唔該` is often the natural resource; `多謝` can encode a different or stronger beneficial-reception stance. Use the event and relationship, not an English dictionary substitution, to choose.

### 7. Directness can still be polite

Pragmatics research in Hong Kong service/business interaction warns against equating politeness with maximum indirectness. Appropriate directness depends on social distance, power, shared task and community norms.

For CCL scripts this means the Cantonese immigrant should not sound permanently deferential or helpless. A polite client may still say directly:

- `咁你幫我取消咗嗰個 direct debit 先啦。`
- `我想你幫我確認返個地址。`
- `呢筆錢我真係唔明點解會扣咗。`

The professional/client power difference should be visible in what each speaker knows and controls, not by making the client unnaturally submissive.

### 8. Negative directives need real Cantonese choices

Corpus research distinguishes Cantonese prohibitive resources such as `咪` and `唔好`; learner material that only uses one misses part of the system.

For script generation, compare:

- `你住先唔好交第二份申請。`
- `你咪再撳 submit 住，我幫你睇清楚先。`

The second has a different interactional feel and should only be used in a relationship/register where that wording is appropriate.

### 9. Information structure should exploit shared context

Cantonese conversation is highly context-dependent. Once a referent is established, speakers naturally use:

- `嗰份表`
- `嗰封信`
- `呢筆錢`
- `佢哋`
- zero subjects/objects where the reference is obvious.

Generated scripts often sound artificial because every turn restates `the application`, `the department`, `your rental property`, etc. Full noun phrases should recur only when disambiguation requires them.

### 10. Emotional stance should be ordinary, not theatrical

Immigrant-life service encounters create real low-level emotions: worry about a deadline, frustration at a duplicate charge, embarrassment about misunderstanding a form, relief after clarification, hesitation before challenging an authority.

Natural resources include:

- `我有少少擔心…`
- `我就係驚…`
- `我真係唔係好明…`
- `咁就好喇。`
- `原來係咁。`
- `弊喇，我一直以為…`

Use these sparingly. Avoid turning every scenario into a dramatic complaint.

### 11. Variation must be social, not random synonym replacement

Do not create "diversity" by mechanically swapping `咁` for another marker or rotating particles.

Vary speakers by:

- age and life stage;
- length of time in Australia;
- familiarity with the service system;
- education/professional background;
- English exposure and likelihood of code-switching;
- urgency/emotional state;
- whether the client is asking, correcting, challenging, confirming or deciding.

A newly arrived parent, an older migrant calling an insurer and a young small-business owner should not all have identical discourse habits.

### 12. Interpreting models must preserve stance, not particles

Court-interpreting research on Cantonese utterance particles is directly relevant to CCL. Particles can affect illocutionary force, modality and discourse coherence even where English has no lexical equivalent.

Model-answer rule:

- translate the proposition **plus** the relevant stance;
- do not omit a challenge, doubt, insistence, surprise or politeness effect merely because it lives in a particle;
- do not invent English filler words for every particle;
- preserve first-person perspective and the social action of the turn.

Example:

- Cantonese source: `你頭先唔係話今日會搞掂嘅咩？`
- Weak English: `Didn't you say it would be done today?`
- Better model when context supports challenge/surprise: `But didn't you say earlier that this would be sorted out today?`

The extra `But` is not a word-for-word particle translation; it preserves the interactional stance.

## A simple naturalness test

Before approving a Cantonese client turn, ask:

1. Would a Hong Kong Cantonese speaker actually say this aloud, or does it look like a Chinese translation?
2. Is the referent already known? If yes, can the line be less explicit?
3. What social action is the speaker performing: asking, checking, correcting, resisting, accepting, thanking, worrying?
4. Does the particle/discourse marker fit that action?
5. Is an English institutional word more natural than a forced Chinese expansion?
6. Does the turn contain exactly the detail an interpreter could plausibly hear and retain?
7. If read by neural TTS, does it have natural clause boundaries rather than one long formal sentence?
8. Does the model interpretation preserve the stance as well as the factual meaning?

## Anti-pattern examples

### Mandarin-shaped

`我現在不知道應該如何處理這個問題，請問你可以告訴我下一個步驟嗎？`

Prefer something like:

`我而家真係唔知下一步要點搞，想問下你我應該做咩先呀？`

### Over-polite template

`請問我是否需要提交這份文件？`

Possible spoken alternative:

`咁呢份文件我仲使唔使交呀？`

### Repeating the entire referent

`我沒有收到租務代理寄出的租金調整通知，所以我不知道租金調整通知上的生效日期。`

Possible spoken alternative:

`agent 嗰封加租通知我冇收到呀，所以我一路都唔知幾時開始加。`

### Particle decoration

Bad process: write a formal sentence, then append `呀/喎/㗎` until it looks Cantonese.

Better process: decide the speaker's stance and shared knowledge first; write the turn naturally; then use a particle only if the interaction calls for one.

## Research saturation map

The lane currently has coverage of:

- spoken corpora;
- connected conversation;
- lexical frequency/dictionaries;
- Written Cantonese vs Standard Written Chinese;
- sentence-final particles;
- epistemic stance;
- politeness and gratitude;
- requests/prohibitives;
- code-switching/loanwords;
- repair and clarification;
- conversation analysis;
- interpreter-mediated particle meaning;
- Cantonese NLP failure modes;
- sociolinguistic variation.

Future research should only be added when it produces a **materially new generation rule**, a better corpus-backed constraint, or evidence that changes one of the rules above. Repeating another generic description of Cantonese particles is not progress.

## Core references

- Luke, K. K. & Wong, M. L. Y. (2015), *The Hong Kong Cantonese Corpus: Design and Uses*. Corpus repository: https://github.com/fcbond/hkcancor
- Winterstein, G., Tang, C. & Lai, R. (2020), *CantoMap: a Hong Kong Cantonese MapTask Corpus*. https://aclanthology.org/2020.lrec-1.355/
- Lau, C.-m., Chan, G. W.-y., Tse, R. K.-w. & Chan, L. S.-y. (2022), *Words.hk: A Comprehensive Cantonese Dictionary Dataset*. https://aclanthology.org/2022.dclrl-1.7/
- Lai, R. & Winterstein, G. (2020), *Cifu: a Frequency Lexicon of Hong Kong Cantonese*. https://aclanthology.org/2020.lrec-1.375/
- Lau, C.-m., Lau, M. & To, A. W. H. (2024), *The Extraction and Fine-grained Classification of Written Cantonese Materials through Linguistic Feature Detection*. https://aclanthology.org/2024.eurali-1.4/
- Cheung, W. N. (2023), *Investigating the semantic/pragmatic function(s) of the Cantonese sentence final particle aa3*. HKU Scholars Hub: https://hub.hku.hk/handle/10722/335514
- Chor, W. (2018), *Sentence final particles as epistemic modulators in Cantonese conversations: A discourse-pragmatic perspective*.
- Leung, E. S. M. & Gibbons, J., *Interpreting Cantonese utterance-final particles in bilingual courtroom discourse*. https://scholars.hkbu.edu.hk/en/publications/interpreting-cantonese-utterance-final-particles-in-bilingual-cou/
- Tam, H. W.-Y. (2021), *The emergence of a beneficial reception marker: The discourse-pragmatic functions of doze in Hong Kong Cantonese*. https://thjcs.site.nthu.edu.tw/p/406-1452-212555%2Cr9262.php?Lang=en
- English Loanwords in Hong Kong Cantonese, PolyU/EdUHK research database. https://chaaklau.github.io/elw/
- Chan, A. S. L., Li, Y. & Poschl, J. (2026), *Word Predictability on Code-switching Points in Cantonese-English Discourse*. https://aclanthology.org/2026.scil-main.21/
- Chan, J. Y. C., Ching, P. C. & Lee, T., *Development of a Cantonese-English code-mixing speech corpus*. CUHK Research Portal.
- Lau, C. O., corpus research on Cantonese prohibitive markers `咪` and `唔好`, EdUHK Research Repository.
- Wong Gonzales, W. D. O. & Tsang, Y. M., research on Cantonese-English alternation in Hong Kong digital interaction, CUHK Research Portal.
- Jiang, J. et al. (2025), *Developing and Utilizing a Large-Scale Cantonese Dataset for Multi-Tasking in Large Language Models*. https://aclanthology.org/2025.findings-emnlp.102/
- Cheng, T. C. et al. (2025), *HKCanto-Eval: A Benchmark for Evaluating Cantonese Language Understanding and Cultural Comprehension in LLMs*.

# Cantonese script generation specification

This is the **operational writing spec** derived from `materials/CANTONESE_LINGUISTICS_RESEARCH_LANE.md`. It is intended for future dialogue generation, rewriting and human QA.

It complements the structural CCL rules in `QUESTION_DESIGN_ANALYSIS.md`; it does not replace them.

## Target speaker model

For this bank:

- **Professional / officer (`P`) speaks English.**
- **Immigrant / community client (`C`) speaks Cantonese.**
- The Cantonese target is **natural spoken Hong Kong Cantonese**, not Standard Written Chinese read aloud.
- The client is a competent adult, not a language-learning caricature.
- The Australian setting should affect the client's lexical choices and knowledge, but not turn the Cantonese into translated government prose.

## The generation order matters

Generate each Cantonese turn in this order:

1. **Situation:** what just happened in the conversation?
2. **Knowledge state:** what does the client know, infer, misunderstand or need confirmed?
3. **Social action:** request, correction, challenge, clarification, acceptance, refusal, worry, gratitude, decision, etc.
4. **Register:** relationship to officer; urgency; age/life background; English exposure.
5. **Information payload:** dates, money, references, names, conditions and consequences.
6. **Cantonese turn shape:** ellipsis, topic/comment structure, discourse marker, repair, code-switch if natural.
7. **Particle/stance:** only after the action is known.
8. **English model:** preserve meaning **and pragmatic force**, not particle-by-particle form.

Do **not** write a Standard Written Chinese sentence and then colloquialise it mechanically.

## Core lexical defaults

Prefer ordinary spoken Hong Kong forms when the meaning/register fits:

| Avoid as routine spoken default | Prefer in ordinary speech |
|---|---|
| 現在 | 而家 |
| 沒有 | 冇 |
| 這個 / 那個 | 呢個 / 嗰個 |
| 這些 / 那些 | 呢啲 / 嗰啲 |
| 他 / 她 / 他們 | 佢 / 佢哋 |
| 什麼 | 乜嘢 |
| 哪裡 | 邊度 |
| 是不是 | 係咪 |
| 怎麼 | 點 / 點樣 |
| 但是 | 但係 |
| 因此 | 所以 / 咁所以（only if natural） |
| 此外 | 同埋 / 仲有 |
| 給我 | 畀我 |
| 在 | 喺 |
| 來 | 嚟 |

These are contextual defaults, not blind substitutions. Formal written wording is legitimate when the client is **quoting or reading** a letter, form, policy or notice.

## Turn design

### Good Cantonese turns are not mini-essays

Prefer 1–3 spoken clauses with natural information packaging.

Useful shapes:

- frame + issue: `其實我上星期已經交咗㗎喇，但係今日又收到封信話欠文件。`
- concern + question: `我就係驚過咗聽日就當逾期，咁我今日仲趕唔趕得切呀？`
- correction: `唔係呀，我講緊係三月嗰張單，唔係今個月嗰張。`
- consequence check: `即係如果我而家補返份證明，就唔使重新申請，係咪？`
- decision: `好，咁我陣間返到屋企就 upload 返上去。`

### Vary turn length

A believable dialogue should include:

- short acknowledgements: `係呀。` / `哦，明白。`
- short repair questions;
- medium explanatory turns;
- a few information-dense turns with numbers/conditions.

Do not make every Cantonese turn 25–35 words.

## Required interactional diversity

Across a dialogue, use a **subset** of these where the scenario supports them:

- clarification;
- self-repair;
- number/date confirmation;
- misunderstanding correction;
- low-level worry/frustration;
- acceptance/relief;
- polite request;
- consequence check;
- objection/challenge;
- English institutional label embedded in Cantonese;
- reference to something established earlier (`嗰份表`, `呢筆錢`).

Do not force every item into every dialogue.

A healthy 12–16 segment dialogue normally benefits from at least **two different interactional events** beyond simple question → answer, but the exact count is a writing judgement rather than a hard invariant.

## Sentence-final particles

### Principle

Particles express stance and interaction; they are not decoration.

Useful common written representations include:

`呀`, `啊`, `啦`, `喎`, `啫`, `㗎`, `嘛`, `咩`, `囉`, `呢`, `喇`, `嘅`.

Do not attach a fixed English meaning to any of these in the generator.

### Specific guidance

- `呀/啊`: can soften, colour a question/request/evaluation or add interpersonal force. Do not use on every line.
- `㗎 / 嘅`: useful where the speaker presents, insists on or frames information as having a particular status; exact force is context-dependent.
- `喎`: often signals information/stance that is noteworthy relative to the current discourse; avoid treating it simply as "you know".
- `啫`: can limit/minimise or mark a restrictive stance; do not sprinkle it as casual flavour.
- `嘛`: can invoke shared/obvious grounds or justification depending on context.
- `咩`: can create a question/challenge/negative expectation; it can change the interpersonal force substantially.
- `啦 / 喇 / 囉`: can help with change-of-state, directive, acceptance, conclusion or stance functions depending on form/prosody/context.

Because these forms are polyfunctional, when uncertain prefer **no particle** over a random particle.

### Anti-patterns

Reject:

- every Cantonese turn ending in `呀`;
- rotating particles mechanically to create diversity;
- multiple particle clusters in every turn;
- adding a particle after translation without changing the information structure;
- English model answers that literally translate a particle as `you know`, `right`, `actually`, etc. without contextual justification.

## Discourse markers

Useful resources include:

`其實`, `咁`, `即係`, `但係`, `不過`, `同埋`, `仲有`, `所以`, `跟住`, `原來`, `咁樣`.

Rules:

- use them to manage discourse, not fill quotas;
- avoid the same turn-initial marker in three consecutive client turns;
- `其實` should introduce/reframe information, not simply mean English "actually" every time;
- `即係` is valuable for inference, paraphrase and confirmation;
- `咁` is common but especially easy for generators to overuse.

## Repair library

Generate repairs by changing the **problem**, not by copying a stock line.

### Hearing repair

`唔好意思，你頭先話個 reference number 最尾係七定九呀？`

### Meaning repair

`即係你意思係，我而家淨係補地址證明就得，係咪？`

### Self-repair

`我係上星期五交嘅——唔係，應該係星期四晚先啱。`

### Wrong-referent correction

`唔係嗰份，我講緊係續租嗰張表呀。`

### Number/date confirmation

`等陣，係四百八十蚊，唔係八百四十，係咪呀？`

### Consequence check

`咁我如果今日唔補到，個 application 係會 hold 住定直接取消？`

Never repeat one of these verbatim across many dialogues.

## Politeness and requests

Vary resources according to the action:

- `想問下…`
- `我想確認下…`
- `唔好意思，我想問…`
- `可唔可以麻煩你…`
- `你可唔可以幫我睇下…`
- `咁我下一步要點做呀？`
- `麻煩你幫我改返個地址。`

### `唔該` vs `多謝`

Do not translate every English `thank you` to the same Cantonese form.

Use the social event:

- routine request/service/assistance often favours `唔該`;
- receipt of a benefit, gift, compliment, unexpected commitment or stronger gratitude can favour `多謝`/`多謝晒`;
- sometimes no overt thanks is the most natural turn if the conversation is still in the middle of resolving a problem.

### Directness

Do not equate politeness with maximum indirectness.

A client can be polite and direct:

`呢筆錢我真係唔明點解會扣咗，你可唔可以幫我查返？`

This is often better than a long ceremonious request formula.

## Negatives and prohibitives

Use genuine Cantonese resources where appropriate:

- ordinary negation: `唔`, `冇`;
- prohibitives: `唔好`, `咪` with context-sensitive differences.

Examples:

`你住先唔好再交第二份申請。`

`你咪再撳 submit 住，我幫你睇清楚先。`

The latter can sound more interactionally marked/direct; do not put it indiscriminately in formal client-to-authority speech.

## Code-switching / English lexical items

### Keep English when it is the real-world label

Examples likely natural in Australian immigrant life:

`Medicare`, `Centrelink`, `myGov`, `ABN`, `TFN`, `ATO`, `bond`, `lease`, `agent`, `claim`, `policy`, `excess`, `reference number`, `email`, `SMS`, `upload`, `direct debit`.

Example:

`我喺 myGov 見到個 claim 係 rejected，但係佢冇寫清楚欠咩文件。`

### Do not over-code-switch

Bad:

`我而家個 situation 好 confusing，所以想 confirm 個 process。`

Unless a deliberately highly bilingual persona is required, this sounds generator-driven.

Better:

`我而家有啲搞唔清個程序，所以想確認下下一步要點做。`

Keep code-switches where the English word is institutional, lexicalised or plausibly more accessible to that speaker.

## Shared context and reference

Once something has been introduced, shorten later references naturally.

First mention:

`租務 agent 寄嗰封加租通知`

Later:

`嗰封信`

Then, if obvious:

`我真係冇收到呀。`

Avoid repeating a complete institutional noun phrase in every turn.

## Client persona matrix

Before generating a dialogue, choose a lightweight persona. Do not write it into the script; use it to constrain language.

### A. Newly arrived parent

- less system knowledge;
- moderate English code-switching for labels heard from institutions;
- more clarification and consequence checks;
- respectful, practical tone.

### B. Older long-term migrant

- confident everyday Cantonese;
- fewer trendy English switches;
- may ask more direct practical questions;
- can have difficulty with digital-only processes without sounding linguistically incompetent.

### C. Young worker/student

- more comfortable with English product/service terms;
- faster, shorter turns;
- casual particles/code-switching possible but still service-appropriate.

### D. Small-business owner / professional immigrant

- higher institutional/financial vocabulary;
- comfortable with `ABN`, `invoice`, `claim`, `payroll`, `GST`, etc.;
- may challenge discrepancies directly and precisely.

### E. Vulnerable/urgent client

- emotional load may shorten or fragment turns;
- prioritise essential facts and consequences;
- do not stereotype or make grammar artificially broken.

## Emotional range

Use understated real-life affect:

- worry: `我有少少擔心…`
- uncertainty: `我真係唔係好肯定…`
- frustration: `我已經打過兩次電話㗎喇。`
- embarrassment: `可能係我自己睇漏咗。`
- relief: `咁就好喇。`
- surprise/revision: `哦，原來係咁。`

A dialogue should not sound emotionally flat, but neither should every client be angry.

## Numbers, dates and names

Natural delivery matters as much as correctness.

- Let a speaker state a number once, then confirm the risky part later.
- Mix money, dates, times, reference numbers and addresses across the bank.
- Do not make every dialogue contain all types of numeric difficulty.
- Build realistic repair around digit order and date ambiguity.
- For unfamiliar Australian names, it is natural for the Cantonese client to repeat/spell/check rather than instantly absorb them.

## Model interpretation rules

The English model must preserve:

- first person;
- factual meaning;
- degree of certainty;
- politeness/directness;
- challenge or correction;
- emotional stance if material;
- referential continuity;
- consequence/request type.

Do not preserve:

- Cantonese particles as fake English filler words;
- Cantonese discourse markers mechanically when English would express the same relation through syntax or intonation.

### Example

Cantonese:

`你頭先唔係話今日會搞掂嘅咩？`

Good model:

`But didn't you say earlier that this would be sorted out today?`

The model carries the corrective/challenging stance without pretending `咩` has a one-word English equivalent.

## Diversity gates for a 100-dialogue bank

Use these as **soft corpus-level QA**, not hard per-dialogue quotas:

- no single opening formula dominates client turns;
- no single closing formula dominates dialogues;
- no repeated clarification sentence template across topics;
- visible variety in particles/discourse markers but no forced equal distribution;
- different client personas show different code-switching levels;
- some dialogues have no explicit repair; others have one or two meaningful repairs;
- some client turns are very short;
- gratitude forms are context-sensitive;
- written/SWC-like forms occur primarily when quoting written material;
- institutional English appears only where scenario-specific.

## Red flags for automated or human review

A reviewer should inspect a Cantonese turn if it has several of these at once:

- `現在`, `沒有`, `這個`, `那個`, `什麼`, `哪裡`, `是否`, `但是`, `因此`, `此外`, `然而` in unquoted everyday speech;
- `請問` in multiple consecutive client turns;
- every sentence ending with the same particle;
- no particles/discourse markers/ellipsis anywhere in a long multi-turn dialogue;
- repeated full nouns where pronouns/zero reference would be obvious;
- multiple English switches in a short ordinary sentence without institutional reason;
- an unusually polished multi-clause written paragraph;
- client repeatedly asks generic `what should I do next?` questions instead of reacting to the actual case;
- model interpretation loses the client's doubt/challenge/relief and only transfers propositional content.

## Final read-aloud gate

Read the Cantonese aloud at normal Hong Kong conversational speed.

Approve only if:

- clause boundaries are speakable;
- the particle/ending does not feel pasted on;
- the line can be said in one natural breath pattern or has a plausible internal pause;
- a service client could say it without sounding like a newsreader;
- the next officer turn is a natural response to the exact action the client performed.

If the officer's next response could follow almost any generic client line, the dialogue probably lacks enough interactional specificity.

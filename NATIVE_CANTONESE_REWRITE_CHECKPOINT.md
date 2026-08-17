# Native Cantonese rewrite — pre-generation checkpoint

Checkpoint date: 2026-08-17

This commit freezes the research and verification state **before** bank-wide dialogue regeneration.

## Frozen decisions

- Professional/officer source turns are English.
- Immigrant/community-client source turns are Cantonese.
- Cantonese source turns target **native spoken Hong Kong Cantonese**, not Standard Written Chinese and not English-shaped translated Cantonese.
- Because this is an interpreting/translation practice bank, Cantonese source turns should carry the lexical transfer burden in Cantonese. English lexical items are rejected by default even where real Hong Kong speech might code-switch. Example design principle: `Facebook` should be realised as `臉書` in the Cantonese source when the intended exercise is lexical transfer.
- Bank-wide generation must avoid both exact sentence reuse and abstract repeated sentence skeletons.
- Cantonese turns are generated from interaction state first: situation → knowledge state → social action → information structure → wording → particles/stance → English model interpretation.
- Do not draft an English sentence and mechanically translate/colloquialise it.

## Baseline findings on the current 100-dialogue bank

The latest bank contains 100 dialogues and 1,412 segments, including 688 Cantonese client-source turns.

Audits found major rewrite debt:

- structural verifier: 1,344 reported violations on the current baseline;
- extensive exact sentence reuse across dialogue families;
- near-duplicate/template reuse well beyond an acceptable native-human target;
- too few genuine repair/confirmation events and short conversational turns;
- Cantonese client-source segments still containing English/Latin lexical material;
- several word-count, scoreable-detail and terminology-transfer inconsistencies.

The current bank is therefore treated as **semantic/scenario reference**, not prose to paraphrase.

## Research / QA assets frozen at this checkpoint

- `materials/CANTONESE_LINGUISTICS_RESEARCH_LANE.md`
- `materials/CANTONESE_SCRIPT_GENERATION_SPEC.md`
- `scripts/audit_cantonese_naturalness.py`
- `scripts/audit_native_cantonese_v2.py`
- `scripts/qa_cantonese.py`
- `scripts/verify_rewrite.py`
- `scripts/merge_rewrite.py`
- `scripts/generate_v4_audio.py`
- `scripts/upload_v4_segments.py`
- `.github/workflows/cantonese-audio-integration.yml`

## Rewrite protocol after this checkpoint

1. Work in independent batches rather than one global template generator.
2. Preserve each dialogue's real-life scenario/topic and scoreable facts only when they still make sense.
3. Plan each client's persona, trigger, misunderstanding/knowledge gap, repair/clarification, decision/consequence and resolution before wording turns.
4. Write Cantonese directly as Cantonese.
5. Remove English lexical leakage from Cantonese source turns unless a truly non-translatable literal datum requires it.
6. Run structural, lexical-transfer, exact-repeat, near-duplicate, skeleton, corpus-register and interactional-naturalness gates after every batch.
7. Freeze the final rewritten bank before synthesising any replacement audio.
8. Regenerate neural MP3s only from that frozen bank, with per-voice calibrated Cantonese speed.
9. Verify text/audio language alignment and all 1,412 assets before production promotion.

No bank-wide rewrite or replacement-audio generation is represented as complete by this checkpoint.

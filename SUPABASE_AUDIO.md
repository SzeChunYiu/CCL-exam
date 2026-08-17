# Supabase neural audio storage

V3 serves each CCL source segment as an individual public MP3 from Supabase Storage. Vercel serves the application; Supabase serves the audio.

## Project layout

- Supabase project: `ccl-exam` (`dmoputkgxuaeoypmdfhm`, EU North / Stockholm)
- Public bucket: `ccl-audio`
- V3 object path: `v3/<dialogue-id>/S<segment>.mp3`, for example `v3/D001/S01.mp3`
- Public browser base URL is stored in `data/audio_remote.json`
- `public.ccl_dialogues` stores the dialogue payload used during generation
- `public.ccl_audio_assets` stores one metadata/status row per generated segment

## Voices and pace

Role-based neural voices:

- English provider: `en-AU-WilliamNeural`
- English client: `en-AU-NatashaNeural`
- Cantonese provider: `zh-HK-WanLungNeural`
- Cantonese client: `zh-HK-HiuGaaiNeural`

English uses normal neural rate. Cantonese uses a small `+5%` synthesis adjustment. This was chosen after benchmarking the supplied practice samples at about 160 English words/minute and roughly 4.0 Cantonese characters/second.

The MP3 contains only source speech. The web player generates the two-tone interpretation cue immediately after the segment, then starts the practice countdown.

## Security model

The bucket is public because the practice MP3s are public study assets. The browser receives **no service-role key** and performs no writes. Database tables use RLS with public-read policies only.

Audio was generated server-side by temporary Supabase Edge Functions. Those functions are locked after migration completes. The site needs only the public object base URL.

## Fallback order

1. V3 Supabase neural segment MP3
2. checked-in legacy bundled MP3
3. an eligible Australian-English or Hong Kong Cantonese device speech voice

The player does not intentionally substitute a Mandarin voice for Cantonese.

## Verification

Release QA requires:

- exactly **1,412** `ready` rows in `public.ccl_audio_assets`;
- **0** `error` rows;
- 100 dialogue payloads;
- all four neural voices represented;
- Storage objects with non-zero byte sizes;
- Supabase security/performance advisor checks clean.

The neural audio is synthetic practice material, not official NAATI audio or human voice acting.

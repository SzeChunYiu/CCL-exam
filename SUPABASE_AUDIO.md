# Supabase audio storage

The exam player can serve the calibrated MP3 bundles from Supabase Storage while keeping the checked-in bundles as a fallback.

## Security model

The audio bucket is public because the practice audio itself is public study content. Uploads use the **service-role key only inside GitHub Actions**. The key is never committed or sent to the browser.

## Required GitHub Actions secrets

In **Settings → Secrets and variables → Actions**, add:

- `SUPABASE_URL` — your project URL, for example `https://<project-ref>.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY` — the project's service-role key; never use the anon key for this uploader

Then run **Actions → Sync calibrated audio to Supabase → Run workflow** on the branch you want to publish.

The workflow will:

1. create or reuse a public bucket named `ccl-audio`;
2. upload the four calibrated bundle files under `v1/`;
3. upload `audio_manifest.json` beside them;
4. verify each public object can be fetched with an HTTP Range request;
5. write `data/audio_remote.json` containing only the public Storage location; and
6. commit that public configuration to the branch.

The website reads `data/audio_remote.json` when present. If the file is missing or Supabase is unavailable, it falls back to `/assets/audio-bundles/`, then to device speech synthesis only if MP3 playback itself fails.

This design keeps the exact sample-calibrated pace unchanged: moving files to Supabase changes delivery, not synthesis or playback rate.

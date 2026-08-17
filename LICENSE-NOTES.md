# Licence and attribution notes

The CCL practice dialogues, model interpretations, study notes, website and generation code in this repository were created as original study materials for this project.

The GitHub build fetches the public eSpeak Cantonese pronunciation list from an upstream mirror, verifies its SHA-256 hash, compiles it with `zhy_rules`, and removes the downloaded source from the working tree afterwards. The upstream pronunciation list contains its own attribution and Creative Commons Attribution-ShareAlike 3.0 notice. See `scripts/fetch_cantonese_dict.py` and `resources/espeak-cantonese/README.md`.

The eSpeak pronunciation resources are used only to generate independent synthetic practice audio. This repository is not affiliated with or endorsed by NAATI or the Australian Government. No NAATI audio and no live or leaked examination content is included.

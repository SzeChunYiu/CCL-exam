# Cantonese eSpeak pronunciation source

`zhy_rules` is committed here. The larger `zhy_list` pronunciation source is fetched during the GitHub build by `scripts/fetch_cantonese_dict.py` from public upstream mirrors and verified against a pinned SHA-256 hash before compilation.

The fetched list contains its upstream attribution/licence notice. The workflow removes the downloaded source after compiling the local eSpeak dictionary, so generated practice audio remains reproducible without vendoring a large third-party text file into this repository.

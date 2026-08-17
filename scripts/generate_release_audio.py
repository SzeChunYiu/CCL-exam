#!/usr/bin/env python3
"""Generate final CCL segment audio with final-bank calibrated rates.

These release-only defaults were measured on the frozen v18 500-dialogue bank,
not inherited from the older 100-dialogue calibration.  A representative
240-segment final-bank probe measured:

    English      170.45 wpm  (target 168.0, +1.5%)
    Cantonese      4.12 Han/s (target 4.07, +1.2%)

Per voice at the selected rates:
    William +7%   -> 173.01 wpm
    Natasha +29%  -> 165.55 wpm
    WanLung +37%  -> 4.07 Han/s
    HiuMaan +39%  -> 4.16 Han/s

The original punctuation shaping is retained because the measured profile passed
with it.  Pitch is globally neutral so lexical Cantonese tone is not shifted.
Environment variables remain overridable for controlled future calibration.
"""
from __future__ import annotations

import os

os.environ.setdefault("CCL_RATE_WILLIAM", "+7%")
os.environ.setdefault("CCL_RATE_NATASHA", "+29%")
os.environ.setdefault("CCL_RATE_WANLUNG", "+37%")
os.environ.setdefault("CCL_RATE_HIUMAAN", "+39%")
os.environ.setdefault("CCL_SPLIT_FOR_SPEECH", "1")
os.environ.setdefault("CCL_PITCH_CYCLE", "+0Hz")

import generate_v4_audio as generator  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(generator.main())

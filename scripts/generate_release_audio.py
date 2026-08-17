#!/usr/bin/env python3
"""Generate final CCL segment audio with calibrated rates and neutral pitch.

The voice-rate calibration stays in generate_v4_audio.py.  Release synthesis
forces a neutral global pitch so lexical Cantonese tone is not shifted by an
artificial per-dialogue pitch cycle.  Natural variation comes from the two
Hong Kong voices, two Australian-English voices, punctuation, clause structure,
and the calibrated delivery rate.
"""
from __future__ import annotations

import os

os.environ.setdefault("CCL_PITCH_CYCLE", "+0Hz")

import generate_v4_audio as generator  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(generator.main())

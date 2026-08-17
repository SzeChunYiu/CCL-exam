#!/usr/bin/env python3
"""Release entry point for the calibrated v4 CCL audio generator.

The underlying generator retains historical probe values and an experimental
pitch cycle.  The release policy is deliberately narrower:

* zh-HK-WanLungNeural: +13%
* zh-HK-HiuMaanNeural: +17%
* en-AU-WilliamNeural: +0%
* en-AU-NatashaNeural: +22%
* neutral global pitch (+0Hz)

For Cantonese, prosodic naturalness comes from native wording, particles, clause
boundaries and the measured delivery rate.  Arbitrary global pitch shifts are not
used because Cantonese is tonal.
"""
from __future__ import annotations

import os

import generate_v4_audio as g


def configure() -> None:
    g.VOICE_RATES["zh-HK-WanLungNeural"] = os.environ.get("CCL_RATE_WANLUNG", "+13%")
    g.VOICE_RATES["zh-HK-HiuMaanNeural"] = os.environ.get("CCL_RATE_HIUMAAN", "+17%")
    g.VOICE_RATES["en-AU-WilliamNeural"] = os.environ.get("CCL_RATE_WILLIAM", "+0%")
    g.VOICE_RATES["en-AU-NatashaNeural"] = os.environ.get("CCL_RATE_NATASHA", "+22%")
    g.PITCH_CYCLE[:] = ["+0Hz"]


if __name__ == "__main__":
    configure()
    raise SystemExit(g.main())

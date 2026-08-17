#!/usr/bin/env python3
"""Run v12 with a Cantonese integer renderer that supports generated amounts."""
from __future__ import annotations

import build_native_500_v12 as v12

DIGITS = "零一二三四五六七八九"


def zh_int(n: int) -> str:
    if n < 0:
        return "負" + zh_int(-n)
    if n < 10:
        return DIGITS[n]
    if n < 20:
        return "十" + (DIGITS[n % 10] if n % 10 else "")
    if n < 100:
        return DIGITS[n // 10] + "十" + (DIGITS[n % 10] if n % 10 else "")
    if n < 1000:
        q, r = divmod(n, 100)
        if not r:
            return DIGITS[q] + "百"
        return DIGITS[q] + "百" + ("零" if r < 10 else "") + zh_int(r)
    if n < 10000:
        q, r = divmod(n, 1000)
        if not r:
            return DIGITS[q] + "千"
        return DIGITS[q] + "千" + ("零" if r < 100 else "") + zh_int(r)
    q, r = divmod(n, 10000)
    if not r:
        return zh_int(q) + "萬"
    return zh_int(q) + "萬" + ("零" if r < 1000 else "") + zh_int(r)


v12.zh_int = zh_int

if __name__ == "__main__":
    raise SystemExit(v12.main())

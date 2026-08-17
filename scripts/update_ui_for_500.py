#!/usr/bin/env python3
"""Remove stale 100-dialogue UI copy after the bank expands to 500.

The application already reads dialogue data and mock pairs dynamically.  These
replacements only remove hard-coded display copy/fallbacks so future bank-size
changes cannot make the interface lie about the loaded data.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path: Path, replacements):
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text == original:
        print(f"{path.name}: no changes needed")
    else:
        path.write_text(text, encoding="utf-8")
        print(f"{path.name}: updated")


def main() -> int:
    patch(ROOT / "app.js", [
        ("100-dialogue Library", "Dialogue Library"),
        ("100-dialogue library", "dialogue library"),
        ("100-dialogue bank", "full dialogue bank"),
    ])
    patch(ROOT / "simple-ui.js", [
        ("100-dialogue library", "Dialogue library"),
        ("state.summary?.dialogues||100", "state.summary?.dialogues||state.dialogues.length||500"),
        ("<h1>100 dialogues</h1>", "<h1>${state.dialogues.length} dialogues</h1>"),
    ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

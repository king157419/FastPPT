"""Render a cached fixture (json) through the current pptx_renderer to PNGs.

Usage: python eval/render_json.py <key>   # key in {math, cs, general}
No LLM calls — reuses outputs/_fix_<key>.json so renderer design can be iterated fast.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)


def main() -> None:
    key = sys.argv[1] if len(sys.argv) > 1 else "math"
    fix_path = os.path.join(BACKEND, "outputs", f"_fix_{key}.json")
    with open(fix_path, encoding="utf-8") as fh:
        data = json.load(fh)

    from core.pptx_renderer import render_pptx

    pptx = os.path.join(BACKEND, "outputs", f"_fix_{key}.pptx")
    render_pptx(data["intent"], data["slides_json"], pptx)

    from eval.render_preview import render

    pngs = render(pptx, os.path.join(BACKEND, "outputs", "_preview"), 130)
    print(f"[{key}] rendered {len(pngs)} pages from cached json:")
    for p in pngs:
        print(p)


if __name__ == "__main__":
    main()

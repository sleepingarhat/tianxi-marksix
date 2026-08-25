# -*- coding: utf-8 -*-
"""個人奇門 × 攪珠日奇門 → 15 碼（chaibu-v2 取數）

用法:
  python src/personal_x_draw_qimen.py --personal 1988-02-08T04:00 --draw 2026-08-22
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pick15 import pick15  # noqa: E402
from qimen_dipan import cast_qimen, extract_scores, pan_to_dict  # noqa: E402


def generate(
    py: int, pm: int, pd: int, ph: int, dy: int, dm: int, dd: int
) -> dict:
    personal = cast_qimen(py, pm, pd, ph)
    draw = cast_qimen(dy, dm, dd, 21)
    scores: dict[int, float] = defaultdict(float)
    for n, w in extract_scores(draw, weight_scale=1.0).items():
        scores[n] += w
    for n, w in extract_scores(personal, weight_scale=0.75).items():
        scores[n] += w
    numbers = pick15(dict(scores))
    return {
        "ruleVersion": "qimen-chaibu-v2 + personal-x-draw-v1",
        "mode": "qimen_personal_x_draw",
        "personal": pan_to_dict(personal),
        "draw": pan_to_dict(draw),
        "draw_datetime": f"{dy:04d}-{dm:02d}-{dd:02d}T21:30:00+08:00",
        "numbers": numbers,
    }


def pure_draw(dy: int, dm: int, dd: int) -> dict:
    draw = cast_qimen(dy, dm, dd, 21)
    numbers = pick15(extract_scores(draw, 1.0))
    return {
        "ruleVersion": "qimen-chaibu-v2",
        "mode": "pure_qimen",
        "draw": pan_to_dict(draw),
        "numbers": numbers,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--personal", default="", help="YYYY-MM-DDTHH；空則純當日")
    ap.add_argument("--draw", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()
    dy, dm, dd = map(int, args.draw.split("-"))
    if not args.personal:
        print(json.dumps(pure_draw(dy, dm, dd), ensure_ascii=False, indent=2))
        return
    p = args.personal.replace("/", "-").replace(" ", "T")
    if "T" in p:
        date_part, time_part = p.split("T", 1)
        hh = int(time_part.split(":")[0])
    else:
        date_part, hh = p, 12
    py, pm, pd = map(int, date_part.split("-"))
    print(json.dumps(generate(py, pm, pd, hh, dy, dm, dd), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

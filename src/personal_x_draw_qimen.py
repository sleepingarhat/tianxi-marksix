# -*- coding: utf-8 -*-
"""個人奇門（出生時盤當終生參考）× 攪珠日奇門 → 15 碼

ruleVersion: personal-x-draw-v1
僅地盤取數。

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
from qimen_dipan import cast_qimen, pan_to_dict  # noqa: E402

GAN = "甲乙丙丁戊己庚辛壬癸"
SAN_QI = set("乙丙丁")


def gan_to_nums(gan: str) -> list[int]:
    if gan not in GAN:
        return []
    i = GAN.index(gan) + 1
    return [((i + k * 10 - 1) % 49) + 1 for k in range(5)]


def palace_to_nums(p: int) -> list[int]:
    # 宮數及倍數映射入 1-49
    return [((p + k * 9 - 1) % 49) + 1 for k in range(6)]


def add_pan_scores(pan, weights: dict[str, float], scores: dict[int, float]) -> None:
    zf = pan.zhi_fu_palace
    zo = pan.zhi_fu_origin
    for palace, gan in pan.di_pan.items():
        if palace == 5:
            continue
        if palace == zf:
            w = weights["zf"]
        elif palace == zo:
            w = weights["zo"]
        elif gan in SAN_QI:
            w = weights["sanqi"]
        else:
            w = weights["other"]
        for n in gan_to_nums(gan):
            scores[n] += w
        for n in palace_to_nums(palace):
            scores[n] += w * 0.5


DRAW_W = {"zf": 3.5, "zo": 3.0, "sanqi": 2.5, "other": 1.5}
PERSONAL_W = {"zf": 2.5, "zo": 2.0, "sanqi": 2.0, "other": 1.0}


def generate(
    py: int, pm: int, pd: int, ph: int, dy: int, dm: int, dd: int
) -> dict:
    personal = cast_qimen(py, pm, pd, ph)
    draw = cast_qimen(dy, dm, dd, 21)
    scores: dict[int, float] = defaultdict(float)
    add_pan_scores(draw, DRAW_W, scores)
    add_pan_scores(personal, PERSONAL_W, scores)
    numbers = pick15(dict(scores))
    return {
        "ruleVersion": "personal-x-draw-v1",
        "mode": "qimen_personal_x_draw",
        "personal": pan_to_dict(personal),
        "draw": pan_to_dict(draw),
        "draw_datetime": f"{dy:04d}-{dm:02d}-{dd:02d}T21:30:00+08:00",
        "numbers": numbers,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--personal", required=True, help="YYYY-MM-DDTHH")
    ap.add_argument("--draw", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()
    p = args.personal.replace("/", "-").replace(" ", "T")
    if "T" in p:
        date_part, time_part = p.split("T", 1)
        hh = int(time_part.split(":")[0])
    else:
        date_part, hh = p, 12
    py, pm, pd = map(int, date_part.split("-"))
    dy, dm, dd = map(int, args.draw.split("-"))
    print(json.dumps(generate(py, pm, pd, hh, dy, dm, dd), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

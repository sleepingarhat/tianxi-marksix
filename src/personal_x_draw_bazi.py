# -*- coding: utf-8 -*-
"""個人八字 × 攪珠日八字 → 15 碼

ruleVersion: personal-x-draw-v1
不用喜用池；只干支映射 + 日主河圖。

用法:
  python src/personal_x_draw_bazi.py --personal 1988-02-08T04:00 --draw 2026-08-22
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import sxtwl
except ImportError as e:
    raise ImportError("需要 sxtwl") from e

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pick15 import pick15  # noqa: E402

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
WX_G = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}
# 河圖尾數
WX_TAILS = {"水": (1, 6), "火": (2, 7), "木": (3, 8), "金": (4, 9), "土": (0, 5)}


def gz_str(gz) -> str:
    return GAN[gz.tg] + ZHI[gz.dz]


def pillars_at(y: int, m: int, d: int, hour: int) -> dict[str, str]:
    day = sxtwl.fromSolar(y, m, d)
    return {
        "year": gz_str(day.getYearGZ(False)),
        "month": gz_str(day.getMonthGZ()),
        "day": gz_str(day.getDayGZ()),
        "hour": gz_str(day.getHourGZ(hour)),
    }


def map_gz_to_scores(gz: str, weight: float, scores: dict[int, float]) -> None:
    """干支展開到 1-49 多組候選。"""
    gi = GAN.index(gz[0]) + 1  # 1-10
    zi = ZHI.index(gz[1]) + 1  # 1-12
    cands = set()
    for base in (gi, zi, gi + zi, abs(gi * zi), (gi * 6 + zi) % 49 + 1):
        n = ((base - 1) % 49) + 1
        cands.add(n)
        cands.add(((n + 9 - 1) % 49) + 1)
        cands.add(((n + 24 - 1) % 49) + 1)
    for n in cands:
        if 1 <= n <= 49:
            scores[n] += weight


def map_wx_to_scores(wx: str, weight: float, scores: dict[int, float]) -> None:
    tails = WX_TAILS.get(wx, ())
    for n in range(1, 50):
        if n % 10 in tails or (n % 10 == 0 and 0 in tails):
            scores[n] += weight


def score_chart(pillars: dict[str, str], weights: dict[str, float], scores: dict[int, float]) -> None:
    for key, w in weights.items():
        if key in pillars:
            map_gz_to_scores(pillars[key], w, scores)
    dm = WX_G[pillars["day"][0]]
    map_wx_to_scores(dm, weights.get("day_master_wx", 1.0), scores)


DRAW_W = {"hour": 4.0, "day": 3.0, "month": 2.0, "year": 1.5, "day_master_wx": 1.0}
PERSONAL_W = {"day": 3.0, "hour": 2.5, "month": 2.0, "year": 1.5, "day_master_wx": 1.0}


def generate(personal_y: int, personal_m: int, personal_d: int, personal_h: int, draw_y: int, draw_m: int, draw_d: int) -> dict:
    personal = pillars_at(personal_y, personal_m, personal_d, personal_h)
    draw = pillars_at(draw_y, draw_m, draw_d, 21)
    scores: dict[int, float] = defaultdict(float)
    score_chart(draw, DRAW_W, scores)
    score_chart(personal, PERSONAL_W, scores)
    numbers = pick15(dict(scores))
    return {
        "ruleVersion": "personal-x-draw-v1",
        "mode": "bazi_personal_x_draw",
        "personal_pillars": personal,
        "draw_pillars": draw,
        "draw_datetime": f"{draw_y:04d}-{draw_m:02d}-{draw_d:02d}T21:30:00+08:00",
        "numbers": numbers,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--personal", required=True, help="YYYY-MM-DDTHH 或 YYYY-MM-DDTHH:MM")
    ap.add_argument("--draw", required=True, help="攪珠日 YYYY-MM-DD")
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

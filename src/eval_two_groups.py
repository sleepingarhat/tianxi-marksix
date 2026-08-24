# -*- coding: utf-8 -*-
"""兩組回測近 N 期（含 5 / 5.5 / ≥6 統計）

A. 純攪珠日盤　B. 個人×攪珠
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from personal_x_draw_bazi import DRAW_W, pillars_at, score_chart  # noqa: E402
from personal_x_draw_bazi import generate as gen_bazi_px  # noqa: E402
from personal_x_draw_qimen import DRAW_W as Q_DRAW_W  # noqa: E402
from personal_x_draw_qimen import add_pan_scores  # noqa: E402
from personal_x_draw_qimen import generate as gen_qimen_px  # noqa: E402
from pick15 import pick15  # noqa: E402
from qimen_dipan import cast_qimen  # noqa: E402

DEFAULT_URL = (
    "https://raw.githubusercontent.com/sleepingarhat/hk-mark-six-2002-now/main/data/mark-six.json"
)


def score(pred: list[int], numbers: list[int], special) -> float:
    s = float(len(set(pred) & set(numbers)))
    if special is not None and special in pred:
        s += 0.5
    return s


def pure_bazi(dy: int, dm: int, dd: int) -> list[int]:
    scores: dict[int, float] = defaultdict(float)
    score_chart(pillars_at(dy, dm, dd, 21), DRAW_W, scores)
    return pick15(dict(scores))


def pure_qimen(dy: int, dm: int, dd: int) -> list[int]:
    scores: dict[int, float] = defaultdict(float)
    add_pan_scores(cast_qimen(dy, dm, dd, 21), Q_DRAW_W, scores)
    return pick15(dict(scores))


def parse_personal(s: str) -> tuple[int, int, int, int]:
    p = s.replace("/", "-").replace(" ", "T")
    if "T" in p:
        date_part, time_part = p.split("T", 1)
        hh = int(time_part.split(":")[0])
    else:
        date_part, hh = p, 12
    y, m, d = map(int, date_part.split("-"))
    return y, m, d, hh


def bucket() -> dict:
    return {"avg": 0.0, "total": 0.0, "eq5": 0, "eq5_5": 0, "ge5": 0, "ge6": 0, "max": 0.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--personal", required=True)
    ap.add_argument("--n", type=int, default=100)
    args = ap.parse_args()
    py, pm, pd, ph = parse_personal(args.personal)

    with urllib.request.urlopen(DEFAULT_URL, timeout=60) as resp:
        draws = json.loads(resp.read().decode("utf-8"))[-args.n :]

    keys = ["A_pure_bazi", "A_pure_qimen", "B_px_bazi", "B_px_qimen"]
    stats = {k: bucket() for k in keys}
    hist = {k: defaultdict(int) for k in keys}

    for row in draws:
        dy, dm, dd = map(int, row["date"].split("-"))
        nums = list(row["numbers"])
        sp = row.get("special") or row.get("special_number") or row.get("sp")
        if sp is None and len(nums) >= 7:
            sp = nums[6]
            nums = nums[:6]
        elif len(nums) > 6:
            nums = nums[:6]

        preds = {
            "A_pure_bazi": pure_bazi(dy, dm, dd),
            "A_pure_qimen": pure_qimen(dy, dm, dd),
            "B_px_bazi": gen_bazi_px(py, pm, pd, ph, dy, dm, dd)["numbers"],
            "B_px_qimen": gen_qimen_px(py, pm, pd, ph, dy, dm, dd)["numbers"],
        }
        for k, pred in preds.items():
            sc = score(pred, nums, sp)
            st = stats[k]
            st["total"] += sc
            st["max"] = max(st["max"], sc)
            hist[k][sc] += 1
            if sc == 5.0:
                st["eq5"] += 1
            if sc == 5.5:
                st["eq5_5"] += 1
            if sc >= 5.0:
                st["ge5"] += 1
            if sc >= 6.0:
                st["ge6"] += 1

    n = len(draws)
    for k in keys:
        stats[k]["avg"] = round(stats[k]["total"] / n, 3)
        stats[k]["total"] = round(stats[k]["total"], 1)
        stats[k]["max"] = stats[k]["max"]

    out = {
        "n": n,
        "personal": args.personal,
        "group_A_pure_draw": {
            "bazi": stats["A_pure_bazi"],
            "qimen": stats["A_pure_qimen"],
        },
        "group_B_personal_x_draw": {
            "bazi": stats["B_px_bazi"],
            "qimen": stats["B_px_qimen"],
        },
        "score_histogram": {k: {str(a): b for a, b in sorted(hist[k].items())} for k in keys},
        "baseline_random_expected_zheng": round(15 * 6 / 49, 3),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

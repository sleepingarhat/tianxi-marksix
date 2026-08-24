# -*- coding: utf-8 -*-
"""列出近 N 期各線最高分及所有 ≥5 字期詳情。"""
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

URL = "https://raw.githubusercontent.com/sleepingarhat/hk-mark-six-2002-now/main/data/mark-six.json"


def score(pred, numbers, special):
    hit = sorted(set(pred) & set(numbers))
    s = float(len(hit))
    sp_hit = special is not None and special in pred
    if sp_hit:
        s += 0.5
    return s, hit, sp_hit


def pure_bazi(dy, dm, dd):
    sc = defaultdict(float)
    score_chart(pillars_at(dy, dm, dd, 21), DRAW_W, sc)
    return pick15(dict(sc))


def pure_qimen(dy, dm, dd):
    sc = defaultdict(float)
    add_pan_scores(cast_qimen(dy, dm, dd, 21), Q_DRAW_W, sc)
    return pick15(dict(sc))


def parse_personal(s):
    p = s.replace("/", "-").replace(" ", "T")
    if "T" in p:
        date_part, time_part = p.split("T", 1)
        hh = int(time_part.split(":")[0])
    else:
        date_part, hh = p, 12
    y, m, d = map(int, date_part.split("-"))
    return y, m, d, hh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--personal", required=True)
    ap.add_argument("--n", type=int, default=100)
    args = ap.parse_args()
    py, pm, pd, ph = parse_personal(args.personal)

    with urllib.request.urlopen(URL, timeout=60) as resp:
        draws = json.loads(resp.read().decode("utf-8"))[-args.n :]

    keys = ["A_pure_bazi", "A_pure_qimen", "B_px_bazi", "B_px_qimen"]
    best = {k: None for k in keys}  # max record
    ge5 = {k: [] for k in keys}

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
            sc, hit, sp_hit = score(pred, nums, sp)
            rec = {
                "date": row["date"],
                "draw_no": row.get("no") or row.get("id") or row.get("period"),
                "score": sc,
                "numbers": nums,
                "special": sp,
                "pred": pred,
                "hit_zheng": hit,
                "hit_special": sp_hit,
            }
            if best[k] is None or sc > best[k]["score"]:
                best[k] = rec
            if sc >= 5.0:
                ge5[k].append(rec)

    print(
        json.dumps(
            {"personal": args.personal, "n": len(draws), "best": best, "ge5": ge5},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

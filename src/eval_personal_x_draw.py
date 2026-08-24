# -*- coding: utf-8 -*-
"""固定個人盤，對近 N 期攪珠做 15 碼字數回測。

用法:
  python src/eval_personal_x_draw.py --personal 1988-02-08T04:00 --n 100
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from personal_x_draw_bazi import generate as gen_bazi  # noqa: E402
from personal_x_draw_qimen import generate as gen_qimen  # noqa: E402

DEFAULT_URL = (
    "https://raw.githubusercontent.com/sleepingarhat/hk-mark-six-2002-now/main/data/mark-six.json"
)


def score(pred: list[int], numbers: list[int], special: int | None) -> float:
    s = float(len(set(pred) & set(numbers)))
    if special is not None and special in pred:
        s += 0.5
    return s


def load_draws(n: int) -> list:
    with urllib.request.urlopen(DEFAULT_URL, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data[-n:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--personal", required=True)
    ap.add_argument("--n", type=int, default=100)
    args = ap.parse_args()
    p = args.personal.replace("/", "-").replace(" ", "T")
    if "T" in p:
        date_part, time_part = p.split("T", 1)
        hh = int(time_part.split(":")[0])
    else:
        date_part, hh = p, 12
    py, pm, pd = map(int, date_part.split("-"))

    draws = load_draws(args.n)
    sum_b = sum_q = 0.0
    hit6_b = hit6_q = 0
    for row in draws:
        dy, dm, dd = map(int, row["date"].split("-"))
        nums = row["numbers"]
        # 數據可能無 special 或用 special / special_number
        sp = row.get("special") or row.get("special_number") or row.get("sp")
        if sp is None and len(nums) >= 7:
            sp = nums[6]
            nums = nums[:6]
        elif isinstance(nums, list) and len(nums) > 6:
            nums = nums[:6]

        rb = gen_bazi(py, pm, pd, hh, dy, dm, dd)
        rq = gen_qimen(py, pm, pd, hh, dy, dm, dd)
        sb = score(rb["numbers"], nums, sp)
        sq = score(rq["numbers"], nums, sp)
        sum_b += sb
        sum_q += sq
        if sb >= 6:
            hit6_b += 1
        if sq >= 6:
            hit6_q += 1

    n = len(draws)
    print(json.dumps(
        {
            "personal": args.personal,
            "n": n,
            "bazi": {
                "avg_score": round(sum_b / n, 3),
                "total": round(sum_b, 1),
                "ge6": hit6_b,
            },
            "qimen": {
                "avg_score": round(sum_q / n, 3),
                "total": round(sum_q, 1),
                "ge6": hit6_q,
            },
            "note": "隨機 15 碼期望約 15*6/49≈1.84 正碼；含特碼約再低",
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()

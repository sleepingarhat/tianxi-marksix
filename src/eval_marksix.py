# -*- coding: utf-8 -*-
"""100 期評估：pattern 分佈 + 用神河圖池蓋正碼率

用法:
  python src/eval_marksix.py
  python src/eval_marksix.py --data /path/to/mark-six.json
  python src/eval_marksix.py --url https://raw.githubusercontent.com/sleepingarhat/hk-mark-six-2002-now/main/data/mark-six.json
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

# 允許直接 python src/eval_marksix.py
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from yongshen_c import yongshen_c  # noqa: E402

DEFAULT_URL = (
    "https://raw.githubusercontent.com/sleepingarhat/hk-mark-six-2002-now/main/data/mark-six.json"
)


def nwx(n: int) -> str:
    t = n % 10
    return {1: "水", 6: "水", 2: "火", 7: "火", 3: "木", 8: "木", 4: "金", 9: "金"}.get(t, "土")


def pool(w: str) -> set[int]:
    return {n for n in range(1, 50) if nwx(n) == w}


def load_draws(path: str | None, url: str | None) -> list:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    u = url or DEFAULT_URL
    with urllib.request.urlopen(u, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description="tianxi-marksix 100期評估")
    ap.add_argument("--data", help="本地 mark-six.json 路徑")
    ap.add_argument("--url", default=DEFAULT_URL, help="遠端 JSON URL")
    ap.add_argument("--n", type=int, default=100, help="最近 N 期")
    ap.add_argument("--sample", default="2026-08-22", help="單盤示範 YYYY-MM-DD")
    args = ap.parse_args()

    y, m, d = map(int, args.sample.split("-"))
    sample = yongshen_c(y, m, d)
    print("=== sample", args.sample, "==="
    print(json.dumps(sample, ensure_ascii=False, indent=2))

    draws = load_draws(args.data, None if args.data else args.url)[-args.n :]
    pat: Counter[str] = Counter()
    hit = total = 0
    for row in draws:
        yy, mm, dd = map(int, row["date"].split("-"))
        r = yongshen_c(yy, mm, dd)
        pat[r["pattern"]["primary"]] += 1
        yp: set[int] = set()
        for w in r["yong_shen"]:
            yp |= pool(w)
        for n in row["numbers"]:
            total += 1
            if n in yp:
                hit += 1

    print("\n=== eval last", len(draws), "draws ===")
    print("pattern 分佈:")
    for k, v in pat.most_common():
        print(f"  {k}: {v}")
    print(f"用神池蓋正碼: {hit}/{total} = {hit / total * 100:.1f}%")
    print("(對照：舊簡表喜用約 40%；隨機兩行約 40%)")


if __name__ == "__main__":
    main()

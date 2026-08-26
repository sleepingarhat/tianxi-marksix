# -*- coding: utf-8 -*-
"""天喜大運入口（相容舊指令）。

完整算法見 tianxi_dayun.py / tianxi_engine.py。
用法:
  python src/dayun.py 1988 2 8 4 male
  python src/dayun.py --birth 1988-02-08T04:00 --sex male
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tianxi_calendar import parse_dt  # noqa: E402
from tianxi_dayun import build_dayun  # noqa: E402


def dayun(year: int, month: int, day: int, hour: int = 4, sex: str = "male", n: int = 8) -> dict:
    birth = datetime(year, month, day, hour, 0, 0)
    return build_dayun(birth, sex, n=n)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("用法: python src/dayun.py YYYY M D [hour] [male|female]")
        sys.exit(1)
    if args[0] == "--birth":
        from tianxi_dayun import main as new_main

        new_main()
        return
    y, m, d = int(args[0]), int(args[1]), int(args[2])
    hour = 4
    sex = "male"
    if len(args) > 3 and args[3].isdigit():
        hour = int(args[3])
    for a in args[3:]:
        if a.lower() in ("male", "female", "男", "女", "m", "f"):
            sex = a
    print(json.dumps(dayun(y, m, d, hour, sex), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

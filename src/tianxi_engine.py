# -*- coding: utf-8 -*-
"""天喜命盤總引擎 tianxi-mingpan-v1

合併：四柱 + 格局喜用 + 男女大運流年。
本版不改 15 碼取號；取號仍走 personal-x-draw-v1。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tianxi_calendar import parse_dt  # noqa: E402
from tianxi_dayun import build_dayun  # noqa: E402
from tianxi_geju import analyze_geju  # noqa: E402

ENGINE_ID = "tianxi-mingpan-v1"


def mingpan(
    birth: datetime,
    sex: str,
    at: datetime | None = None,
) -> dict[str, Any]:
    yun = build_dayun(birth, sex, at=at)
    ge = analyze_geju(yun["pillars"])
    return {
        "engineId": ENGINE_ID,
        "birth": yun["birth"],
        "sex": yun["sex"],
        "at": yun["at"],
        "pillars": yun["pillars"],
        "day_master": yun["day_master"],
        "pattern": ge["pattern"],
        "yong_shen": ge["yong_shen"],
        "xi_shen": ge["xi_shen"],
        "ji_shen": ge["ji_shen"],
        "chou_shen": ge["chou_shen"],
        "tiaohou": ge["tiaohou"],
        "zhong_gua": ge["zhong_gua"],
        "shi_shen": ge["shi_shen"],
        "dayun": {
            "direction": yun["direction"],
            "forward": yun["forward"],
            "jie": yun["jie"],
            "qiyun": yun["qiyun"],
            "qiyun_solar": yun["qiyun_solar"],
            "qiyun_note": yun["qiyun_note"],
            "current_dayun": yun["current_dayun"],
            "current_liunian": yun["current_liunian"],
            "rows": yun["dayun"],
            "liunian_in_current": yun["liunian_in_current"],
        },
        "note": ge["note"],
    }


def main() -> None:
    birth_s = sex = at_s = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--birth" and i + 1 < len(args):
            birth_s = args[i + 1]
            i += 2
        elif args[i] == "--sex" and i + 1 < len(args):
            sex = args[i + 1]
            i += 2
        elif args[i] == "--at" and i + 1 < len(args):
            at_s = args[i + 1]
            i += 2
        else:
            i += 1
    if not birth_s or not sex:
        print(
            "用法: python src/tianxi_engine.py --birth 1988-02-08T04:00 --sex male [--at 2026-08-22T21:30]"
        )
        sys.exit(1)
    at = parse_dt(at_s, 21) if at_s else None
    print(json.dumps(mingpan(parse_dt(birth_s, 4), sex, at=at), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

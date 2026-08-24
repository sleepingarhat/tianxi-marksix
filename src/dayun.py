# -*- coding: utf-8 -*-
"""大運：節氣起運歲數 + 順逆排柱

陽男陰女順行；陰男陽女逆行。
起運：順行取出生後下一個節；逆行取上一個節。
差日 / 3 → 年（餘數×4 → 月，粗算）。

用法:
  python src/dayun.py 1988 2 8 4 male
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import sxtwl
except ImportError as e:
    raise ImportError("需要 sxtwl") from e

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from yongshen_c import GAN, ZHI, WX_G, gz_str, yongshen_c  # noqa: E402

YANG_GAN = set("甲丙戊庚壬")

# 節（非中氣）：立春0 驚蟄2 清明4 立夏6 芒種8 小暑10 立秋12 白露14 寒露16 立冬18 大雪20 小寒22
JIE_INDEX = {0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22}


def _solar_date(y: int, m: int, d: int) -> date:
    return date(y, m, d)


def find_jie_around(year: int, month: int, day: int, forward: bool) -> tuple[date, str]:
    """找出生前後最近節（順=後，逆=前）。返回 (公曆日, 節名粗標)."""
    birth = _solar_date(year, month, day)
    # 掃前後 60 天內所有節
    candidates: list[tuple[date, int]] = []
    for delta in range(-50, 80):
        dt = birth + timedelta(days=delta)
        day_obj = sxtwl.fromSolar(dt.year, dt.month, dt.day)
        # sxtwl: hasJieQi / getJieQi 在當日是否交節
        if day_obj.hasJieQi():
            jq = day_obj.getJieQi()
            if jq in JIE_INDEX:
                candidates.append((dt, jq))

    if forward:
        after = [(d, j) for d, j in candidates if d > birth]
        if not after:
            raise RuntimeError("找不到出生後之節")
        d, j = min(after, key=lambda x: x[0])
    else:
        before = [(d, j) for d, j in candidates if d < birth]
        if not before:
            raise RuntimeError("找不到出生前之節")
        d, j = max(before, key=lambda x: x[0])
    return d, str(j)


def days_to_yun(days: int) -> tuple[int, int]:
    """差日→起運年、月（3日≈1年，1日≈4月）."""
    years = days // 3
    rem = days % 3
    months = rem * 4
    return years, months


def next_gz(gan: str, zhi: str, step: int) -> str:
    gi = (GAN.index(gan) + step) % 10
    zi = (ZHI.index(zhi) + step) % 12
    return GAN[gi] + ZHI[zi]


def dayun(
    year: int,
    month: int,
    day: int,
    hour: int = 4,
    sex: str = "male",
    n: int = 8,
) -> dict:
    chart = yongshen_c(year, month, day, hour)
    pillars = chart["pillars"]
    year_gan = pillars["year"][0]
    yang_year = year_gan in YANG_GAN
    # 陽男陰女順；陰男陽女逆
    if sex.lower() in ("m", "male", "男"):
        forward = yang_year
    else:
        forward = not yang_year

    jie_date, jie_id = find_jie_around(year, month, day, forward)
    birth = _solar_date(year, month, day)
    delta_days = abs((jie_date - birth).days)
    qiyun_y, qiyun_m = days_to_yun(delta_days)

    month_gz = pillars["month"]
    step = 1 if forward else -1
    rows = []
    for i in range(1, n + 1):
        gz = next_gz(month_gz[0], month_gz[1], step * i)
        start_age = qiyun_y + (i - 1) * 10
        # 起運月粗加到虛歲區間
        end_age = start_age + 9
        rows.append(
            {
                "index": i,
                "ganzhi": gz,
                "wx_gan": WX_G[gz[0]],
                "start_age": start_age,
                "end_age": end_age,
                "note": f"約{start_age}–{end_age}歲",
            }
        )

    return {
        "birth": f"{year:04d}-{month:02d}-{day:02d}",
        "sex": sex,
        "pillars": pillars,
        "day_master": chart["day_master"],
        "pattern": chart["pattern"],
        "yong_shen": chart["yong_shen"],
        "xi_shen": chart["xi_shen"],
        "ji_shen": chart["ji_shen"],
        "forward": forward,
        "jie_date": jie_date.isoformat(),
        "delta_days": delta_days,
        "qiyun": {"years": qiyun_y, "months": qiyun_m},
        "dayun": rows,
        "ruleNote": "起運歲數為節氣差日/3 粗算；大運十神未逐柱重算",
    }


def main() -> None:
    if len(sys.argv) < 4:
        print("用法: python src/dayun.py YYYY M D [hour] [male|female]")
        sys.exit(1)
    y, m, d = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    hour = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 4
    sex = "male"
    for a in sys.argv[4:]:
        if a.lower() in ("male", "female", "男", "女", "m", "f"):
            sex = a
    print(json.dumps(dayun(y, m, d, hour, sex), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

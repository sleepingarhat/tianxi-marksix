# -*- coding: utf-8 -*-
"""天喜大運流年引擎 tianxi-dayun-v2

陽男陰女順行，陰男陽女逆行（年干取立春年柱）。
起運只看十二節，分鐘折算：
  4320 分 = 1 年，360 分 = 1 月，12 分 = 1 日，餘分 ×2 = 時。
當運以交運公曆比較，不以整歲估。
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

from tianxi_calendar import (  # noqa: E402
    YANG_GAN,
    WX_G,
    add_ymdh,
    find_jie,
    next_gz,
    parse_dt,
    parse_sex,
    pillars_at,
    shi_shen_of,
    solar_to_jd,
    year_gz_lichun,
)

ENGINE_ID = "tianxi-dayun-v2"


def is_forward(year_gan: str, sex: str) -> bool:
    yang = year_gan in YANG_GAN
    male = parse_sex(sex) == "male"
    return (yang and male) or ((not yang) and (not male))


def qiyun_from_minutes(minutes: float) -> dict[str, int]:
    minutes = max(0, int(round(minutes)))
    years = minutes // 4320
    minutes -= years * 4320
    months = minutes // 360
    minutes -= months * 360
    days = minutes // 12
    minutes -= days * 12
    hours = minutes * 2
    return {
        "years": int(years),
        "months": int(months),
        "days": int(days),
        "hours": int(hours),
    }


def build_dayun(
    birth: datetime,
    sex: str,
    n: int = 8,
    at: datetime | None = None,
) -> dict[str, Any]:
    sex_n = parse_sex(sex)
    pillars = pillars_at(birth)
    year_gan = pillars["year"][0]
    forward = is_forward(year_gan, sex_n)
    jie_dt, jie_name = find_jie(birth, forward)
    if forward:
        start_pt, end_pt = birth, jie_dt
    else:
        start_pt, end_pt = jie_dt, birth
    minutes = (solar_to_jd(end_pt) - solar_to_jd(start_pt)) * 24 * 60
    qiyun = qiyun_from_minutes(minutes)
    start_solar = add_ymdh(
        birth, qiyun["years"], qiyun["months"], qiyun["days"], qiyun["hours"]
    )

    rows: list[dict[str, Any]] = []
    child_end = start_solar
    rows.append(
        {
            "index": 0,
            "kind": "童限",
            "ganzhi": pillars["month"],
            "wx_gan": WX_G[pillars["month"][0]],
            "shi_shen": shi_shen_of(pillars["day"][0], pillars["month"][0]),
            "start_solar": birth.isoformat(timespec="seconds"),
            "end_solar": child_end.isoformat(timespec="seconds"),
            "start_year": birth.year,
            "end_year": child_end.year if child_end.year >= birth.year else birth.year,
            "xu_sui_start": 1,
            "xu_sui_end": max(1, start_solar.year - birth.year),
        }
    )
    step = 1 if forward else -1
    for i in range(1, n + 1):
        gz = next_gz(pillars["month"], step * i)
        st = add_ymdh(start_solar, (i - 1) * 10, 0, 0, 0)
        ed = add_ymdh(start_solar, i * 10, 0, 0, 0)
        rows.append(
            {
                "index": i,
                "kind": "大運",
                "ganzhi": gz,
                "wx_gan": WX_G[gz[0]],
                "shi_shen": shi_shen_of(pillars["day"][0], gz[0]),
                "start_solar": st.isoformat(timespec="seconds"),
                "end_solar": ed.isoformat(timespec="seconds"),
                "start_year": st.year,
                "end_year": ed.year - 1,
                "xu_sui_start": st.year - birth.year + 1,
                "xu_sui_end": st.year - birth.year + 10,
            }
        )

    at_dt = at or datetime.now()
    current = rows[0]
    for row in rows:
        st = datetime.fromisoformat(row["start_solar"])
        ed = datetime.fromisoformat(row["end_solar"])
        if st <= at_dt < ed:
            current = row
            break
    else:
        current = rows[-1]

    ln_start = datetime.fromisoformat(current["start_solar"]).year
    ln_end = datetime.fromisoformat(current["end_solar"]).year
    liunian = []
    for y in range(ln_start, ln_end + 1):
        gz = year_gz_lichun(y)
        liunian.append(
            {
                "year": y,
                "ganzhi": gz,
                "wx_gan": WX_G[gz[0]],
                "shi_shen": shi_shen_of(pillars["day"][0], gz[0]),
                "current": y == at_dt.year,
            }
        )
    at_ln = year_gz_lichun(at_dt.year)

    return {
        "engineId": ENGINE_ID,
        "birth": birth.isoformat(timespec="seconds"),
        "sex": sex_n,
        "pillars": pillars,
        "day_master": {"gan": pillars["day"][0], "wx": WX_G[pillars["day"][0]]},
        "year_gan_yang": year_gan in YANG_GAN,
        "forward": forward,
        "direction": "順行" if forward else "逆行",
        "jie": {"name": jie_name, "datetime": jie_dt.isoformat(timespec="seconds")},
        "delta_minutes": int(round(minutes)),
        "qiyun": qiyun,
        "qiyun_solar": start_solar.isoformat(timespec="seconds"),
        "qiyun_note": f"{qiyun['years']}年{qiyun['months']}個月{qiyun['days']}日{qiyun['hours']}時後起運",
        "at": at_dt.isoformat(timespec="seconds"),
        "current_dayun": {
            "index": current["index"],
            "kind": current["kind"],
            "ganzhi": current["ganzhi"],
            "shi_shen": current["shi_shen"],
            "start_solar": current["start_solar"],
            "end_solar": current["end_solar"],
            "xu_sui": f"{current['xu_sui_start']}–{current['xu_sui_end']}歲",
        },
        "current_liunian": {
            "year": at_dt.year,
            "ganzhi": at_ln,
            "shi_shen": shi_shen_of(pillars["day"][0], at_ln[0]),
        },
        "dayun": rows,
        "liunian_in_current": liunian,
    }


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "用法: python src/tianxi_dayun.py --birth 1988-02-08T04:00 --sex male [--at 2026-08-22T21:30]"
        )
        sys.exit(1)
    args = sys.argv[1:]
    birth_s = sex = at_s = None
    i = 0
    while i < len(args):
        if args[i] == "--birth":
            birth_s = args[i + 1]
            i += 2
        elif args[i] == "--sex":
            sex = args[i + 1]
            i += 2
        elif args[i] == "--at":
            at_s = args[i + 1]
            i += 2
        else:
            i += 1
    if not birth_s or not sex:
        raise SystemExit("必須提供 --birth 與 --sex")
    at = parse_dt(at_s, 21) if at_s else None
    print(json.dumps(build_dayun(parse_dt(birth_s, 4), sex, at=at), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""天喜節氣對照 tianxi-jieqi-check-v1

sxtwl.getJieQiByYear × 逐日 hasJieQi 掃描 ×（可選）tyme4py / lunar-python。
用來鎖定起運所依之十二節交節制。
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
    JIE_INDEX,
    JQ_NAMES,
    find_jie,
    jd_to_dt,
    list_jieqi_year,
    parse_dt,
)

ENGINE_ID = "tianxi-jieqi-check-v1"
TOLERANCE_SEC = 2

# lunar-python 用簡體節名
_SIMP = {
    "驚蟲": "惊蛰",
    "穀雨": "谷雨",
    "小滿": "小满",
    "處暑": "处暑",
}


def _scan_year(year: int) -> dict[str, datetime]:
    import sxtwl

    found: dict[str, datetime] = {}
    cur = sxtwl.fromSolar(year, 1, 1)
    for _ in range(430):
        if cur.hasJieQi():
            idx = int(cur.getJieQi()) % 24
            dt = jd_to_dt(cur.getJieQiJD())
            if year <= dt.year <= year + 1:
                found[f"{JQ_NAMES[idx]}|{dt.year}-{dt.month:02d}-{dt.day:02d}"] = dt
        cur = cur.after(1)
        if cur.getSolarYear() > year + 1:
            break
    return found


def _tyme_table(year: int) -> dict[str, datetime]:
    try:
        from tyme4py.solar import SolarTerm
    except ImportError:
        return {}
    out: dict[str, datetime] = {}
    # index 0 = 該年冬至；立春約在 index 3
    term = SolarTerm.from_name(year, "立春")
    for _ in range(25):
        jd = term.get_julian_day()
        st = jd.get_solar_time()
        dt = datetime(st.get_year(), st.get_month(), st.get_day(), st.get_hour(), st.get_minute(), st.get_second())
        out[term.get_name()] = dt
        term = term.next(1)
    return out


def _lunar_table(year: int) -> dict[str, datetime]:
    try:
        from lunar_python import Solar
    except ImportError:
        return {}
    table = Solar.fromYmd(year, 6, 1).getLunar().getJieQiTable()
    out: dict[str, datetime] = {}
    for trad in JQ_NAMES:
        key = _SIMP.get(trad, trad)
        sol = table.get(key) or table.get(trad)
        if sol is None:
            continue
        out[trad] = datetime(
            sol.getYear(), sol.getMonth(), sol.getDay(),
            sol.getHour(), sol.getMinute(), sol.getSecond(),
        )
    return out


def _delta_sec(a: datetime, b: datetime) -> int:
    return abs(int((a - b).total_seconds()))


def check_year(year: int) -> dict[str, Any]:
    official = list_jieqi_year(year)
    scanned = _scan_year(year)
    tyme = _tyme_table(year)
    lunar = _lunar_table(year)
    diffs: list[dict[str, Any]] = []
    max_scan = 0
    max_tyme = 0
    max_lunar = 0
    for row in official:
        dt = datetime.fromisoformat(row["datetime"])
        key = f"{row['name']}|{dt.year}-{dt.month:02d}-{dt.day:02d}"
        scan_dt = scanned.get(key)
        item: dict[str, Any] = {
            "name": row["name"],
            "is_jie": row["is_jie"],
            "sxtwl": row["datetime"],
        }
        if scan_dt is not None:
            d = _delta_sec(dt, scan_dt)
            max_scan = max(max_scan, d)
            item["scan"] = scan_dt.isoformat(timespec="seconds")
            item["scan_delta_sec"] = d
        tdt = tyme.get(row["name"])
        if tdt is not None:
            # tyme 可能跟下一年同名節衝突；只比較同一公曆日
            if tdt.date() == dt.date() or abs((tdt - dt).days) <= 1:
                d = _delta_sec(dt, tdt)
                max_tyme = max(max_tyme, d)
                item["tyme"] = tdt.isoformat(timespec="seconds")
                item["tyme_delta_sec"] = d
        ldt = lunar.get(row["name"])
        if ldt is not None and (ldt.date() == dt.date() or abs((ldt - dt).days) <= 1):
            d = _delta_sec(dt, ldt)
            max_lunar = max(max_lunar, d)
            item["lunar"] = ldt.isoformat(timespec="seconds")
            item["lunar_delta_sec"] = d
        diffs.append(item)

    # 起運用的 find_jie ：1988-02-08 04:00 順=驚蟲 逆=立春
    sample_birth = datetime(year, 2, 8, 4, 0, 0) if year != 1988 else datetime(1988, 2, 8, 4, 0, 0)
    nxt, nxt_name = find_jie(sample_birth, True)
    prv, prv_name = find_jie(sample_birth, False)
    jie_ok = nxt_name in JQ_NAMES and prv_name in JQ_NAMES
    ok = max_scan <= TOLERANCE_SEC and jie_ok
    if tyme:
        ok = ok and max_tyme <= TOLERANCE_SEC
    if lunar:
        ok = ok and max_lunar <= TOLERANCE_SEC
    return {
        "engineId": ENGINE_ID,
        "year": year,
        "count": len(official),
        "jie_count": sum(1 for r in official if r["is_jie"]),
        "max_scan_delta_sec": max_scan,
        "max_tyme_delta_sec": max_tyme if tyme else None,
        "max_lunar_delta_sec": max_lunar if lunar else None,
        "sources": {
            "sxtwl": True,
            "day_scan": True,
            "tyme4py": bool(tyme),
            "lunar_python": bool(lunar),
        },
        "sample_find_jie": {
            "birth": sample_birth.isoformat(timespec="seconds"),
            "next_jie": {"name": nxt_name, "datetime": nxt.isoformat(timespec="seconds")},
            "prev_jie": {"name": prv_name, "datetime": prv.isoformat(timespec="seconds")},
        },
        "ok": ok,
        "tolerance_sec": TOLERANCE_SEC,
        "terms": diffs,
    }


def main() -> None:
    year = 2026
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        year = int(sys.argv[1])
    elif "--year" in sys.argv:
        i = sys.argv.index("--year")
        year = int(sys.argv[i + 1])
    out = check_year(year)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if not out["ok"]:
        sys.exit(2)


if __name__ == "__main__":
    main()

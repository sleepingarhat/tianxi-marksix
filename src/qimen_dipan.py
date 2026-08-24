# -*- coding: utf-8 -*-
"""時家奇門：置閏定局 + 地盤 + 值符（取數）

rule: qimen-zhirun-v1
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

try:
    import sxtwl
except ImportError as e:
    raise ImportError("需要 sxtwl") from e

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
YI_ORDER = list("戊己庚辛壬癸丁丙乙")

JQ_NAME = [
    "立春", "雨水", "驚蟄", "春分", "清明", "穀雨",
    "立夏", "小滿", "芒種", "夏至", "小暑", "大暑",
    "立秋", "處暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]

# 近似月日（再 ±3 天用 sxtwl 對真）
JQ_APPROX = {
    0: (2, 4), 1: (2, 19), 2: (3, 6), 3: (3, 21), 4: (4, 5), 5: (4, 20),
    6: (5, 6), 7: (5, 21), 8: (6, 6), 9: (6, 21), 10: (7, 7), 11: (7, 23),
    12: (8, 8), 13: (8, 23), 14: (9, 8), 15: (9, 23), 16: (10, 8), 17: (10, 23),
    18: (11, 7), 19: (11, 22), 20: (12, 7), 21: (12, 22), 22: (1, 6), 23: (1, 20),
}

YANG_JU = {
    "冬至": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6),
    "立春": (8, 5, 2), "雨水": (9, 6, 3), "驚蟄": (1, 7, 4),
    "春分": (3, 9, 6), "清明": (2, 8, 5), "穀雨": (3, 9, 6),
    "立夏": (4, 1, 7), "小滿": (5, 2, 8), "芒種": (6, 3, 9),
}
YIN_JU = {
    "夏至": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4),
    "立秋": (2, 5, 8), "處暑": (1, 4, 7), "白露": (9, 3, 6),
    "秋分": (7, 1, 4), "寒露": (8, 2, 5), "霜降": (7, 1, 4),
    "立冬": (6, 9, 3), "小雪": (5, 8, 2), "大雪": (4, 7, 1),
}

_JQ_CACHE: dict[tuple[int, int], date] = {}


def gz_str(gz) -> str:
    return GAN[gz.tg] + ZHI[gz.dz]


def _solar(y: int, m: int, d: int):
    return sxtwl.fromSolar(y, m, d)


def _jq_date_fast(y: int, jq_index: int) -> date:
    key = (y, jq_index)
    if key in _JQ_CACHE:
        return _JQ_CACHE[key]
    mm, dd = JQ_APPROX[jq_index]
    yy = y
    # 小寒大寒屬「冬至後」常落在 y+1 年 1 月——此處 y 已是目標公曆年
    base = date(yy, mm, dd)
    found = base
    for delta in range(-4, 5):
        dt = base + timedelta(days=delta)
        try:
            day = sxtwl.fromSolar(dt.year, dt.month, dt.day)
            if day.hasJieQi() and day.getJieQi() == jq_index:
                found = dt
                break
        except Exception:
            continue
    _JQ_CACHE[key] = found
    return found


def _find_current_jie(y: int, m: int, d: int) -> tuple[str, date, bool]:
    target = date(y, m, d)
    candidates: list[tuple[date, int, str]] = []
    for yy in (y - 1, y, y + 1):
        for ji in range(24):
            jd = _jq_date_fast(yy, ji)
            candidates.append((jd, ji, JQ_NAME[ji]))
    candidates.sort(key=lambda x: x[0])
    cur = None
    for item in candidates:
        if item[0] <= target:
            cur = item
        else:
            break
    if cur is None:
        return "冬至", date(y, 12, 22), True
    jd, ji, name = cur
    yang = True
    for jd2, ji2, _ in reversed([c for c in candidates if c[0] <= target]):
        if ji2 == 21:
            yang = True
            break
        if ji2 == 9:
            yang = False
            break
    return name, jd, yang


def fu_tou_date(y: int, m: int, d: int) -> date:
    for back in range(0, 15):
        dt = date(y, m, d) - timedelta(days=back)
        if _solar(dt.year, dt.month, dt.day).getDayGZ().tg in (0, 5):
            return dt
    return date(y, m, d)


def yuan_and_ju_zhirun(y: int, m: int, d: int) -> tuple[bool, int, str, dict]:
    name, jie_start, yang = _find_current_jie(y, m, d)
    table = YANG_JU if yang else YIN_JU
    ft = fu_tou_date(y, m, d)
    zhirun = False
    if ft < jie_start:
        zhirun = True
        prev = jie_start - timedelta(days=1)
        name, jie_start, yang = _find_current_jie(prev.year, prev.month, prev.day)
        table = YANG_JU if yang else YIN_JU

    if name not in table:
        # 中氣：併入同遁上一個表內節
        name = list(table.keys())[0]
        for k in table:
            name = k  # 最後一個可用；更佳：按時間
        # 用當前節氣名模糊
        for k in table:
            if k[0] == name[0]:
                name = k
                break

    days_into = (date(y, m, d) - jie_start).days
    if days_into < 5:
        yuan, yi = "上元", 0
    elif days_into < 10:
        yuan, yi = "中元", 1
    else:
        yuan, yi = "下元", 2

    ju = table.get(name, (1, 7, 4))[yi]
    meta = {
        "jie": name,
        "jie_start": str(jie_start),
        "fu_tou": str(ft),
        "zhirun": zhirun,
        "days_into_jie": days_into,
        "method": "zhirun",
    }
    return yang, ju, yuan, meta


def arrange_di_pan(yang: bool, ju: int) -> dict[int, str]:
    path = [1, 8, 3, 4, 9, 2, 7, 6]
    start_idx = path.index(ju) if ju in path else 0
    if ju == 5:
        start_idx = path.index(2)
    di: dict[int, str] = {}
    for i, yi in enumerate(YI_ORDER):
        palace = path[(start_idx + i) % 8] if yang else path[(start_idx - i) % 8]
        di[palace] = yi
    di[5] = di.get(2, "戊")
    return di


def xun_shou_yi(day_gan_zhi: str) -> str:
    gan, zhi = day_gan_zhi[0], day_gan_zhi[1]
    idx = 0
    for i in range(60):
        if GAN[i % 10] == gan and ZHI[i % 12] == zhi:
            idx = i
            break
    return "戊己庚辛壬癸"[idx // 10]


@dataclass
class QimenPan:
    yang: bool
    ju: int
    yuan: str
    pillars: dict[str, str]
    di_pan: dict[int, str]
    zhi_fu_palace: int
    zhi_fu_origin: int
    meta: dict


def cast_qimen(y: int, m: int, d: int, hour: int) -> QimenPan:
    day = _solar(y, m, d)
    pillars = {
        "year": gz_str(day.getYearGZ(False)),
        "month": gz_str(day.getMonthGZ()),
        "day": gz_str(day.getDayGZ()),
        "hour": gz_str(day.getHourGZ(hour)),
    }
    yang, ju, yuan, meta = yuan_and_ju_zhirun(y, m, d)
    di = arrange_di_pan(yang, ju)
    yi0 = xun_shou_yi(pillars["day"])
    origin = 5
    for p, g in di.items():
        if g == yi0 and p != 5:
            origin = p
            break
    hg = pillars["hour"][0]
    target = yi0 if hg == "甲" else (hg if hg in YI_ORDER else yi0)
    zf = origin
    for p, g in di.items():
        if g == target and p != 5:
            zf = p
            break
    return QimenPan(yang, ju, yuan, pillars, di, zf, origin, meta)


def pan_to_dict(p: QimenPan) -> dict[str, Any]:
    return {
        "yang_dun": p.yang,
        "ju": p.ju,
        "yuan": p.yuan,
        "pillars": p.pillars,
        "di_pan": {str(k): v for k, v in p.di_pan.items()},
        "zhi_fu_palace": p.zhi_fu_palace,
        "zhi_fu_origin": p.zhi_fu_origin,
        "meta": p.meta,
    }

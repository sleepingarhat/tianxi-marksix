# -*- coding: utf-8 -*-
"""時家奇門：置閏定局 + 地盤三奇六儀 + 值符宮（取數用）

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

# 十二節（只用節，不用中氣）對應 sxtwl 節氣序：偶數多為節
# sxtwl: 0立春 1雨水 2驚蟄 3春分 4清明 5穀雨 6立夏 7小滿 8芒種 9夏至
# 10小暑 11大暑 12立秋 13處暑 14白露 15秋分 16寒露 17霜降 18立冬 19小雪 20大雪 21冬至 22小寒 23大寒
JIE_IDX = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]  # 立春…大雪 的「節」；冬至=21 另作陽遁起

# 局數表：(陽遁?, 節名) -> (上,中,下)
# 陽遁：冬至→夏至前；陰遁：夏至→冬至前
YANG_JU = {
    "冬至": (1, 7, 4),
    "小寒": (2, 8, 5),
    "大寒": (3, 9, 6),
    "立春": (8, 5, 2),
    "雨水": (9, 6, 3),
    "驚蟄": (1, 7, 4),
    "春分": (3, 9, 6),
    "清明": (2, 8, 5),
    "穀雨": (3, 9, 6),
    "立夏": (4, 1, 7),
    "小滿": (5, 2, 8),
    "芒種": (6, 3, 9),
}
YIN_JU = {
    "夏至": (9, 3, 6),
    "小暑": (8, 2, 5),
    "大暑": (7, 1, 4),
    "立秋": (2, 5, 8),
    "處暑": (1, 4, 7),
    "白露": (9, 3, 6),
    "秋分": (7, 1, 4),
    "寒露": (8, 2, 5),
    "霜降": (7, 1, 4),
    "立冬": (6, 9, 3),
    "小雪": (5, 8, 2),
    "大雪": (4, 7, 1),
}

JQ_NAME = [
    "立春", "雨水", "驚蟄", "春分", "清明", "穀雨",
    "立夏", "小滿", "芒種", "夏至", "小暑", "大暑",
    "立秋", "處暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]


def gz_str(gz) -> str:
    return GAN[gz.tg] + ZHI[gz.dz]


def _solar(y: int, m: int, d: int):
    return sxtwl.fromSolar(y, m, d)


def _jq_date(y: int, jq_index: int) -> date:
    """該年某節氣的公曆日（sxtwl getJieQiByYear 或掃日）。"""
    # sxtwl 2.x: fromSolar + getJieQi / 用年內搜
    for m in range(1, 13):
        for d in range(1, 32):
            try:
                day = sxtwl.fromSolar(y, m, d)
            except Exception:
                continue
            # 當日是否為該節氣
            # sxtwl Day: getJie() / hasJieQi
            try:
                if day.hasJieQi():
                    jq = day.getJieQi()
                    if jq == jq_index:
                        return date(y, m, d)
            except Exception:
                pass
    # fallback 近似
    approx = {
        0: (2, 4), 2: (3, 6), 4: (4, 5), 6: (5, 6), 8: (6, 6), 9: (6, 21),
        10: (7, 7), 12: (8, 8), 14: (9, 8), 15: (9, 23), 16: (10, 8),
        18: (11, 7), 20: (12, 7), 21: (12, 22), 22: (1, 6), 23: (1, 20),
    }
    mm, dd = approx.get(jq_index, (6, 21))
    yy = y if mm != 1 or jq_index < 22 else y + 1
    if jq_index in (22, 23) and m == 1:
        yy = y
    return date(yy, mm, dd)


def _find_current_jie(y: int, m: int, d: int) -> tuple[str, date, bool]:
    """返回 (節名, 節起始日, 是否陽遁)."""
    target = date(y, m, d)
    # 掃前後年所有節氣日，取 ≤ target 最近一個「用於定局」的氣（節+冬至夏至）
    candidates: list[tuple[date, int, str]] = []
    for yy in (y - 1, y, y + 1):
        for ji in range(24):
            try:
                jd = _jq_date_fast(yy, ji)
            except Exception:
                continue
            if jd is None:
                continue
            name = JQ_NAME[ji]
            candidates.append((jd, ji, name))
    candidates.sort(key=lambda x: x[0])
    cur = None
    for jd, ji, name in candidates:
        if jd <= target:
            cur = (jd, ji, name)
        else:
            break
    if cur is None:
        return "冬至", date(y, 12, 22), True
    jd, ji, name = cur
    # 陽遁：冬至(21)起至夏至前；陰遁：夏至(9)起至冬至前
    yang = True
    for jd2, ji2, name2 in reversed([c for c in candidates if c[0] <= target]):
        if ji2 == 21:  # 冬至
            yang = True
            break
        if ji2 == 9:  # 夏至
            yang = False
            break
    return name, jd, yang


_JQ_CACHE: dict[tuple[int, int], date] = {}


def _jq_date_fast(y: int, jq_index: int) -> date | None:
    key = (y, jq_index)
    if key in _JQ_CACHE:
        return _JQ_CACHE[key]
    # 用 sxtwl 逐日：只掃該節大概月份
    month_hint = {
        0: 2, 1: 2, 2: 3, 3: 3, 4: 4, 5: 4, 6: 5, 7: 5, 8: 6, 9: 6,
        10: 7, 11: 7, 12: 8, 13: 8, 14: 9, 15: 9, 16: 10, 17: 10,
        18: 11, 19: 11, 20: 12, 21: 12, 22: 1, 23: 1,
    }[jq_index]
    years = [y]
    if jq_index in (22, 23):
        years = [y, y + 1]
    for yy in years:
        for m in {month_hint, month_hint % 12 + 1}:
            for d in range(1, 32):
                try:
                    day = sxtwl.fromSolar(yy, m, d)
                except Exception:
                    continue
                try:
                    if day.hasJieQi() and day.getJieQi() == jq_index:
                        dt = date(yy, m, d)
                        _JQ_CACHE[key] = dt
                        return dt
                except Exception:
                    continue
    return None


def fu_tou_date(y: int, m: int, d: int) -> date:
    """往前含當日最近甲／己日。"""
    for back in range(0, 15):
        dt = date(y, m, d) - timedelta(days=back)
        g = _solar(dt.year, dt.month, dt.day).getDayGZ().tg
        if g in (0, 5):
            return dt
    return date(y, m, d)


def yuan_and_ju_zhirun(y: int, m: int, d: int) -> tuple[bool, int, str, dict]:
    """置閏定局。返回 (陽遁?, 局數, 元, meta)."""
    name, jie_start, yang = _find_current_jie(y, m, d)
    table = YANG_JU if yang else YIN_JU
    # 若節名不在表（中氣），映射到上一節名已在 _find 用節氣名
    if name not in table:
        # 中氣：用上一節表項——簡化：找同遁最近表鍵
        for k in table:
            if k in name or name in k:
                name = k
                break
        else:
            # fallback 按公曆月
            name = list(table.keys())[min((m - 1) % 12, len(table) - 1)]

    ft = fu_tou_date(y, m, d)
    # 距本節起始天數
    days_into = (date(y, m, d) - jie_start).days
    # 置閏：符頭在節前（超神）→ 仍用上一節下元局，直到符頭過節
    zhirun = False
    if ft < jie_start:
        zhirun = True
        # 用上一節
        prev = jie_start - timedelta(days=1)
        name, jie_start, yang = _find_current_jie(prev.year, prev.month, prev.day)
        table = YANG_JU if yang else YIN_JU
        if name not in table:
            name = list(table.keys())[0]
        days_into = (date(y, m, d) - jie_start).days

    # 三元：每 5 日；置閏時下元可延長（超 15 仍算下元）
    if days_into < 5:
        yuan, yi = "上元", 0
    elif days_into < 10:
        yuan, yi = "中元", 1
    else:
        yuan, yi = "下元", 2

    ju_triple = table.get(name, (1, 7, 4))
    ju = ju_triple[yi]
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
        if yang:
            palace = path[(start_idx + i) % 8]
        else:
            palace = path[(start_idx - i) % 8]
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
    return QimenPan(
        yang=yang,
        ju=ju,
        yuan=yuan,
        pillars=pillars,
        di_pan=di,
        zhi_fu_palace=zf,
        zhi_fu_origin=origin,
        meta=meta,
    )


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

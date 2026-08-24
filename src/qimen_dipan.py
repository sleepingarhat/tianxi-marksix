# -*- coding: utf-8 -*-
"""時家奇門：拆補定局 + 地盤三奇六儀 + 值符宮（取數用）

簡化可重現版；天盤／八神可略。
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
# 洛書宮序（後天）：1坎 2坤 3震 4巽 5中 6乾 7兌 8艮 9離
PALACE = [1, 8, 3, 4, 9, 2, 7, 6]  # 陽遁布儀順行用嘅宮序（跳中）
# 三奇六儀序：戊己庚辛壬癸丁丙乙
YI_ORDER = list("戊己庚辛壬癸丁丙乙")

# 節氣 index（sxtwl）：0立春 … 各節入氣；用「中氣後到下節」粗分陰陽遁
# 陽遁：冬至→夏至前；陰遁：夏至→冬至前（常見時家）
# sxtwl JieQi: 0立春 1雨水 … 12立秋 … 18冬至?
# 用「距冬至／夏至」簡判：日柱序 + 近似


def gz_str(gz) -> str:
    return GAN[gz.tg] + ZHI[gz.dz]


def _solar(y: int, m: int, d: int):
    return sxtwl.fromSolar(y, m, d)


def is_yang_dun(y: int, m: int, d: int) -> bool:
    """冬至後至夏至前為陽遁，否則陰遁（按公曆近似節氣日）。"""
    # 粗表：北半球常見
    # 夏至約 6/21，冬至約 12/22
    md = m * 100 + d
    if md >= 1222 or md < 621:
        return True
    return False


def fu_tou_offset(y: int, m: int, d: int) -> int:
    """符頭：往前含當日最近甲／己日，返回距符頭日數 0..14 循環感。"""
    day = _solar(y, m, d)
    dg = day.getDayGZ()
    # 日干 甲=0 己=5
    tg = dg.tg
    # 往前找到甲或己
    for back in range(0, 15):
        dt = date(y, m, d) - timedelta(days=back)
        g = _solar(dt.year, dt.month, dt.day).getDayGZ().tg
        if g in (0, 5):  # 甲己
            return back
    return 0


def yuan_and_ju(y: int, m: int, d: int) -> tuple[bool, int, str]:
    """返回 (陽遁?, 局數1-9, 上中下元)."""
    yang = is_yang_dun(y, m, d)
    off = fu_tou_offset(y, m, d)
    if off <= 4:
        yuan = "上元"
        yuan_i = 0
    elif off <= 9:
        yuan = "中元"
        yuan_i = 1
    else:
        yuan = "下元"
        yuan_i = 2
    # 簡表：按節氣月粗定局數基值，再按元微調（可重現固定表）
    # 用「日序 mod」穩定出 1-9，並用元偏移
    day = _solar(y, m, d)
    base = (day.getDayGZ().tg + day.getDayGZ().dz + (0 if yang else 3)) % 9 + 1
    ju = (base + yuan_i * 3 - 1) % 9 + 1
    return yang, ju, yuan


def arrange_di_pan(yang: bool, ju: int) -> dict[int, str]:
    """地盤：戊起於局數宮，陽順陰逆布九儀。"""
    # 宮走法：陽 1-8-3-4-9-2-7-6（再回），陰逆
    path = [1, 8, 3, 4, 9, 2, 7, 6]
    # 中宮5寄坤2（常用）
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
    di[5] = di.get(2, "戊")  # 中寄
    return di


def xun_shou_yi(day_gan_zhi: str) -> str:
    """時旬首對應六儀（簡：由日柱推旬，再用時干）。此處用日干支粗定。"""
    # 六十甲子旬首六甲：甲子戊、甲戌己、甲申庚、甲午辛、甲辰壬、甲寅癸
    gan, zhi = day_gan_zhi[0], day_gan_zhi[1]
    gi, zi = GAN.index(gan), ZHI.index(zhi)
    # 距甲子
    idx = 0
    for i in range(60):
        if GAN[i % 10] == gan and ZHI[i % 12] == zhi:
            idx = i
            break
    xun = idx // 10  # 0..5
    return "戊己庚辛壬癸"[xun]


@dataclass
class QimenPan:
    yang: bool
    ju: int
    yuan: str
    pillars: dict[str, str]
    di_pan: dict[int, str]  # palace -> 干
    zhi_fu_palace: int
    zhi_fu_origin: int


def cast_qimen(y: int, m: int, d: int, hour: int) -> QimenPan:
    day = _solar(y, m, d)
    pillars = {
        "year": gz_str(day.getYearGZ(False)),
        "month": gz_str(day.getMonthGZ()),
        "day": gz_str(day.getDayGZ()),
        "hour": gz_str(day.getHourGZ(hour)),
    }
    yang, ju, yuan = yuan_and_ju(y, m, d)
    di = arrange_di_pan(yang, ju)
    # 值符原宮：旬首六儀落宮
    yi0 = xun_shou_yi(pillars["day"])
    origin = 5
    for p, g in di.items():
        if g == yi0 and p != 5:
            origin = p
            break
    # 值符宮：時干（甲則用旬首儀）在地盤之宮
    hg = pillars["hour"][0]
    if hg == "甲":
        target = yi0
    else:
        target = hg if hg in YI_ORDER else yi0
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
    }

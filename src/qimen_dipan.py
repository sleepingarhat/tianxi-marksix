# -*- coding: utf-8 -*-
"""時家奇門：拆補定局 + 地盤／值符 + 時乾落宮字尾取數

rule: qimen-chaibu-v2
定局參考：符頭地支定上中下元；交節即用本節局（不置閏）。
取數參考：https://www.qimenpai.com/blog/719
  - 時乾落宮字尾數為主池
  - 地盤／宮先天後天／天干數等公式擴池
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
SAN_QI = set("乙丙丁")

JQ_NAME = [
    "立春", "雨水", "驚蟄", "春分", "清明", "穀雨",
    "立夏", "小滿", "芒種", "夏至", "小暑", "大暑",
    "立秋", "處暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]
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

# 拆補：符頭地支 → 元（0上 1中 2下）
# 子午卯酉上；寅申巳亥中；辰戌丑未下
FU_ZHI_YUAN = {
    "子": 0, "午": 0, "卯": 0, "酉": 0,
    "寅": 1, "申": 1, "巳": 1, "亥": 1,
    "辰": 2, "戌": 2, "丑": 2, "未": 2,
}

# 後天宮數（洛書）：坎1 坤2 震3 巽4 中5 乾6 兌7 艮8 離9
PALACE_HOUTIAN = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
# 先天數（文章表：坎6 坤8 震4 巽5 乾1 兌2 艮7 離3）
PALACE_XIAN_TIAN = {1: 6, 2: 8, 3: 4, 4: 5, 5: 5, 6: 1, 7: 2, 8: 7, 9: 3}

# 各宮字尾數（奇門派彩券文）
PALACE_TAILS: dict[int, list[int]] = {
    1: [1, 6, 8],           # 坎
    8: [4, 5, 0, 7, 8],     # 艮
    3: [3, 8, 4],           # 震
    4: [3, 8, 4, 5, 2],     # 巽
    9: [2, 7, 9, 3, 1],     # 離
    2: [5, 0, 2, 8],        # 坤
    7: [4, 9, 2, 7, 6],     # 兌
    6: [4, 9, 6, 7, 1],     # 乾
    5: [5, 0],              # 中
}

# 十天干數（文：甲1/9 乙2…癸10）
GAN_NUMS: dict[str, list[int]] = {
    "甲": [1, 9], "乙": [2], "丙": [3], "丁": [4], "戊": [5],
    "己": [6], "庚": [7], "辛": [8], "壬": [9], "癸": [10],
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
    base = date(y, mm, dd)
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
            candidates.append((_jq_date_fast(yy, ji), ji, JQ_NAME[ji]))
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
    for _jd2, ji2, _ in reversed([c for c in candidates if c[0] <= target]):
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


def _resolve_ju_key(name: str, table: dict) -> str:
    if name in table:
        return name
    for k in table:
        if k[0] == name[0]:
            return k
    return list(table.keys())[0]


def yuan_and_ju_chaibu(y: int, m: int, d: int) -> tuple[bool, int, str, dict]:
    """拆補定局（v2）。

    1. 當日所在節氣 → 陽／陰遁與局表
    2. 符頭（甲／己日）地支 → 上中下元
       子午卯酉上；寅申巳亥中；辰戌丑未下
    3. 不置閏：超神只記錄，局仍用本節
    """
    name, jie_start, yang = _find_current_jie(y, m, d)
    table = YANG_JU if yang else YIN_JU
    key = _resolve_ju_key(name, table)
    ft = fu_tou_date(y, m, d)
    ft_day = _solar(ft.year, ft.month, ft.day)
    ft_gz = gz_str(ft_day.getDayGZ())
    ft_zhi = ft_gz[1]
    yi = FU_ZHI_YUAN.get(ft_zhi, 0)
    yuan = ["上元", "中元", "下元"][yi]
    ju = table[key][yi]
    target = date(y, m, d)
    meta = {
        "jie": name,
        "ju_key": key,
        "jie_start": str(jie_start),
        "fu_tou": str(ft),
        "fu_tou_gz": ft_gz,
        "yuan_by": "fu_tou_zhi",
        "days_into_jie": (target - jie_start).days,
        "chao_shen": ft < jie_start,
        "method": "chaibu",
        "rule": "qimen-chaibu-v2",
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


def find_shi_gan_palace(di_pan: dict[int, str], hour_gan: str, yi0: str) -> int:
    """時干落宮：甲用旬首儀，其餘找地盤天干所在宮。"""
    target = yi0 if hour_gan == "甲" else hour_gan
    for p, g in di_pan.items():
        if p != 5 and g == target:
            return p
    return 5


@dataclass
class QimenPan:
    yang: bool
    ju: int
    yuan: str
    pillars: dict[str, str]
    di_pan: dict[int, str]
    zhi_fu_palace: int
    zhi_fu_origin: int
    shi_gan_palace: int
    meta: dict


def cast_qimen(y: int, m: int, d: int, hour: int) -> QimenPan:
    day = _solar(y, m, d)
    pillars = {
        "year": gz_str(day.getYearGZ(False)),
        "month": gz_str(day.getMonthGZ()),
        "day": gz_str(day.getDayGZ()),
        "hour": gz_str(day.getHourGZ(hour)),
    }
    yang, ju, yuan, meta = yuan_and_ju_chaibu(y, m, d)
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
    sgp = find_shi_gan_palace(di, hg, yi0)
    return QimenPan(yang, ju, yuan, pillars, di, zf, origin, sgp, meta)


def _norm49(x: int) -> int:
    if x <= 0:
        x = abs(x) if x != 0 else 1
    return ((x - 1) % 49) + 1


def _tails_to_nums(tails: list[int]) -> list[int]:
    out: list[int] = []
    for n in range(1, 50):
        t = n % 10
        if t in tails or (t == 0 and 0 in tails) or (t == 0 and 10 in tails):
            out.append(n)
    return out


def extract_scores(pan: QimenPan, weight_scale: float = 1.0) -> dict[int, float]:
    """按奇門派彩券思路：時乾落宮字尾為主，公式擴池。"""
    scores: dict[int, float] = {i: 0.0 for i in range(1, 50)}
    sgp = pan.shi_gan_palace
    di = pan.di_pan
    hg = pan.pillars["hour"][0]

    # 1) 時乾落宮字尾 — 最高權
    for n in _tails_to_nums(PALACE_TAILS.get(sgp, [1, 6])):
        scores[n] += 4.0 * weight_scale

    # 2) 值符宮字尾
    for n in _tails_to_nums(PALACE_TAILS.get(pan.zhi_fu_palace, [])):
        scores[n] += 2.5 * weight_scale

    # 3) 公式：後天宮數、先天宮數、天干數、地盤干數
    ht = PALACE_HOUTIAN.get(sgp, 5)
    xt = PALACE_XIAN_TIAN.get(sgp, 5)
    gnums = GAN_NUMS.get(hg, [5])
    di_gan = di.get(sgp, "戊")
    di_nums = GAN_NUMS.get(di_gan, [5])

    formula_vals = [
        ht, xt,
        ht + xt,
        gnums[0],
        di_nums[0],
        ht + di_nums[0],
        xt + di_nums[0],
        ht + gnums[0],
        xt + gnums[0],
        pan.ju,
        pan.ju + ht,
        pan.zhi_fu_palace,
        pan.zhi_fu_origin,
    ]
    for v in formula_vals:
        scores[_norm49(v)] += 2.0 * weight_scale
        scores[_norm49(v + 10)] += 1.2 * weight_scale
        scores[_norm49(v + 20)] += 1.0 * weight_scale
        scores[_norm49(v + 30)] += 0.8 * weight_scale

    # 4) 地盤三奇六儀輔助（較低權）
    for palace, gan in di.items():
        if palace == 5:
            continue
        w = 1.5 if gan in SAN_QI else 0.8
        if palace == pan.zhi_fu_palace:
            w += 1.0
        for gn in GAN_NUMS.get(gan, []):
            scores[_norm49(gn)] += w * 0.5 * weight_scale
            scores[_norm49(gn + palace)] += w * 0.4 * weight_scale

    return scores


def pan_to_dict(p: QimenPan) -> dict[str, Any]:
    return {
        "yang_dun": p.yang,
        "ju": p.ju,
        "yuan": p.yuan,
        "pillars": p.pillars,
        "di_pan": {str(k): v for k, v in p.di_pan.items()},
        "zhi_fu_palace": p.zhi_fu_palace,
        "zhi_fu_origin": p.zhi_fu_origin,
        "shi_gan_palace": p.shi_gan_palace,
        "meta": p.meta,
    }

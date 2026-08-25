# -*- coding: utf-8 -*-
"""時家奇門：拆補起局 + 時乾落宮／範洪取數

rule: qimen-chaibu-v3
起局參考：https://www.qimenpai.com/blog/407
  - 冬至後陽遁、夏至後陰遁
  - 符頭甲／己；地支子午卯酉上元、寅申巳亥中元、辰戌丑未下元
  - 拆補：按「當日所在節氣」+ 符頭所屬元定局（不置閏）
  - 局數口訣見 YANG_JU / YIN_JU
取數參考：blog/719、28、31
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

# —— 陽遁九局起例（blog/407 口訣）——
# 冬至驚蟄一七四；小寒二八五；春分大寒三九六；立春八五二；
# 穀雨小滿五二八；雨水九六三；清明立夏四一七；芒種六三九
YANG_JU = {
    "冬至": (1, 7, 4),
    "小寒": (2, 8, 5),
    "大寒": (3, 9, 6),
    "立春": (8, 5, 2),
    "雨水": (9, 6, 3),
    "驚蟄": (1, 7, 4),
    "春分": (3, 9, 6),
    "清明": (4, 1, 7),
    "穀雨": (5, 2, 8),
    "立夏": (4, 1, 7),
    "小滿": (5, 2, 8),
    "芒種": (6, 3, 9),
}

# —— 陰遁九局起例（blog/407 口訣）——
# 夏至白露九三六；小暑八二五；大暑秋分七一四；立秋二五八；
# 霜降小雪五八二；大雪四七一；處暑一四七；立冬寒露六九三
YIN_JU = {
    "夏至": (9, 3, 6),
    "小暑": (8, 2, 5),
    "大暑": (7, 1, 4),
    "立秋": (2, 5, 8),
    "處暑": (1, 4, 7),
    "白露": (9, 3, 6),
    "秋分": (7, 1, 4),
    "寒露": (6, 9, 3),
    "霜降": (5, 8, 2),
    "立冬": (6, 9, 3),
    "小雪": (5, 8, 2),
    "大雪": (4, 7, 1),
}

# 符頭地支 → 元（0上 1中 2下）
FU_ZHI_YUAN = {
    "子": 0, "午": 0, "卯": 0, "酉": 0,
    "寅": 1, "申": 1, "巳": 1, "亥": 1,
    "辰": 2, "戌": 2, "丑": 2, "未": 2,
}

PALACE_HOUTIAN = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
PALACE_XIAN_TIAN = {1: 6, 2: 8, 3: 4, 4: 5, 5: 5, 6: 1, 7: 2, 8: 7, 9: 3}

PALACE_TAILS: dict[int, list[int]] = {
    1: [1, 6, 8],
    8: [4, 5, 0, 7, 8],
    3: [3, 8, 4],
    4: [3, 8, 4, 5, 2],
    9: [2, 7, 9, 3, 1],
    2: [5, 0, 2, 8],
    7: [4, 9, 2, 7, 6],
    6: [4, 9, 6, 7, 1],
    5: [5, 0],
}

FAN_HONG: dict[str, int] = {
    "甲": 9, "己": 9, "子": 9, "午": 9,
    "乙": 8, "庚": 8, "丑": 8, "未": 8,
    "丙": 7, "辛": 7, "寅": 7, "申": 7,
    "丁": 6, "壬": 6, "卯": 6, "酉": 6,
    "戊": 5, "癸": 5, "辰": 5, "戌": 5,
    "巳": 4, "亥": 4,
}

SHEN_NUM = {"值符": 1, "螣蛇": 2, "太陰": 8, "六合": 6, "白虎": 6, "玄武": 5, "九地": 9, "九天": 9}

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
    """當日最近已交節氣；陽遁=冬至後至夏至前，陰遁=夏至後至冬至前。"""
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
        if ji2 == 21:  # 冬至
            yang = True
            break
        if ji2 == 9:  # 夏至
            yang = False
            break
    return name, jd, yang


def fu_tou_date(y: int, m: int, d: int) -> date:
    """往前含當日最近甲／己日。"""
    for back in range(0, 15):
        dt = date(y, m, d) - timedelta(days=back)
        if _solar(dt.year, dt.month, dt.day).getDayGZ().tg in (0, 5):
            return dt
    return date(y, m, d)


def _resolve_ju_key(name: str, table: dict) -> str:
    """節氣名對局表；中氣併入口訣同組之節。"""
    if name in table:
        return name
    # 中氣名直接嘗試別名
    aliases = {"谷雨": "穀雨", "惊蛰": "驚蟄", "处暑": "處暑", "小满": "小滿"}
    if name in aliases and aliases[name] in table:
        return aliases[name]
    for k in table:
        if k[0] == name[0]:
            return k
    return list(table.keys())[0]


def yuan_and_ju_chaibu(y: int, m: int, d: int) -> tuple[bool, int, str, dict]:
    """拆補定局（blog/407）。

    步驟：
    1. 年月日時干支（外層 cast 處理）
    2. 定節氣 → 陽／陰遁
    3. 符頭（甲己日）地支 → 上中下元
    4. 查口訣表得局數（不置閏）
    """
    name, jie_start, yang = _find_current_jie(y, m, d)
    table = YANG_JU if yang else YIN_JU
    key = _resolve_ju_key(name, table)
    ft = fu_tou_date(y, m, d)
    ft_day = _solar(ft.year, ft.month, ft.day)
    ft_gz = gz_str(ft_day.getDayGZ())
    yi = FU_ZHI_YUAN.get(ft_gz[1], 0)
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
        "jie_qi": "正授" if ft == jie_start else ("超神" if ft < jie_start else "接氣"),
        "method": "chaibu",
        "rule": "qimen-chaibu-v3",
        "source": "qimenpai.com/blog/407",
    }
    return yang, ju, yuan, meta


def arrange_di_pan(yang: bool, ju: int) -> dict[int, str]:
    """地盤：陽順陰逆，局數宮起戊。"""
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


def _digit_expand(digit: int) -> list[int]:
    d = digit % 10
    if d == 0:
        d = 10
    return [n for k in range(5) if 1 <= (n := d + k * 10) <= 49]


def _tails_to_nums(tails: list[int]) -> list[int]:
    out: list[int] = []
    for n in range(1, 50):
        t = n % 10
        if t in tails or (t == 0 and 0 in tails):
            out.append(n)
    return out


def _add(scores: dict[int, float], nums: list[int], w: float) -> None:
    for n in nums:
        if 1 <= n <= 49:
            scores[n] += w


def extract_scores(pan: QimenPan, weight_scale: float = 1.0) -> dict[int, float]:
    scores: dict[int, float] = {i: 0.0 for i in range(1, 50)}
    sgp = pan.shi_gan_palace
    di = pan.di_pan
    pillars = pan.pillars
    hg, hz = pillars["hour"][0], pillars["hour"][1]
    dg, dz = pillars["day"][0], pillars["day"][1]

    _add(scores, _tails_to_nums(PALACE_TAILS.get(sgp, [1, 6])), 4.0 * weight_scale)
    _add(scores, _tails_to_nums(PALACE_TAILS.get(pan.zhi_fu_palace, [])), 2.5 * weight_scale)

    for char, w in ((hg, 3.5), (hz, 3.0), (dg, 2.5), (dz, 2.0)):
        fh = FAN_HONG.get(char)
        if fh is not None:
            _add(scores, _digit_expand(fh), w * weight_scale)

    for palace, gan in di.items():
        if palace == 5:
            continue
        fh = FAN_HONG.get(gan)
        if fh is None:
            continue
        w = 1.2
        if palace == sgp:
            w = 3.0
        elif palace == pan.zhi_fu_palace:
            w = 2.5
        elif gan in SAN_QI:
            w = 1.8
        _add(scores, _digit_expand(fh), w * weight_scale)
        _add(scores, [_norm49(PALACE_HOUTIAN[palace] + fh)], 1.5 * weight_scale)
        _add(scores, [_norm49(PALACE_XIAN_TIAN[palace] + fh)], 1.2 * weight_scale)

    ht = PALACE_HOUTIAN.get(sgp, 5)
    xt = PALACE_XIAN_TIAN.get(sgp, 5)
    for v, w in (
        (ht, 2.0), (xt, 1.8), (ht + xt, 1.5),
        (pan.ju, 1.5), (pan.ju + ht, 1.4),
        (pan.zhi_fu_palace, 1.3), (pan.zhi_fu_origin, 1.2),
        (SHEN_NUM["值符"], 1.0), (SHEN_NUM["九天"], 0.9), (SHEN_NUM["太陰"], 0.9),
    ):
        _add(scores, _digit_expand(v), w * weight_scale)
        _add(scores, [_norm49(v), _norm49(v + 10), _norm49(v + 20)], 0.8 * weight_scale)

    for key, w in (("year", 1.0), ("month", 1.2)):
        gz = pillars.get(key, "")
        if len(gz) >= 2:
            for ch in (gz[0], gz[1]):
                fh = FAN_HONG.get(ch)
                if fh is not None:
                    _add(scores, _digit_expand(fh), w * weight_scale)

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

# -*- coding: utf-8 -*-
"""天喜曆法層：四柱、節氣時刻、干支常數。

節氣用壽星天文曆（sxtwl）儒略日，精確到分。
年柱以立春換年；月柱以十二節換月。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

try:
    import sxtwl
except ImportError as e:
    raise ImportError("需要 sxtwl: pip install sxtwl") from e

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]

WX_G = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
WX_Z = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}
ZHI_BEN_GAN = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬",
}
CANG = {
    "子": [("癸", 1.0)],
    "丑": [("己", 1.0), ("癸", 0.5), ("辛", 0.5)],
    "寅": [("甲", 1.0), ("丙", 0.5), ("戊", 0.5)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 1.0), ("乙", 0.5), ("癸", 0.5)],
    "巳": [("丙", 1.0), ("戊", 0.5), ("庚", 0.5)],
    "午": [("丁", 1.0), ("己", 0.5)],
    "未": [("己", 1.0), ("丁", 0.5), ("乙", 0.5)],
    "申": [("庚", 1.0), ("壬", 0.5), ("戊", 0.5)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 1.0), ("辛", 0.5), ("丁", 0.5)],
    "亥": [("壬", 1.0), ("甲", 0.5)],
}
LU = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}
YANG_GAN = set("甲丙戊庚壬")
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

JQ_NAMES = [
    "冬至", "小寒", "大寒", "立春", "雨水", "驚蟾", "春分", "清明",
    "穀雨", "立夏", "小滿", "芒種", "夏至", "小暑", "大暑", "立秋",
    "處暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
]
JIE_INDEX = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23}
JIE_NAMES = {JQ_NAMES[i] for i in JIE_INDEX}


def gz_str(gz: Any) -> str:
    return GAN[gz.tg] + ZHI[gz.dz]


def next_gz(ganzhi: str, step: int) -> str:
    if not ganzhi or len(ganzhi) < 2:
        return ""
    gi = (GAN.index(ganzhi[0]) + step) % 10
    zi = (ZHI.index(ganzhi[1]) + step) % 12
    return GAN[gi] + ZHI[zi]


def year_gz_lichun(year: int) -> str:
    """公曆年立春後之年柱。1984 = 甲子。"""
    return JIAZI[(year - 1984) % 60]


def parse_sex(sex: str) -> str:
    s = (sex or "").strip().lower()
    if s in ("m", "male", "男", "1", "man"):
        return "male"
    if s in ("f", "female", "女", "0", "woman"):
        return "female"
    raise ValueError("性別須為 male/female 或 男/女")


def parse_dt(text: str, default_hour: int = 12) -> datetime:
    t = text.strip().replace("/", "-").replace(" ", "T")
    if "T" in t:
        date_part, time_part = t.split("T", 1)
        bits = time_part.replace("Z", "").split(":")
        hh = int(bits[0] or 0)
        mm = int(bits[1]) if len(bits) > 1 else 0
        ss = int(float(bits[2])) if len(bits) > 2 else 0
    else:
        date_part, hh, mm, ss = t, default_hour, 0, 0
    y, m, d = [int(x) for x in date_part.split("-")[:3]]
    return datetime(y, m, d, hh, mm, ss)


def jd_to_dt(jd: float) -> datetime:
    t = sxtwl.JD2DD(jd)
    sec = int(round(t.s))
    minute = int(t.m)
    hour = int(t.h)
    extra, sec = divmod(sec, 60)
    minute += extra
    extra, minute = divmod(minute, 60)
    hour += extra
    base = datetime(int(t.Y), int(t.M), int(t.D), 0, 0, 0)
    return base + timedelta(hours=hour, minutes=minute, seconds=sec)


def solar_to_jd(dt: datetime) -> float:
    t = sxtwl.Time()
    t.Y, t.M, t.D = dt.year, dt.month, dt.day
    t.h, t.m, t.s = dt.hour, dt.minute, float(dt.second)
    return float(sxtwl.toJD(t))


def pillars_at(dt: datetime) -> dict[str, str]:
    day = sxtwl.fromSolar(dt.year, dt.month, dt.day)
    return {
        "year": gz_str(day.getYearGZ(False)),
        "month": gz_str(day.getMonthGZ()),
        "day": gz_str(day.getDayGZ()),
        "hour": gz_str(day.getHourGZ(dt.hour)),
    }


def _jie_event(day_obj: Any) -> tuple[datetime, str, int] | None:
    if not day_obj.hasJieQi():
        return None
    idx = int(day_obj.getJieQi()) % 24
    if idx not in JIE_INDEX:
        return None
    return jd_to_dt(day_obj.getJieQiJD()), JQ_NAMES[idx], idx


def find_jie(birth: datetime, forward: bool) -> tuple[datetime, str]:
    """順行取出生後下一個節；逆行取出生前上一個節。時刻用節氣交節 JD。"""
    origin = sxtwl.fromSolar(birth.year, birth.month, birth.day)
    if forward:
        cur = origin
        for _ in range(80):
            cur = cur.after(1)
            ev = _jie_event(cur)
            if ev and ev[0] > birth:
                return ev[0], ev[1]
        raise RuntimeError("找不到出生後之節")
    ev0 = _jie_event(origin)
    if ev0 and ev0[0] < birth:
        return ev0[0], ev0[1]
    cur = origin
    for _ in range(80):
        cur = cur.before(1)
        ev = _jie_event(cur)
        if ev and ev[0] < birth:
            return ev[0], ev[1]
    raise RuntimeError("找不到出生前之節")


def add_ymdh(dt: datetime, years: int, months: int, days: int, hours: int) -> datetime:
    y = dt.year + years
    m = dt.month + months
    while m > 12:
        y += 1
        m -= 12
    while m < 1:
        y -= 1
        m += 12
    from calendar import monthrange

    d = min(dt.day, monthrange(y, m)[1])
    out = datetime(y, m, d, dt.hour, dt.minute, dt.second)
    return out + timedelta(days=days, hours=hours)


def shi_shen_of(dm_gan: str, other_gan: str) -> str:
    if other_gan == dm_gan:
        return "比肩"
    dm_wx, ot_wx = WX_G[dm_gan], WX_G[other_gan]
    same = (dm_gan in YANG_GAN) == (other_gan in YANG_GAN)
    if ot_wx == dm_wx:
        return "比肩" if same else "劫財"
    if SHENG[dm_wx] == ot_wx:
        return "食神" if same else "傷官"
    if KE[dm_wx] == ot_wx:
        return "偏財" if same else "正財"
    if KE[ot_wx] == dm_wx:
        return "七殺" if same else "正官"
    if SHENG[ot_wx] == dm_wx:
        return "偏印" if same else "正印"
    return "?"


def has_root(dm_gan: str, zhi: str) -> bool:
    dm = WX_G[dm_gan]
    if zhi == LU.get(dm_gan):
        return True
    if WX_Z[zhi] == dm:
        return True
    for cg, w in CANG.get(zhi, []):
        if WX_G[cg] == dm and w >= 1.0:
            return True
    return False

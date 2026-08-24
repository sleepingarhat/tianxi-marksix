# -*- coding: utf-8 -*-
"""喜用引擎 C：滴天髓眾寡論優先 (yongshen-ditian-zhonggua-v1)

依賴: sxtwl
用法:
  from yongshen_c import yongshen_c
  r = yongshen_c(2026, 8, 22)  # 21:30 HKT 時柱
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any

try:
    import sxtwl
except ImportError as e:
    raise ImportError("需要 sxtwl: pip install sxtwl") from e

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
WX_G = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
WX_Z = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
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
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
CHONG = {
    ("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
}
CHONG |= {(b, a) for a, b in list(CHONG)}
LIUHE = {
    ("子", "丑"): "土", ("寅", "亥"): "木", ("卯", "戌"): "火",
    ("辰", "酉"): "金", ("巳", "申"): "水", ("午", "未"): "土",
}
LIUHE.update({(b, a): v for (a, b), v in list(LIUHE.items())})
LU = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}


def gz_str(gz) -> str:
    return GAN[gz.tg] + ZHI[gz.dz]


def tongguan(w1: str, w2: str) -> str | None:
    if KE.get(w1) == w2:
        return SHENG[w1]
    if KE.get(w2) == w1:
        return SHENG[w2]
    return None


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


def _uniq(xs: list[str]) -> list[str]:
    out: list[str] = []
    for x in xs:
        if x and x not in out:
            out.append(x)
    return out


def yongshen_c(year: int, month: int, day: int, hour: int = 21) -> dict[str, Any]:
    """以公曆日 + 時辰（預設 21=亥時）起盤，返回眾寡喜用結果。"""
    d = sxtwl.fromSolar(year, month, day)
    Y = gz_str(d.getYearGZ(False))
    M = gz_str(d.getMonthGZ())
    D = gz_str(d.getDayGZ())
    H = gz_str(d.getHourGZ(hour))
    dm_gan = D[0]
    dm = WX_G[dm_gan]
    zhis = [Y[1], M[1], D[1], H[1]]
    gans = [Y[0], M[0], D[0], H[0]]

    coef = [1.0, 1.0, 1.0, 1.0]
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zhis[i], zhis[j]
            if (a, b) in CHONG:
                coef[i] *= 0.5
                coef[j] *= 0.5
            if (a, b) in LIUHE:
                hu = LIUHE[(a, b)]
                if WX_Z[M[1]] == hu or WX_G[M[0]] == hu:
                    coef[i] *= 0.3
                    coef[j] *= 0.3
                else:
                    coef[i] *= 0.7
                    coef[j] *= 0.7

    score: dict[str, float] = defaultdict(float)
    for g in gans:
        score[WX_G[g]] += 1.0
    for i, z in enumerate(zhis):
        w = 2.0 if i == 1 else 1.0
        score[WX_Z[z]] += w * coef[i]
        for cg, cw in CANG.get(z, []):
            score[WX_G[cg]] += cw * 0.5 * coef[i]
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zhis[i], zhis[j]
            if (a, b) in LIUHE:
                hu = LIUHE[(a, b)]
                if WX_Z[M[1]] == hu or WX_G[M[0]] == hu:
                    score[hu] += 2.0

    yin = [k for k, v in SHENG.items() if v == dm][0]
    shi, cai = SHENG[dm], KE[dm]
    guan = [k for k, v in KE.items() if v == dm][0]
    party_self = score[dm] + score[yin]
    party_other = score[shi] + score[cai] + score[guan]
    ratio = (party_self + 1e-6) / (party_other + 1e-6)
    rooted = any(has_root(dm_gan, z) for z in zhis)

    yue = M[1]
    tiaohou = "火" if yue in "亥子丑" else ("水" if yue in "巳午未" else None)
    tiaohou_urgent = (tiaohou == "火" and score["火"] <= 0.3) or (
        tiaohou == "水" and score["水"] <= 0.3
    )

    ranked = sorted(score.items(), key=lambda x: -x[1])
    maj_wx, maj_sc = ranked[0]
    sec_wx, sec_sc = ranked[1]

    pattern = ""
    yong: list[str] = []
    xi: list[str] = []
    ji: list[str] = []
    note: list[str] = []

    if (not rooted) and ratio < 0.5:
        pattern = "從勢"
        other = [(shi, score[shi]), (cai, score[cai]), (guan, score[guan])]
        other.sort(key=lambda x: -x[1])
        yong = [other[0][0]]
        if other[1][1] > 0.5:
            xi.append(other[1][0])
        ji = [dm, yin]
        note.append(f"無根 ratio={ratio:.2f}")
    elif (not rooted) and ratio > 2.0 and score[dm] >= maj_sc * 0.8:
        pattern = "從強"
        yong = [dm, yin]
        ji = [cai, guan]
    elif (KE.get(maj_wx) == sec_wx or KE.get(sec_wx) == maj_wx) and sec_sc >= maj_sc * 0.55:
        tg = tongguan(maj_wx, sec_wx)
        pattern = "交戰通關"
        yong = [tg] if tg else [maj_wx]
        xi = [maj_wx, sec_wx]
        note.append(f"{maj_wx}↔{sec_wx}")
    else:
        yue_ben = WX_Z[M[1]]
        if yue_ben == dm:
            ss = "比劫"
        elif yue_ben == yin:
            ss = "印"
        elif yue_ben == shi:
            ss = "食傷"
        elif yue_ben == cai:
            ss = "財"
        elif yue_ben == guan:
            ss = "官殺"
        else:
            ss = "?"
        tou = yue_ben in [WX_G[g] for g in gans]
        if tou and ss in ("官殺", "財", "食傷", "印"):
            pattern = f"正格({ss})"
            if ss == "官殺":
                yong, ji = [cai, yin], [shi]
            elif ss == "財":
                yong = [shi] if ratio >= 1 else [yin, dm]
            elif ss == "食傷":
                yong, ji = [cai], [yin]
            elif ss == "印":
                yong = [guan] if score[guan] > 0.5 else [dm]
                ji = [cai]
        else:
            pattern = "眾寡扶抑"
            if ratio >= 1.2:
                yong, ji = [shi, cai], [yin]
            else:
                yong, ji = [yin, dm], [guan]

    if tiaohou:
        if tiaohou_urgent and pattern.startswith("從"):
            if tiaohou not in ji:
                xi.append(tiaohou)
        elif tiaohou_urgent:
            if tiaohou not in yong:
                yong.insert(0, tiaohou)
            note.append("調候升主")
        elif tiaohou not in yong and tiaohou not in xi:
            xi.append(tiaohou)

    yong, xi, ji = _uniq(yong), _uniq(xi), _uniq(ji)
    xi = [x for x in xi if x not in yong]
    ji = [x for x in ji if x not in yong and x not in xi]

    return {
        "ruleId": "yongshen-ditian-zhonggua-v1",
        "pillars": {"year": Y, "month": M, "day": D, "hour": H},
        "day_master": dm,
        "score": {k: round(v, 3) for k, v in score.items()},
        "party_self": round(party_self, 3),
        "party_other": round(party_other, 3),
        "ratio": round(ratio, 3),
        "rooted": rooted,
        "pattern": pattern,
        "yong_shen": yong,
        "xi_shen": xi,
        "ji_shen": ji,
        "tiaohou": tiaohou,
        "tiaohou_urgent": tiaohou_urgent,
        "note": note,
    }


if __name__ == "__main__":
    import pprint

    pprint.pp(yongshen_c(2026, 8, 22))

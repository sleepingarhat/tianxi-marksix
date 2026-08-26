# -*- coding: utf-8 -*-
"""四柱八字生克制化 tianxi-zhihua-v1

計齊年／月／日／時天干地支：沖合會刑、干合、十神制化、得令得地得生得助。
身強弱唔可以只睇日主有無根。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from tianxi_calendar import CANG, KE, SHENG, WX_G, WX_Z, ZHI_BEN_GAN, has_root, shi_shen_of

CHONG = {
    ("子", "午"), ("午", "子"), ("丑", "未"), ("未", "丑"),
    ("寅", "申"), ("申", "寅"), ("卯", "酉"), ("酉", "卯"),
    ("辰", "戌"), ("戌", "辰"), ("巳", "亥"), ("亥", "巳"),
}
LIUHE = {
    ("子", "丑"): "土", ("丑", "子"): "土",
    ("寅", "亥"): "木", ("亥", "寅"): "木",
    ("卯", "戌"): "火", ("戌", "卯"): "火",
    ("辰", "酉"): "金", ("酉", "辰"): "金",
    ("巳", "申"): "水", ("申", "巳"): "水",
    ("午", "未"): "土", ("未", "午"): "土",
}
GAN_HE = {
    ("甲", "己"): "土", ("己", "甲"): "土",
    ("乙", "庚"): "金", ("庚", "乙"): "金",
    ("丙", "辛"): "水", ("辛", "丙"): "水",
    ("丁", "壬"): "木", ("壬", "丁"): "木",
    ("戊", "癸"): "火", ("癸", "戊"): "火",
}
SANHE = [(set("申子辰"), "水"), (set("亥卯未"), "木"), (set("寅午戌"), "火"), (set("巳酉丑"), "金")]
SANHUI = [(set("寅卯辰"), "木"), (set("巳午未"), "火"), (set("申酉戌"), "金"), (set("亥子丑"), "水")]
XING = {
    ("寅", "巳"), ("巳", "申"), ("申", "寅"),
    ("丑", "戌"), ("戌", "未"), ("未", "丑"),
    ("子", "卯"), ("卯", "子"),
}
KEYS = ("year", "month", "day", "hour")
POS = {"year": "年", "month": "月", "day": "日", "hour": "時"}


def roles_of(dm_wx: str) -> dict[str, str]:
    yin = [k for k, v in SHENG.items() if v == dm_wx][0]
    guan = [k for k, v in KE.items() if v == dm_wx][0]
    return {"比劫": dm_wx, "印": yin, "食傷": SHENG[dm_wx], "財": KE[dm_wx], "官殺": guan}


def _uniq(xs: list[str]) -> list[str]:
    out: list[str] = []
    for x in xs:
        if x and x not in out:
            out.append(x)
    return out


def interact_bazi(pillars: dict[str, str]) -> dict[str, Any]:
    gans = [pillars[k][0] for k in KEYS]
    zhis = [pillars[k][1] for k in KEYS]
    dm_gan = pillars["day"][0]
    dm_wx = WX_G[dm_gan]
    roles = roles_of(dm_wx)
    rel: list[str] = []
    tags: list[str] = []
    coef = [1.0, 2.0, 1.0, 1.0]

    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zhis[i], zhis[j]
            lab = POS[KEYS[i]] + POS[KEYS[j]]
            if (a, b) in CHONG:
                coef[i] *= 0.5
                coef[j] *= 0.5
                rel.append(f"{lab}{a}{b}相沖")
            if (a, b) in XING:
                coef[i] *= 0.85
                coef[j] *= 0.85
                rel.append(f"{lab}{a}{b}相刑")
            if (a, b) in LIUHE:
                hu = LIUHE[(a, b)]
                if WX_Z[zhis[1]] == hu or WX_G[gans[1]] == hu:
                    coef[i] *= 0.35
                    coef[j] *= 0.35
                    rel.append(f"{lab}{a}{b}合化{hu}")
                else:
                    coef[i] *= 0.75
                    coef[j] *= 0.75
                    rel.append(f"{lab}{a}{b}六合（未化）")

    zset = set(zhis)
    for grp, hu in SANHUI:
        hit = grp & zset
        if len(hit) == 3:
            rel.append(f"{''.join(hit)}三會{hu}")
            tags.append(f"三會{hu}")
        elif len(hit) == 2:
            rel.append(f"{''.join(hit)}半會{hu}")
    for grp, hu in SANHE:
        hit = grp & zset
        if len(hit) == 3:
            rel.append(f"{''.join(hit)}三合{hu}")
            tags.append(f"三合{hu}")
        elif len(hit) == 2:
            rel.append(f"{''.join(hit)}半合{hu}")

    for i in range(4):
        for j in range(i + 1, 4):
            if (gans[i], gans[j]) in GAN_HE:
                rel.append(f"{POS[KEYS[i]]}{POS[KEYS[j]]}{gans[i]}{gans[j]}合{GAN_HE[(gans[i], gans[j])]}")

    gan_ss = ["日主" if k == "day" else shi_shen_of(dm_gan, gans[i]) for i, k in enumerate(KEYS)]
    zhi_ss = [shi_shen_of(dm_gan, ZHI_BEN_GAN[z]) for z in zhis]
    all_ss = [s for s in gan_ss + zhi_ss if s and s != "日主"]

    def has_ss(*names: str) -> bool:
        return any(s in names for s in all_ss)

    tou_ss = [s for i, s in enumerate(gan_ss) if KEYS[i] != "day"]
    if has_ss("食神") and has_ss("七殺"):
        tags.append("食神制殺"); rel.append("食神制殺")
    if has_ss("傷官") and has_ss("正官", "七殺"):
        tags.append("傷官見官"); rel.append("傷官見官")
        if has_ss("正印", "偏印"):
            tags.append("印化官殺"); rel.append("印通關，化官殺之剋")
        else:
            rel.append("傷官見官無印通關")
    if has_ss("傷官", "食神") and has_ss("正財", "偏財"):
        tags.append("食傷生財"); rel.append("食傷生財")
    if has_ss("正財", "偏財") and has_ss("正官", "七殺"):
        tags.append("財生官殺"); rel.append("財生官殺")
    if has_ss("正印", "偏印") and has_ss("正官", "七殺"):
        tags.append("官印相生"); rel.append("官殺生印")
    if has_ss("正財", "偏財") and has_ss("正印", "偏印"):
        tags.append("財壞印"); rel.append("財星壞印")
    if has_ss("比肩", "劫財") and has_ss("正財", "偏財"):
        tags.append("比劫爭財"); rel.append("比劫爭財")
    if has_ss("正印", "偏印") and has_ss("食神", "傷官"):
        tags.append("印制食傷"); rel.append("印制食傷")

    for i, k in enumerate(KEYS):
        if k == "day":
            continue
        w = WX_G[gans[i]]
        lab = POS[k] + gans[i]
        if SHENG[w] == dm_wx:
            rel.append(lab + "生身")
        elif w == dm_wx:
            rel.append(lab + "助身")
        elif KE[w] == dm_wx:
            rel.append(lab + "剋身")
        elif SHENG[dm_wx] == w:
            rel.append(lab + "洩身")
        elif KE[dm_wx] == w:
            rel.append(lab + "耗身")

    score: dict[str, float] = defaultdict(float)
    for g in gans:
        score[WX_G[g]] += 1.0
    for i, z in enumerate(zhis):
        score[WX_Z[z]] += coef[i]
        for cg, cw in CANG.get(z, []):
            score[WX_G[cg]] += cw * 0.5 * coef[i]
    for item in rel:
        if "合化" in item and item[-1] in "木火土金水":
            score[item[-1]] += 1.2

    help_sc = score[roles["比劫"]] + score[roles["印"]]
    hurt_sc = score[roles["食傷"]] + score[roles["財"]] + score[roles["官殺"]]
    if "食神制殺" in tags or "印化官殺" in tags:
        hurt_sc *= 0.82
        help_sc *= 1.05
    if "傷官見官" in tags and "印化官殺" not in tags:
        hurt_sc *= 1.12
    if "財壞印" in tags:
        help_sc *= 0.88

    de_ling = zhi_ss[1] in ("比肩", "劫財", "正印", "偏印")
    de_di = any(has_root(dm_gan, z) for z in zhis)
    de_sheng = any(shi_shen_of(dm_gan, g) in ("正印", "偏印") for g in gans if g != dm_gan) or any(
        shi_shen_of(dm_gan, ZHI_BEN_GAN[z]) in ("正印", "偏印") for z in zhis
    )
    de_zhu = any(shi_shen_of(dm_gan, g) in ("比肩", "劫財") for g in gans if g != dm_gan)
    strength = help_sc - hurt_sc
    if strength >= 0.6 and (de_ling or de_di or help_sc >= hurt_sc):
        body = "旺"
    elif strength <= -0.4 or (not de_di and help_sc < hurt_sc * 0.85):
        body = "弱"
    else:
        body = "中和"

    return {
        "relations": _uniq(rel),
        "tags": _uniq(tags),
        "score": {k: round(float(score.get(k, 0.0)), 3) for k in ("木", "火", "土", "金", "水")},
        "help": round(help_sc, 3),
        "hurt": round(hurt_sc, 3),
        "strength": round(strength, 3),
        "body": body,
        "de_ling": de_ling,
        "de_di": de_di,
        "de_sheng": de_sheng,
        "de_zhu": de_zhu,
        "yin_tou": any(s in ("正印", "偏印") for s in tou_ss),
        "cai_tou": any(s in ("正財", "偏財") for s in tou_ss),
        "guan_tou": any(s in ("正官", "七殺") for s in tou_ss),
        "shi_tou": any(s in ("食神", "傷官") for s in tou_ss),
        "yin_root": any(WX_Z[z] == roles["印"] for z in zhis) or any(WX_G[ZHI_BEN_GAN[z]] == roles["印"] for z in zhis),
        "cai_root": any(WX_Z[z] == roles["財"] for z in zhis),
        "roles": roles,
        "gan_ss": {KEYS[i]: gan_ss[i] for i in range(4)},
        "zhi_ss": {KEYS[i]: zhi_ss[i] for i in range(4)},
        "coef": [round(c, 3) for c in coef],
    }

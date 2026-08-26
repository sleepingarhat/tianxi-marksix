# -*- coding: utf-8 -*-
"""天喜格局喜用引擎 tianxi-geju-xiyong-v1

定格序：真從／專旺 → 月令正格（雜氣透干）→ 成敗救應 → 調候次喜。
用／喜／忌以五行輸出；本檔不取號。
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tianxi_calendar import (  # noqa: E402
    CANG,
    KE,
    SHENG,
    WX_G,
    WX_Z,
    ZHI_BEN_GAN,
    has_root,
    parse_dt,
    pillars_at,
    shi_shen_of,
)

ENGINE_ID = "tianxi-geju-xiyong-v1"

YUE_GE = {
    "比肩": "建禄格", "劫財": "羊刃格", "食神": "食神格", "傷官": "傷官格",
    "偏財": "偏財格", "正財": "正財格", "七殺": "七殺格", "正官": "正官格",
    "偏印": "偏印格", "正印": "正印格",
}
TABLE: dict[str, dict[str, list[str]]] = {
    "正官格": {"yong": ["官殺"], "xi": ["財", "印"], "ji": ["食傷"], "chou": ["比劫"]},
    "七殺格": {"yong": ["官殺"], "xi": ["食傷", "印"], "ji": ["財"], "chou": []},
    "正財格": {"yong": ["財"], "xi": ["食傷", "官殺"], "ji": ["比劫"], "chou": []},
    "偏財格": {"yong": ["財"], "xi": ["食傷", "官殺"], "ji": ["比劫"], "chou": []},
    "正印格": {"yong": ["印"], "xi": ["官殺", "比劫"], "ji": ["財"], "chou": ["食傷"]},
    "偏印格": {"yong": ["印"], "xi": ["官殺", "比劫"], "ji": ["財"], "chou": ["食傷"]},
    "食神格": {"yong": ["食傷"], "xi": ["財", "比劫"], "ji": ["印"], "chou": ["官殺"]},
    "傷官格": {"yong": ["食傷"], "xi": ["印", "財"], "ji": ["官殺"], "chou": []},
    "羊刃格": {"yong": ["官殺"], "xi": ["財", "印"], "ji": ["食傷"], "chou": []},
    "建禄格": {"yong": ["官殺", "財"], "xi": ["食傷", "印"], "ji": ["比劫"], "chou": []},
    "從財格": {"yong": ["財"], "xi": ["食傷", "官殺"], "ji": ["比劫", "印"], "chou": []},
    "從殺格": {"yong": ["官殺"], "xi": ["財"], "ji": ["食傷", "印", "比劫"], "chou": []},
    "從兒格": {"yong": ["食傷"], "xi": ["財"], "ji": ["印", "比劫"], "chou": []},
    "從勢格": {"yong": ["食傷", "財", "官殺"], "xi": [], "ji": ["印", "比劫"], "chou": []},
    "專旺格": {"yong": ["比劫", "印"], "xi": ["食傷"], "ji": ["財", "官殺"], "chou": []},
    "扶抑身旺": {"yong": ["食傷", "財"], "xi": ["官殺"], "ji": ["印"], "chou": []},
    "扶抑身弱": {"yong": ["印", "比劫"], "xi": [], "ji": ["官殺"], "chou": ["財"]},
}
ZAQI = set("辰戌丑未")
ZAQI_CANG_ORDER = {
    "辰": ["戊", "乙", "癸"],
    "戌": ["戊", "辛", "丁"],
    "丑": ["己", "癸", "辛"],
    "未": ["己", "丁", "乙"],
}


def _roles(dm_wx: str) -> dict[str, str]:
    yin = [k for k, v in SHENG.items() if v == dm_wx][0]
    return {
        "比劫": dm_wx,
        "印": yin,
        "食傷": SHENG[dm_wx],
        "財": KE[dm_wx],
        "官殺": [k for k, v in KE.items() if v == dm_wx][0],
    }


def _expand(roles: dict[str, str], keys: list[str]) -> list[str]:
    out: list[str] = []
    for k in keys:
        wx = roles.get(k, k)
        if wx and wx not in out:
            out.append(wx)
    return out


def _uniq(xs: list[str]) -> list[str]:
    out: list[str] = []
    for x in xs:
        if x and x not in out:
            out.append(x)
    return out


def score_wuxing(pillars: dict[str, str]) -> dict[str, Any]:
    zhis = [pillars["year"][1], pillars["month"][1], pillars["day"][1], pillars["hour"][1]]
    gans = [pillars["year"][0], pillars["month"][0], pillars["day"][0], pillars["hour"][0]]
    score: dict[str, float] = defaultdict(float)
    for g in gans:
        score[WX_G[g]] += 1.0
    for i, z in enumerate(zhis):
        w = 2.0 if i == 1 else 1.0
        score[WX_Z[z]] += w
        for cg, cw in CANG.get(z, []):
            score[WX_G[cg]] += cw * 0.5
    dm = WX_G[pillars["day"][0]]
    roles = _roles(dm)
    party_self = score[roles["比劫"]] + score[roles["印"]]
    party_other = score[roles["食傷"]] + score[roles["財"]] + score[roles["官殺"]]
    ratio = (party_self + 1e-6) / (party_other + 1e-6)
    dm_gan = pillars["day"][0]
    rooted = any(has_root(dm_gan, z) for z in zhis)
    weak = False
    for z in zhis:
        if has_root(dm_gan, z):
            weak = True
            break
        for cg, w in CANG.get(z, []):
            if WX_G[cg] == WX_G[dm_gan] and w >= 0.5:
                weak = True
                break
    return {
        "score": {k: round(float(score.get(k, 0.0)), 3) for k in ("木", "火", "土", "金", "水")},
        "party_self": round(party_self, 3),
        "party_other": round(party_other, 3),
        "ratio": round(ratio, 3),
        "rooted": rooted,
        "rooted_weak": weak,
        "roles": roles,
    }


def month_pattern(dm_gan: str, pillars: dict[str, str]) -> tuple[str, str, list[str]]:
    yue_zhi = pillars["month"][1]
    notes: list[str] = []
    gans = [pillars["year"][0], pillars["month"][0], pillars["hour"][0]]
    if yue_zhi in ZAQI:
        hidden = ZAQI_CANG_ORDER[yue_zhi]
        tou = [g for g in hidden if g in gans]
        if tou:
            pri = {"正官": 0, "七殺": 0, "正財": 1, "偏財": 1, "正印": 2, "偏印": 2, "食神": 3, "傷官": 3}
            tou_ss = [(g, shi_shen_of(dm_gan, g)) for g in tou]
            tou_ss.sort(key=lambda x: pri.get(x[1], 9))
            ss = tou_ss[0][1]
            notes.append(f"雜氣透{tou_ss[0][0]}取{ss}")
        else:
            ss = shi_shen_of(dm_gan, ZHI_BEN_GAN[yue_zhi])
            notes.append("雜氣不透取本氣")
    else:
        ss = shi_shen_of(dm_gan, ZHI_BEN_GAN[yue_zhi])
    ge = YUE_GE.get(ss, f"正格({ss})")
    return ge, ss, notes


def detect_cong(score: dict[str, Any]) -> str | None:
    if score.get("rooted_weak") or score["rooted"]:
        return None
    if score["ratio"] < 0.5:
        roles = score["roles"]
        sc = score["score"]
        other = [("從兒格", sc[roles["食傷"]]), ("從財格", sc[roles["財"]]), ("從殺格", sc[roles["官殺"]])]
        other.sort(key=lambda x: -x[1])
        if other[0][1] >= (other[1][1] + other[2][1]) * 0.8 and other[0][1] > 0:
            return other[0][0]
        return "從勢格"
    if score["ratio"] > 2.0:
        return "專旺格"
    return None


def tiaohou_need(yue_zhi: str) -> str | None:
    if yue_zhi in "亥子丑":
        return "火"
    if yue_zhi in "巳午未":
        return "水"
    return None


def analyze_geju(pillars: dict[str, str]) -> dict[str, Any]:
    dm_gan = pillars["day"][0]
    dm_wx = WX_G[dm_gan]
    zhong = score_wuxing(pillars)
    roles = zhong["roles"]
    notes: list[str] = []
    status = "成"
    cong = detect_cong(zhong)
    yue_ge, yue_ss, yue_notes = month_pattern(dm_gan, pillars)
    notes.extend(yue_notes)
    if cong:
        primary = cong
        notes.append(f"無根 ratio={zhong['ratio']:.2f} → {cong}")
    else:
        primary = yue_ge
    key = primary if primary in TABLE else "扶抑身弱"
    if primary in ("建禄格", "羊刃格") and zhong["ratio"] < 1.0:
        key = "扶抑身弱"
        notes.append("禄刃而身弱，改扶抑")
    if primary.startswith("正格"):
        key = "扶抑身旺" if zhong["ratio"] >= 1.0 else "扶抑身弱"
    if key not in TABLE:
        key = "扶抑身旺" if zhong["ratio"] >= 1.2 else "扶抑身弱"
        primary = key
        status = "不成改扶抑"
    pack = TABLE[key]
    yong = _expand(roles, pack["yong"])
    xi = _expand(roles, pack["xi"])
    ji = _expand(roles, pack["ji"])
    chou = _expand(roles, pack["chou"])
    th = tiaohou_need(pillars["month"][1])
    th_urgent = False
    if th:
        th_urgent = zhong["score"].get(th, 0) <= 0.3
        if cong:
            if th not in ji and th not in yong:
                xi.append(th)
                notes.append("調候入次喜，不逆從")
        elif th_urgent:
            if th not in yong:
                yong.insert(0, th)
            notes.append("調候升主")
        elif th not in yong and th not in xi:
            xi.append(th)
    yong, xi, ji, chou = _uniq(yong), _uniq(xi), _uniq(ji), _uniq(chou)
    xi = [x for x in xi if x not in yong]
    ji = [x for x in ji if x not in yong and x not in xi]
    chou = [x for x in chou if x not in yong and x not in xi and x not in ji]
    shi = {}
    for k in ("year", "month", "day", "hour"):
        gan, zhi = pillars[k][0], pillars[k][1]
        shi[k] = {
            "gan": "日主" if k == "day" else shi_shen_of(dm_gan, gan),
            "zhi_ben": shi_shen_of(dm_gan, ZHI_BEN_GAN[zhi]),
        }
    return {
        "engineId": ENGINE_ID,
        "pillars": pillars,
        "day_master": {"gan": dm_gan, "wx": dm_wx},
        "shi_shen": shi,
        "zhong_gua": {
            "score": zhong["score"],
            "party_self": zhong["party_self"],
            "party_other": zhong["party_other"],
            "ratio": zhong["ratio"],
            "rooted": zhong["rooted"],
            "rooted_weak": zhong["rooted_weak"],
        },
        "pattern": {
            "primary": primary,
            "yue_ling": yue_ss,
            "yue_ge": yue_ge,
            "table_key": key,
            "status": status,
            "confidence": "rule",
        },
        "yong_shen": yong,
        "xi_shen": xi,
        "ji_shen": ji,
        "chou_shen": chou,
        "tiaohou": {"need": th, "urgent": th_urgent},
        "note": notes,
    }


def analyze_at(dt: datetime) -> dict[str, Any]:
    return analyze_geju(pillars_at(dt))


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python src/tianxi_geju.py 1988-02-08T04:00")
        sys.exit(1)
    raw = analyze_at(parse_dt(sys.argv[1], 4))
    print(json.dumps(raw, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

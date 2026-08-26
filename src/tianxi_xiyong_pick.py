# -*- coding: utf-8 -*-
"""天喜喜用取號 tianxi-xiyong-pick-v1

本命格局喜用 × 當運 × 流年 × 攪珠日四柱 → 15 碼。
層 A 沿用 personal-x-draw-v1 骨架。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from personal_x_draw_bazi import (  # noqa: E402
    DRAW_W,
    PERSONAL_W,
    map_gz_to_scores,
    map_wx_to_scores,
    pillars_at,
    score_chart,
)
from pick15 import pick15  # noqa: E402
from tianxi_calendar import WX_G, WX_Z, parse_dt, parse_sex  # noqa: E402
from tianxi_dayun import build_dayun  # noqa: E402
from tianxi_geju import analyze_geju  # noqa: E402

RULE = "tianxi-xiyong-pick-v1"

B_W = {"用": 2.5, "喜": 1.2, "忌": -1.2, "仇": -2.0}
TIAOHOU_EXTRA = 0.8
C_W = {
    "用": (2.0, 1.2),
    "喜": (1.0, 0.6),
    "忌": (-1.0, -0.6),
    "仇": (-1.8, -1.0),
}
D_W = {
    "用": (1.4, 0.8),
    "喜": (0.7, 0.4),
    "忌": (-0.7, -0.4),
    "仇": (-1.2, -0.7),
}
E_W = {
    "hour": {"用": (1.6, 1.0), "喜": (0.8, 0.5), "忌": (-0.8, -0.5), "仇": (-1.4, -0.9)},
    "day": {"用": (1.2, 0.8), "喜": (0.6, 0.4), "忌": (-0.6, -0.4), "仇": (-1.1, -0.7)},
    "month": {"用": (0.6, 0.4), "喜": (0.3, 0.2), "忌": (-0.3, -0.2), "仇": (-0.6, -0.4)},
    "year": {"用": (0.4, 0.3), "喜": (0.2, 0.15), "忌": (-0.2, -0.15), "仇": (-0.4, -0.25)},
}


def role_of(wx: str, bags: dict[str, list[str]]) -> str | None:
    for name in ("用", "喜", "忌", "仇"):
        if wx in bags[name]:
            return name
    return None


def bags_from_ge(ge: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "用": list(ge.get("yong_shen") or []),
        "喜": list(ge.get("xi_shen") or []),
        "忌": list(ge.get("ji_shen") or []),
        "仇": list(ge.get("chou_shen") or []),
    }


def apply_wx(scores: dict[int, float], wx: str | None, weight: float) -> None:
    if wx and weight:
        map_wx_to_scores(wx, weight, scores)


def apply_gz_roles(scores: dict[int, float], gz: str, table: dict[str, tuple[float, float]], bags: dict[str, list[str]]) -> dict[str, str | None]:
    gan_wx = WX_G.get(gz[0]) if gz else None
    zhi_wx = WX_Z.get(gz[1]) if gz and len(gz) > 1 else None
    rg = role_of(gan_wx or "", bags)
    rz = role_of(zhi_wx or "", bags)
    if rg and gan_wx:
        apply_wx(scores, gan_wx, table[rg][0])
    if rz and zhi_wx:
        apply_wx(scores, zhi_wx, table[rz][1])
    return {"gan_wx": gan_wx, "zhi_wx": zhi_wx, "gan_role": rg, "zhi_role": rz}


def generate(
    birth: datetime,
    sex: str,
    draw: datetime,
) -> dict[str, Any]:
    sex_n = parse_sex(sex)
    yun = build_dayun(birth, sex_n, at=draw)
    personal = yun["pillars"]
    draw_p = pillars_at(draw.year, draw.month, draw.day, 21)
    ge = analyze_geju(personal)
    bags = bags_from_ge(ge)
    scores: dict[int, float] = defaultdict(float)
    score_chart(draw_p, DRAW_W, scores)
    score_chart(personal, PERSONAL_W, scores)
    for role, w in B_W.items():
        for wx in bags[role]:
            apply_wx(scores, wx, w)
    th = ge.get("tiaohou") or {}
    if th.get("urgent") and th.get("need"):
        apply_wx(scores, th["need"], TIAOHOU_EXTRA)
    cur = yun["current_dayun"]
    ln = yun["current_liunian"]
    c_tag = apply_gz_roles(scores, cur["ganzhi"], C_W, bags)
    d_tag = apply_gz_roles(scores, ln["ganzhi"], D_W, bags)
    e_tags: dict[str, dict[str, str | None]] = {}
    for key in ("hour", "day", "month", "year"):
        e_tags[key] = apply_gz_roles(scores, draw_p[key], E_W[key], bags)
    f_notes: list[str] = []
    if c_tag["gan_role"] == "用" and d_tag["gan_role"] == "用":
        apply_wx(scores, c_tag["gan_wx"], 0.8)
        f_notes.append("當運用×流年用")
    elif c_tag["gan_role"] == "用" and d_tag["gan_role"] == "忌":
        apply_wx(scores, c_tag["gan_wx"], -0.5)
        f_notes.append("當運用×流年忌")
    elif c_tag["gan_role"] == "忌" and d_tag["gan_role"] == "用":
        apply_wx(scores, d_tag["gan_wx"], 0.3)
        f_notes.append("當運忌×流年用")
    if c_tag["gan_role"] == "仇" and d_tag["gan_role"] == "仇":
        apply_wx(scores, c_tag["gan_wx"], -0.8)
        f_notes.append("當運仇×流年仇")
    numbers = pick15(dict(scores))
    top = sorted(((n, round(s, 3)) for n, s in scores.items() if 1 <= n <= 49), key=lambda x: (-x[1], x[0]))[:15]
    return {
        "ruleVersion": RULE,
        "mode": "xiyong_personal_x_draw",
        "birth": birth.isoformat(timespec="minutes"),
        "sex": sex_n,
        "draw_datetime": f"{draw.year:04d}-{draw.month:02d}-{draw.day:02d}T21:30:00+08:00",
        "personal_pillars": personal,
        "draw_pillars": draw_p,
        "pattern": ge["pattern"],
        "yong_shen": ge["yong_shen"],
        "xi_shen": ge["xi_shen"],
        "ji_shen": ge["ji_shen"],
        "chou_shen": ge["chou_shen"],
        "tiaohou": ge["tiaohou"],
        "current_dayun": {"ganzhi": cur["ganzhi"], "shi_shen": cur.get("shi_shen"), **c_tag},
        "current_liunian": {"year": ln["year"], "ganzhi": ln["ganzhi"], "shi_shen": ln.get("shi_shen"), **d_tag},
        "draw_roles": e_tags,
        "interact": f_notes,
        "top15_scores": [{"n": n, "s": s} for n, s in top],
        "numbers": numbers,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--birth", required=True)
    ap.add_argument("--sex", required=True)
    ap.add_argument("--draw", required=True, help="攪珠日 YYYY-MM-DD")
    args = ap.parse_args()
    dy, dm, dd = [int(x) for x in args.draw.split("-")[:3]]
    out = generate(parse_dt(args.birth, 4), args.sex, datetime(dy, dm, dd, 21, 30, 0))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

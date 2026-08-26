# -*- coding: utf-8 -*-
"""天喜大運／格局自檢。"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tianxi_calendar import find_jie  # noqa: E402
from tianxi_dayun import build_dayun, is_forward as yun_fwd  # noqa: E402
from tianxi_engine import mingpan  # noqa: E402
from tianxi_geju import analyze_geju  # noqa: E402


def test_direction_table() -> None:
    assert yun_fwd("戊", "male") is True
    assert yun_fwd("戊", "female") is False
    assert yun_fwd("乙", "male") is False
    assert yun_fwd("乙", "female") is True


def test_jie_is_jie_not_qi() -> None:
    birth = datetime(1988, 2, 8, 4, 0, 0)
    nxt, name = find_jie(birth, True)
    prv, pname = find_jie(birth, False)
    assert name == "驚蟾"
    assert pname == "立春"
    assert nxt > birth
    assert prv < birth


def test_sample_male_1988() -> None:
    birth = datetime(1988, 2, 8, 4, 0, 0)
    at = datetime(2026, 8, 22, 21, 30, 0)
    yun = build_dayun(birth, "male", at=at)
    assert yun["pillars"]["year"] == "戊辰"
    assert yun["forward"] is True
    assert yun["jie"]["name"] == "驚蟾"
    assert yun["qiyun"]["years"] >= 1
    assert yun["current_dayun"]["ganzhi"]
    assert yun["current_liunian"]["year"] == 2026
    q = datetime.fromisoformat(yun["qiyun_solar"])
    assert q > birth


def test_male_female_opposite() -> None:
    birth = datetime(1988, 2, 8, 4, 0, 0)
    m = build_dayun(birth, "男")
    f = build_dayun(birth, "女")
    assert m["forward"] is True
    assert f["forward"] is False
    assert m["dayun"][1]["ganzhi"] != f["dayun"][1]["ganzhi"]


def test_geju_keys() -> None:
    birth = datetime(1988, 2, 8, 4, 0, 0)
    from tianxi_calendar import pillars_at

    ge = analyze_geju(pillars_at(birth))
    assert ge["pattern"]["primary"]
    assert ge["yong_shen"]
    assert isinstance(ge["xi_shen"], list)
    assert ge["day_master"]["gan"] == "癸"


def test_mingpan_merge() -> None:
    out = mingpan(datetime(1988, 2, 8, 4, 0, 0), "male", datetime(2026, 8, 22, 21, 30))
    assert out["engineId"] == "tianxi-mingpan-v1"
    assert out["dayun"]["current_liunian"]["ganzhi"]
    assert out["yong_shen"]


if __name__ == "__main__":
    test_direction_table()
    test_jie_is_jie_not_qi()
    test_sample_male_1988()
    test_male_female_opposite()
    test_geju_keys()
    test_mingpan_merge()
    print("ok")

# -*- coding: utf-8 -*-
"""天喜大運／格局／節氣自檢。"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tianxi_calendar import JINGZHE, find_jie, list_jieqi_year  # noqa: E402
from tianxi_dayun import build_dayun, is_forward as yun_fwd  # noqa: E402
from tianxi_engine import mingpan  # noqa: E402
from tianxi_geju import analyze_geju  # noqa: E402
from tianxi_jieqi_check import check_year  # noqa: E402


def test_direction_table() -> None:
    assert yun_fwd("\u620a", "male") is True
    assert yun_fwd("\u620a", "female") is False
    assert yun_fwd("\u4e59", "male") is False
    assert yun_fwd("\u4e59", "female") is True


def test_jie_is_jie_not_qi() -> None:
    birth = datetime(1988, 2, 8, 4, 0, 0)
    nxt, name = find_jie(birth, True)
    prv, pname = find_jie(birth, False)
    assert name == JINGZHE
    assert pname == "\u7acb\u6625"
    assert nxt > birth
    assert prv < birth
    assert nxt == datetime(1988, 3, 5, 16, 46, 32)
    assert prv == datetime(1988, 2, 4, 22, 42, 49)


def test_list_jieqi_1988() -> None:
    rows = list_jieqi_year(1988)
    assert len(rows) == 25
    assert rows[0]["name"] == "\u7acb\u6625"
    assert rows[0]["datetime"] == "1988-02-04T22:42:49"
    names = [r["name"] for r in rows]
    assert JINGZHE in names
    assert "\u9a5a\u87f2" not in names  # 蟲，不是蟄
    assert sum(1 for r in rows if r["is_jie"]) >= 12


def test_jieqi_check_sample_years() -> None:
    for y in (1988, 2026):
        out = check_year(y)
        assert out["ok"] is True, out
        assert out["max_scan_delta_sec"] <= 2


def test_sample_male_1988() -> None:
    birth = datetime(1988, 2, 8, 4, 0, 0)
    at = datetime(2026, 8, 22, 21, 30, 0)
    yun = build_dayun(birth, "male", at=at)
    assert yun["pillars"]["year"] == "\u620a\u8fb0"
    assert yun["forward"] is True
    assert yun["jie"]["name"] == JINGZHE
    assert yun["qiyun"]["years"] >= 1
    assert yun["current_dayun"]["ganzhi"]
    assert yun["current_liunian"]["year"] == 2026
    q = datetime.fromisoformat(yun["qiyun_solar"])
    assert q > birth


def test_male_female_opposite() -> None:
    birth = datetime(1988, 2, 8, 4, 0, 0)
    m = build_dayun(birth, "\u7537")
    f = build_dayun(birth, "\u5973")
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
    assert ge["day_master"]["gan"] == "\u7678"


def test_mingpan_merge() -> None:
    out = mingpan(datetime(1988, 2, 8, 4, 0, 0), "male", datetime(2026, 8, 22, 21, 30))
    assert out["engineId"] == "tianxi-mingpan-v1"
    assert out["dayun"]["current_liunian"]["ganzhi"]
    assert out["yong_shen"]


if __name__ == "__main__":
    test_direction_table()
    test_jie_is_jie_not_qi()
    test_list_jieqi_1988()
    test_jieqi_check_sample_years()
    test_sample_male_1988()
    test_male_female_opposite()
    test_geju_keys()
    test_mingpan_merge()
    print("ok")

# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tianxi_xiyong_pick import generate  # noqa: E402


def test_sample_1988() -> None:
    out = generate(datetime(1988, 2, 8, 4, 0), "male", datetime(2026, 8, 22, 21, 30))
    assert out["ruleVersion"] == "tianxi-xiyong-pick-v1"
    assert out["pattern"]["primary"] == "傷官格"
    assert "木" in out["yong_shen"]
    assert len(out["numbers"]) == 15
    assert out["numbers"] == sorted(set(out["numbers"]))
    assert all(1 <= n <= 49 for n in out["numbers"])
    assert out["current_dayun"]["ganzhi"]
    assert out["current_liunian"]["year"] == 2026


def test_sex_changes_yun() -> None:
    m = generate(datetime(1988, 2, 8, 4, 0), "男", datetime(2026, 8, 22, 21, 30))
    f = generate(datetime(1988, 2, 8, 4, 0), "女", datetime(2026, 8, 22, 21, 30))
    assert m["current_dayun"]["ganzhi"] != f["current_dayun"]["ganzhi"]
    assert m["numbers"] != f["numbers"]


if __name__ == "__main__":
    test_sample_1988()
    test_sex_changes_yun()
    print("ok")

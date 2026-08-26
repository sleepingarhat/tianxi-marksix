# 天喜六合彩研究（tianxi-marksix）

天喜命盤 + 攪珠研究工具。四柱、格局喜用、男女大運流年、奇門地盤、15 碼取數——同一倉庫。

> 可重現研究工具，非投注建議。

---

## 命盤引擎（新）

| 引擎 | 檔案 | 說明 |
|------|------|------|
| **tianxi-mingpan-v1** | `src/tianxi_engine.py` | 四柱 + 格局喜用 + 大運流年 |
| **tianxi-dayun-v2** | `src/tianxi_dayun.py` | 性別順逆、節氣分鐘起運、當運、流年 |
| **tianxi-geju-xiyong-v1** | `src/tianxi_geju.py` | 月令定格 + 從格門檻 + 喜用忌仇表 |
| **tianxi-jieqi-check-v1** | `src/tianxi_jieqi_check.py` | 二十四節氣交節對照（起運精度） |

```bash
pip install -r requirements.txt
python src/tianxi_engine.py --birth 1988-02-08T04:00 --sex male --at 2026-08-22T21:30
python tests/test_dayun_geju.py
python src/tianxi_jieqi_check.py 1988
```

細則：[`docs/TIANXI_DAYUN.md`](docs/TIANXI_DAYUN.md) · [`docs/TIANXI_GEJU_XIYONG.md`](docs/TIANXI_GEJU_XIYONG.md)

---

## 取號

| 功能 | 狀態 |
|------|------|
| 攪珠日八字 → 15 碼 | 獨測，不接喜用 |
| 攪珠日奇門地盤 → 15 碼 | 獨測，不接喜用 |
| 個人八字 × 攪珠日八字 | `personal-x-draw-v1` 骨架 |
| **喜用 × 當運 × 流年 × 攪珠日** | **`tianxi-xiyong-pick-v1`** |
| 個人奇門 × 攪珠日奇門 | 見 `docs/PERSONAL_X_DRAW.md` |

```bash
python src/personal_x_draw_bazi.py --personal 1988-02-08T04:00 --draw 2026-08-22
python src/tianxi_xiyong_pick.py --birth 1988-02-08T04:00 --sex male --draw 2026-08-22
python tests/test_xiyong_pick.py
```

細則：[`docs/TIANXI_XIYONG_PICK.md`](docs/TIANXI_XIYONG_PICK.md)

---

## 總則

| 項目 | 定案 |
|------|------|
| 時間錨點 | 攪珠日 **21:30 HKT** |
| 年柱 | 立春換年 |
| 起運 | 十二節 + 分鐘折算 |
| 每路產出 | **15** 個不重複 1–49 |
| 計分 | 正碼 +1；特碼在池 +0.5 |

---

## 目錄

```
src/
  tianxi_engine.py      # 總盤
  tianxi_dayun.py       # 大運流年
  tianxi_geju.py        # 格局喜用
  tianxi_calendar.py    # 曆法／節氣
  tianxi_jieqi_check.py  # 節氣對照
  tianxi_xiyong_pick.py # 喜用取號
  personal_x_draw_bazi.py
docs/
  TIANXI_DAYUN.md
  TIANXI_GEJU_XIYONG.md
  TIANXI_XIYONG_PICK.md
  PERSONAL_X_DRAW.md
tests/
  test_dayun_geju.py
  test_xiyong_pick.py
```

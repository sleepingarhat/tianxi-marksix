# 天喜六合彩研究（tianxi-marksix）

**主路徑（現行）：最簡兩術**——四柱八字、奇門遁甲（**僅地盤取數**）。  
目標：取代 [`tianxi-site.pages.dev/marksix`](https://tianxi-site.pages.dev/marksix/)。

> 可重現研究工具，非投注建議。

---

## 現行重點

| 功能 | 狀態 | 說明 |
|------|------|------|
| 攪珠日八字 → 15 碼 | 規格已有 | 日3時4 干支映射 + pick15 |
| 攪珠日奇門地盤 → 15 碼 | 規格已有 | 拆補 + 地盤 |
| **個人八字 × 攪珠日八字 → 15** | **已實作 v1** | `src/personal_x_draw_bazi.py` |
| **個人奇門 × 攪珠日奇門 → 15** | 下一刀 | 見 `docs/PERSONAL_X_DRAW.md` |

詳規：[`docs/PERSONAL_X_DRAW.md`](docs/PERSONAL_X_DRAW.md)

```bash
pip install -r requirements.txt
python src/personal_x_draw_bazi.py --personal 1988-02-08T04:00 --draw 2026-08-22
```

---

## 已擱置（不進入正式取號）

以下僅歷史／研究檔，**不作為推號依據**：

- 滴天髓眾寡喜用引擎（`yongshen_c.py`）
- 完整子平喜用／從格／調候升主推號
- 大運敘事（`dayun.py`）
- 格局 ML／知識圖譜方向

---

## 總則

| 項目 | 定案 |
|------|------|
| 時間錨點 | 攪珠日 **21:30 HKT** |
| 每路產出 | **15** 個不重複 1–49 |
| 分段 | 五段目標各 3；不足他段補 |
| 計分 | 正碼 +1；特碼在池 +0.5 |

`ruleVersion` 個人合參：**`personal-x-draw-v1`**  
純當日盤仍可用規格 **`bazi-qimen-fifteen-v1`**。

---

## 目錄

```
src/
  pick15.py
  personal_x_draw_bazi.py   # 個人八字×攪珠日
  yongshen_c.py / dayun.py  # 擱置研究
docs/
  PERSONAL_X_DRAW.md
  ZIPING_YONGSHEN_C.md      # 擱置
```

# 結構化標註 Schema（滴天髓主腦）

> 配合 `ruleId: yongshen-ditian-zhonggua-v1`  
> 目標：格局／十神可重現、可版本化、可測。

## 設計原則

1. **規則先於模型**：主路徑由確定性規則產出；ML 僅可作可選旁路。
2. **版本綁定**：任何計分或格局表變更必須升 `ruleId`（v2…），舊結果不可混比。
3. **兩層評估分開**  
   - 結構層：十神／眾寡／格局標籤是否穩定、（有金標時）分類準確率  
   - 應用層：用神池或 15 碼對攪珠的覆蓋率／字數（100 期）

## JSON 字段

| 字段 | 類型 | 說明 |
|------|------|------|
| `ruleId` | string | 規則版本 |
| `datetime` | string | ISO8601，預設攪珠日 21:30 +08:00 |
| `pillars` | object | year/month/day/hour 干支 |
| `day_master` | object | gan, wx |
| `shi_shen` | object | 年柱月柱日柱時柱：gan 十神、zhi_ben 支本氣十神 |
| `zhong_gua` | object | score 五行分、party_self/other、ratio、majority_wx、rooted |
| `pattern` | object | primary 主標籤、tags[]、confidence=`rule`|
| `yong_shen` | string[] | 用神五行 |
| `xi_shen` | string[] | 喜神 |
| `ji_shen` | string[] | 忌神 |
| `tiaohou` | object | need, urgent |
| `note` | string[] | 可選調試說明 |

### pattern.primary 枚舉（v1）

- `從勢` / `從強`
- `交戰通關`
- `正格(官殺|財|食傷|印)`
- `眾寡扶抑`
- `特殊待定`（飛天祿馬等，v1 不強判）

### pattern.tags 示例

`傷官` `印` `食神` `七殺` `財` `官` — 用於「傷官配印」「食神制殺」等組合檢索，不單獨當最終用神。

## 十神判定（相對日主）

按日干陰陽與五行生剋定正偏：

| 關係 | 同陰陽 | 異陰陽 |
|------|--------|--------|
| 同我 | 比肩 | 劫財 |
| 我生 | 食神 | 傷官 |
| 我剋 | 偏財 | 正財 |
| 剋我 | 七殺 | 正官 |
| 生我 | 偏印 | 正印 |

地支先取本氣天干再套上表。

## 可測指標

### 無金標（常規）

| 指標 | 說明 |
|------|------|
| 穩定性 | 同輸入輸出完全一致 |
| pattern 分佈 | 100 期 primary 直方圖 |
| 用神蓋正碼率 | 用神河圖池 ∩ 六正碼 / 600 |
| 對照 | 舊月令簡表喜用蓋碼率（期望≈40%） |

### 有金標（可選）

| 指標 | 說明 |
|------|------|
| 格局準確率 | primary 或 tags 與人工金標一致比例 |
| 用神命中率 | yong_shen 與金標用神集合相交 |

未建金標前不宣稱「格局準確率 xx%」。

## 與取號

本 schema 服務研究盤與個人盤。  
攪珠 15 碼預設仍以干支映射為主；`yong_shen` 池僅 A/B。

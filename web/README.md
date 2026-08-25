# 六合彩研究頁（web）

路徑：`web/marksix/index.html` + `engine.js`

## 功能

1. **純八字 / 純奇門**：詳細起盤、推號說明、本期 15 碼
2. **期期對比**：對官方結果計字（正碼+1／特碼+0.5）
3. **100 期回測**：純當日盤平均字、≥5 期數、明細表
4. **個人混合**：輸入出生日時 → 個人八字盤＋個人奇門盤＋混合 15 碼

## 本地預覽

```bash
cd web/marksix && python -m http.server 8080
# 開 http://localhost:8080/
```

或直接用 GitHub Pages / 複製到 `tianxi-site/marksix/`。

## 依賴

- CDN：`lunar-javascript`（排盤）
- 數據：`hk-mark-six-2002-now` raw JSON

## 與正式站

若要把本頁取代 `https://tianxi-site.pages.dev/marksix/`：

1. 將 `engine.js`、`index.html` 拷入 `tianxi-site/marksix/`（可保留站內 shell／樣式再嵌）
2. 或給 connector 開 `tianxi-site` 寫入權再自動同步

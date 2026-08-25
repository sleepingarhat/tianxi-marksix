# 正式站接入（tianxi-site/marksix）

已準備好套站殼版本：

| 檔案 | 用途 |
|------|------|
| `web/marksix/site-index.html` | 正式站 `marksix/index.html`（brandbar／botnav／tokens／結果／統計＋八字奇門） |
| `web/marksix/engine.js` | 同路徑 `marksix/engine.js` |

## 手動拷入（若 connector 無 tianxi-site 寫入權）

```bash
cp web/marksix/site-index.html ../tianxi-site/marksix/index.html
cp web/marksix/engine.js ../tianxi-site/marksix/engine.js
cd ../tianxi-site && git add marksix && git commit -m "feat(marksix): 八字／奇門 chaibu-v3" && git push
```

Pages → https://tianxi-site.pages.dev/marksix/

## 功能

- 保留：最新攪珠、號碼統計、站內 shell
- 換走：舊四術研究簿
- 新增：純八字／純奇門、個人混合（個人＝出生時奇門終身盤）、100 期回測

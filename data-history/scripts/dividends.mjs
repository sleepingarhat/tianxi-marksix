#!/usr/bin/env node
// 六合彩每期派彩收料（HKJC 官方 GraphQL）。
// 輸出 data/dividends.json：{ [drawId]: { draw, date, unitBet, prizes:[{tier,winningUnit,dividend}] } }
// 只增不改已收期數（除非該期派彩仍為空）；--full 由 2002 起全部回補。
import { readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ENDPOINT = 'https://info.cld.hkjc.com/graphql/base/';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, '..', 'data', 'dividends.json');

const GQL = `fragment lotteryDrawsFragment on LotteryDraw {
  id
  year
  no
  openDate
  closeDate
  drawDate
  status
  snowballCode
  snowballName_en
  snowballName_ch
  lotteryPool {
    sell
    status
    totalInvestment
    jackpot
    unitBet
    estimatedPrize
    derivedFirstPrizeDiv
    lotteryPrizes {
      type
      winningUnit
      dividend
    }
  }
  drawResult {
    drawnNo
    xDrawnNo
  }
}

query marksixResult($lastNDraw: Int, $startDate: String, $endDate: String, $drawType: LotteryDrawType) {
  lotteryDraws(lastNDraw: $lastNDraw, startDate: $startDate, endDate: $endDate, drawType: $drawType) {
    ...lotteryDrawsFragment
  }
}`;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fetchRange(startDate, endDate) {
  const body = JSON.stringify({ operationName: 'marksixResult', query: GQL, variables: { startDate, endDate, drawType: 'All' } });
  let err = null;
  for (let k = 0; k < 5; k++) {
    try {
      const res = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (tianxi-marksix dividends)', Origin: 'https://bet.hkjc.com', Referer: 'https://bet.hkjc.com/' },
        body,
      });
      const j = await res.json();
      if (j?.data?.lotteryDraws) return j.data.lotteryDraws;
      if (j?.errors) throw new Error(JSON.stringify(j.errors));
    } catch (e) { err = e; }
    await sleep(800 * (k + 1));
  }
  throw err ?? new Error('fetch failed');
}

function quarters(from, to) {
  const q = [];
  for (let y = from; y <= to; y++) for (const [a, b] of [['0101', '0331'], ['0401', '0630'], ['0701', '0930'], ['1001', '1231']]) q.push([`${y}${a}`, `${y}${b}`]);
  return q;
}

async function main() {
  const full = process.argv.includes('--full');
  let out = {};
  if (!full && existsSync(OUT)) out = JSON.parse(await readFile(OUT, 'utf8'));
  const now = new Date().getUTCFullYear();
  const from = full || !Object.keys(out).length ? 2002 : now - 1;
  let added = 0;
  for (const [sd, ed] of quarters(from, now)) {
    if (Number(sd) > Number(new Date().toISOString().slice(0, 10).replace(/-/g, ''))) break;
    const rows = await fetchRange(sd, ed);
    for (const r of rows) {
      if (!r || r.status !== 'Result') continue;
      const prizes = (r.lotteryPool?.lotteryPrizes || [])
        .map((p) => ({ tier: Number(p.type), winningUnit: Number(p.winningUnit) || 0, dividend: Number(p.dividend) || 0 }))
        .filter((p) => p.tier >= 1 && p.tier <= 7)
        .sort((a, b) => a.tier - b.tier);
      if (!prizes.length) continue;
      const prev = out[r.id];
      if (prev && prev.prizes?.length) continue; // 已收，唔改
      out[r.id] = {
        draw: `${String(r.year).slice(2)}/${String(r.no).padStart(3, '0')}`,
        date: (r.drawDate || '').slice(0, 10),
        unitBet: Number(r.lotteryPool?.unitBet) || 10,
        prizes,
      };
      added++;
    }
    await sleep(200);
  }
  const sorted = Object.fromEntries(Object.entries(out).sort((a, b) => (a[1].date < b[1].date ? 1 : -1)));
  await writeFile(OUT, JSON.stringify(sorted) + '\n');
  console.log(`dividends: +${added}, total ${Object.keys(sorted).length}`);
}

main().catch((e) => { console.error(e); process.exit(1); });

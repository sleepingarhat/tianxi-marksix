/* tianxi marksix engine — pure bazi / chaibu qimen / personal hybrid */
(function (global) {
  'use strict';
  var GAN = '甲乙丙丁戊己庚辛壬癸';
  var ZHI = '子丑寅卯辰巳午未申酉戌亥';
  var YI_ORDER = '戊己庚辛壬癸丁丙乙'.split('');
  var SAN_QI = { 乙: 1, 丙: 1, 丁: 1 };
  var WX_G = { 甲: '木', 乙: '木', 丙: '火', 丁: '火', 戊: '土', 己: '土', 庚: '金', 辛: '金', 壬: '水', 癸: '水' };
  var WX_TAILS = { 水: [1, 6], 火: [2, 7], 木: [3, 8], 金: [4, 9], 土: [0, 5] };
  var YANG_JU = {
    冬至: [1, 7, 4], 小寒: [2, 8, 5], 大寒: [3, 9, 6], 立春: [8, 5, 2], 雨水: [9, 6, 3],
    驚蟄: [1, 7, 4], 惊蛰: [1, 7, 4], 春分: [3, 9, 6], 清明: [2, 8, 5], 穀雨: [3, 9, 6], 谷雨: [3, 9, 6],
    立夏: [4, 1, 7], 小滿: [5, 2, 8], 小满: [5, 2, 8], 芒種: [6, 3, 9], 芒种: [6, 3, 9]
  };
  var YIN_JU = {
    夏至: [9, 3, 6], 小暑: [8, 2, 5], 大暑: [7, 1, 4], 立秋: [2, 5, 8], 處暑: [1, 4, 7], 处暑: [1, 4, 7],
    白露: [9, 3, 6], 秋分: [7, 1, 4], 寒露: [8, 2, 5], 霜降: [7, 1, 4], 立冬: [6, 9, 3], 小雪: [5, 8, 2], 大雪: [4, 7, 1]
  };
  var DRAW_W = { hour: 4, day: 3, month: 2, year: 1.5, day_master_wx: 1 };
  var PERSONAL_W = { day: 3, hour: 2.5, month: 2, year: 1.5, day_master_wx: 1 };
  var Q_DRAW_W = { zf: 3.5, zo: 3, sanqi: 2.5, other: 1.5 };
  var Q_PERSONAL_W = { zf: 2.5, zo: 2, sanqi: 2, other: 1 };

  function band(n) { return n <= 9 ? 0 : n <= 19 ? 1 : n <= 29 ? 2 : n <= 39 ? 3 : 4; }
  function pick15(scores) {
    var by = [[], [], [], [], []];
    Object.keys(scores).forEach(function (k) {
      var n = +k; if (n >= 1 && n <= 49) by[band(n)].push([n, scores[n]]);
    });
    by.forEach(function (b) { b.sort(function (a, c) { return c[1] - a[1] || a[0] - c[0]; }); });
    var chosen = [], set = {};
    for (var i = 0; i < 5; i++) by[i].slice(0, 3).forEach(function (x) { chosen.push(x[0]); set[x[0]] = 1; });
    var remain = [];
    for (var bi = 0; bi < 5; bi++) by[bi].forEach(function (x) { if (!set[x[0]]) remain.push(x); });
    remain.sort(function (a, c) { return c[1] - a[1] || a[0] - c[0]; });
    for (var r = 0; r < remain.length && chosen.length < 15; r++) chosen.push(remain[r][0]);
    for (var n = 1; n <= 49 && chosen.length < 15; n++) if (chosen.indexOf(n) < 0) chosen.push(n);
    return chosen.slice(0, 15).sort(function (a, b) { return a - b; });
  }

  function pillarsAt(y, m, d, hour) {
    var Solar = global.Solar;
    if (!Solar) throw new Error('需要 lunar-javascript');
    var solar = Solar.fromYmdHms(y, m, d, hour, hour === 21 ? 30 : 0, 0);
    var ec = solar.getLunar().getEightChar();
    return { year: ec.getYear(), month: ec.getMonth(), day: ec.getDay(), hour: ec.getTime(), dayMaster: ec.getDay().charAt(0), dayMasterWx: WX_G[ec.getDay().charAt(0)] || '' };
  }

  function mapGz(gz, weight, scores) {
    if (!gz || gz.length < 2) return;
    var gi = GAN.indexOf(gz.charAt(0)) + 1, zi = ZHI.indexOf(gz.charAt(1)) + 1;
    if (gi < 1 || zi < 1) return;
    var bases = [gi, zi, gi + zi, Math.abs(gi * zi), (gi * 6 + zi) % 49 + 1], cands = {};
    bases.forEach(function (base) {
      var n = ((base - 1) % 49) + 1; cands[n] = 1; cands[((n + 8) % 49) + 1] = 1; cands[((n + 23) % 49) + 1] = 1;
    });
    Object.keys(cands).forEach(function (k) { scores[+k] = (scores[+k] || 0) + weight; });
  }
  function mapWx(wx, weight, scores) {
    var tails = WX_TAILS[wx] || [];
    for (var n = 1; n <= 49; n++) {
      var t = n % 10;
      if (tails.indexOf(t) >= 0 || (t === 0 && tails.indexOf(0) >= 0)) scores[n] = (scores[n] || 0) + weight;
    }
  }
  function scoreChart(pillars, weights, scores) {
    ['year', 'month', 'day', 'hour'].forEach(function (k) { if (weights[k]) mapGz(pillars[k], weights[k], scores); });
    if (weights.day_master_wx) mapWx(pillars.dayMasterWx || WX_G[pillars.day.charAt(0)], weights.day_master_wx, scores);
  }

  function pureBazi(y, m, d) {
    var pillars = pillarsAt(y, m, d, 21), scores = {};
    scoreChart(pillars, DRAW_W, scores);
    return { mode: 'pure_bazi', pillars: pillars, method: { anchor: '攪珠日 21:30 HKT', weights: '時4 日3 月2 年1.5 + 日主河圖1', pick: '五段目標各3，不足他段補' }, numbers: pick15(scores) };
  }
  function personalBazi(py, pm, pd, ph, dy, dm, dd) {
    var personal = pillarsAt(py, pm, pd, ph), draw = pillarsAt(dy, dm, dd, 21), scores = {};
    scoreChart(draw, DRAW_W, scores); scoreChart(personal, PERSONAL_W, scores);
    return { mode: 'bazi_personal_x_draw', personal_pillars: personal, draw_pillars: draw, numbers: pick15(scores) };
  }

  function jieqiAround(y, m, d) {
    var solar = global.Solar.fromYmd(y, m, d);
    var lunar = solar.getLunar();
    var prev = lunar.getPrevJieQi(true);
    var jqSolar = prev.getSolar();
    var jieStart = new Date(jqSolar.getYear(), jqSolar.getMonth() - 1, jqSolar.getDay());
    var yang = true, scan = lunar;
    try {
      for (var i = 0; i < 24; i++) {
        var p = scan.getPrevJieQi(true), nm = p.getName();
        if (nm === '冬至') { yang = true; break; }
        if (nm === '夏至') { yang = false; break; }
        scan = p.getSolar().getLunar();
      }
    } catch (e) {}
    return { name: prev.getName(), jieStart: jieStart, yang: yang };
  }
  function fuTou(y, m, d) {
    for (var back = 0; back < 15; back++) {
      var dt = new Date(y, m - 1, d - back);
      var p = pillarsAt(dt.getFullYear(), dt.getMonth() + 1, dt.getDate(), 12);
      if (p.day.charAt(0) === '甲' || p.day.charAt(0) === '己') return new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    }
    return new Date(y, m - 1, d);
  }
  function resolveKey(name, table) {
    if (table[name]) return name;
    var keys = Object.keys(table);
    for (var i = 0; i < keys.length; i++) if (keys[i].charAt(0) === name.charAt(0)) return keys[i];
    return keys[0];
  }
  /** 拆補：符頭起三元；局用當日節氣表（超神不回退上一節） */
  function yuanJu(y, m, d) {
    var jq = jieqiAround(y, m, d);
    var yang = jq.yang, table = yang ? YANG_JU : YIN_JU;
    var key = resolveKey(jq.name, table);
    var ft = fuTou(y, m, d);
    var target = new Date(y, m - 1, d);
    var daysFromFt = Math.floor((target - ft) / 86400000);
    var yi = ((daysFromFt % 15) + 15) % 15;
    yi = Math.floor(yi / 5);
    var yuan = ['上元', '中元', '下元'][yi];
    var ju = table[key][yi];
    var daysInto = Math.floor((target - jq.jieStart) / 86400000);
    return {
      yang: yang, ju: ju, yuan: yuan,
      meta: {
        jie: jq.name, ju_key: key,
        jie_start: jq.jieStart.toISOString().slice(0, 10),
        fu_tou: ft.toISOString().slice(0, 10),
        days_from_fu_tou: daysFromFt,
        days_into_jie: daysInto,
        chao_shen: ft < jq.jieStart,
        method: 'chaibu'
      }
    };
  }
  function arrangeDi(yang, ju) {
    var path = [1, 8, 3, 4, 9, 2, 7, 6], startIdx = path.indexOf(ju);
    if (ju === 5) startIdx = path.indexOf(2); if (startIdx < 0) startIdx = 0;
    var di = {};
    for (var i = 0; i < YI_ORDER.length; i++) {
      var palace = yang ? path[(startIdx + i) % 8] : path[(startIdx - i + 80) % 8];
      di[palace] = YI_ORDER[i];
    }
    di[5] = di[2] || '戊'; return di;
  }
  function xunShouYi(dayGz) {
    var gi = GAN.indexOf(dayGz.charAt(0)), zi = ZHI.indexOf(dayGz.charAt(1)), idx = 0;
    for (var i = 0; i < 60; i++) if (i % 10 === gi && i % 12 === zi) { idx = i; break; }
    return '戊己庚辛壬癸'.charAt(Math.floor(idx / 10));
  }
  function castQimen(y, m, d, hour) {
    var pillars = pillarsAt(y, m, d, hour), yj = yuanJu(y, m, d), di = arrangeDi(yj.yang, yj.ju);
    var yi0 = xunShouYi(pillars.day), origin = 5;
    Object.keys(di).forEach(function (pk) { var p = +pk; if (di[p] === yi0 && p !== 5) origin = p; });
    var hg = pillars.hour.charAt(0), target = hg === '甲' ? yi0 : (YI_ORDER.indexOf(hg) >= 0 ? hg : yi0), zf = origin;
    Object.keys(di).forEach(function (pk) { var p = +pk; if (di[p] === target && p !== 5) zf = p; });
    return { yang: yj.yang, ju: yj.ju, yuan: yj.yuan, pillars: pillars, di_pan: di, zhi_fu_palace: zf, zhi_fu_origin: origin, meta: yj.meta };
  }
  function ganNums(gan) {
    var i = GAN.indexOf(gan) + 1, out = []; if (i < 1) return out;
    for (var k = 0; k < 5; k++) out.push(((i + k * 10 - 1) % 49) + 1); return out;
  }
  function palaceNums(p) {
    var out = []; for (var k = 0; k < 6; k++) out.push(((p + k * 9 - 1) % 49) + 1); return out;
  }
  function addPanScores(pan, weights, scores) {
    Object.keys(pan.di_pan).forEach(function (pk) {
      var palace = +pk; if (palace === 5) return;
      var gan = pan.di_pan[palace], w = weights.other;
      if (palace === pan.zhi_fu_palace) w = weights.zf;
      else if (palace === pan.zhi_fu_origin) w = weights.zo;
      else if (SAN_QI[gan]) w = weights.sanqi;
      ganNums(gan).forEach(function (n) { scores[n] = (scores[n] || 0) + w; });
      palaceNums(palace).forEach(function (n) { scores[n] = (scores[n] || 0) + w * 0.5; });
    });
  }
  function pureQimen(y, m, d) {
    var pan = castQimen(y, m, d, 21), scores = {};
    addPanScores(pan, Q_DRAW_W, scores);
    return {
      mode: 'pure_qimen', pan: pan,
      method: {
        dingju: '拆補 · 符頭起三元（0–4上／5–9中／10–14下）· 局取當日節氣表',
        extract: '僅地盤；值符宮3.5／原宮3／三奇2.5／其餘1.5',
        pick: '五段×3'
      },
      numbers: pick15(scores)
    };
  }
  function personalQimen(py, pm, pd, ph, dy, dm, dd) {
    var personal = castQimen(py, pm, pd, ph), draw = castQimen(dy, dm, dd, 21), scores = {};
    addPanScores(draw, Q_DRAW_W, scores); addPanScores(personal, Q_PERSONAL_W, scores);
    return { mode: 'qimen_personal_x_draw', personal: personal, draw: draw, numbers: pick15(scores) };
  }
  function scorePred(pred, numbers, special) {
    var set = {}; pred.forEach(function (n) { set[n] = 1; });
    var hit = []; (numbers || []).forEach(function (n) { if (set[n]) hit.push(n); });
    var s = hit.length, spHit = special != null && set[special];
    if (spHit) s += 0.5;
    return { score: s, hit_zheng: hit, hit_special: !!spHit };
  }

  global.TXMarkSixEngine = {
    pureBazi: pureBazi, pureQimen: pureQimen, personalBazi: personalBazi, personalQimen: personalQimen,
    pillarsAt: pillarsAt, castQimen: castQimen, scorePred: scorePred,
    ruleVersion: 'bazi-qimen-fifteen-v1 + personal-x-draw-v1 + qimen-chaibu-v1'
  };
})(typeof window !== 'undefined' ? window : globalThis);

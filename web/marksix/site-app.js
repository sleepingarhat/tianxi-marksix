(function(){
  'use strict';
  var RAW='https://raw.githubusercontent.com/sleepingarhat/hk-mark-six-2002-now/main/data/';
  var LATEST_URL=RAW+'latest.json', HISTORY_URL=RAW+'mark-six.json';
  var RED=new Set([1,2,7,8,12,13,18,19,23,24,29,30,34,35,40,45,46]);
  var BLUE=new Set([3,4,9,10,14,15,20,25,26,31,36,37,41,42,47,48]);
  function grp(n){return RED.has(n)?'red':BLUE.has(n)?'blue':'green';}
  function ball(n,size,special){return '<span class="m6-ball m6-ball--'+(size||'md')+' '+grp(n)+(special?' special':'')+'">'+n+'</span>';}
  function ballHit(n,hits,sp){var c='m6-ball m6-ball--sm '+grp(n)+(hits&&hits.indexOf(n)>=0?' hit':'')+(sp!=null&&n===sp?' sp':'');return '<span class="'+c+'">'+n+'</span>';}
  var TIER={1:'頭獎',2:'二獎',3:'三獎',4:'四獎',5:'五獎',6:'六獎',7:'七獎'};
  var WD=['日','一','二','三','四','五','六'];
  function money(v){if(v==null||v==='')return'';var n=Number(v);return isNaN(n)?String(v):'$'+n.toLocaleString('en-US');}
  function num(v){var n=Number(v);return isNaN(n)?String(v):n.toLocaleString('en-US');}
  function cnDate(iso){if(!iso)return'';var m=iso.match(/^(\d{4})-(\d{2})-(\d{2})/);if(!m)return iso;var d=new Date(Date.UTC(+m[1],+m[2]-1,+m[3]));return +m[1]+'年'+(+m[2])+'月'+(+m[3])+'日（'+WD[d.getUTCDay()]+'）';}
  var HISTORY=[],LATEST=null,LATEST_YEAR='',PERIOD='100',SORT='num',byDate={};
  var mode='pure',E=window.TXMarkSixEngine;
  if(E) document.getElementById('ruleVer').textContent=E.ruleVersion;

  function renderResult(){
    var el=document.getElementById('m6-result');
    if(!LATEST){el.innerHTML='<div class="m6-state err">未能載入攪珠結果。</div>';return;}
    var d=LATEST,ballsHTML='';
    d.numbers.forEach(function(n){ballsHTML+=ball(n,'lg',false);});
    ballsHTML+='<span class="m6-plus">+</span>'+ball(d.special,'lg',true);
    var prizes=d.prizes||[],showUnits=prizes.some(function(p){return p.winningUnit!=null&&p.winningUnit!=='';});
    var showDividend=prizes.some(function(p){return p.dividend!=null&&p.dividend!=='';});
    var rows='';
    prizes.forEach(function(p){
      rows+='<tr class="'+(p.tier===1?'t1':'')+'"><td>'+(TIER[p.tier]||('第'+p.tier))+'</td>'+
        (showUnits?'<td class="units">'+num(p.winningUnit)+'</td>':'')+
        (showDividend?'<td class="amt">'+money(p.dividend)+'</td>':'')+'</tr>';
    });
    var nd=d.nextDraw,nextLine=nd&&nd.date?cnDate(nd.date)+(nd.estimatedPrize?' · 估計頭獎基金 '+money(nd.estimatedPrize):''):'待 HKJC 公佈';
    el.innerHTML='<div class="m6-rhead"><span class="draw">第 '+d.draw+' 期</span><span class="date">'+cnDate(d.date)+'</span>'+
      (d.snowball?'<span class="m6-snow">'+d.snowball+'</span>':'')+'</div>'+
      '<div class="m6-balls">'+ballsHTML+'</div><div class="m6-balls-cap">攪珠結果 · 最後一個（＋）為特別號碼</div>'+
      (rows?'<table class="m6-prize"><thead><tr><th>獎級</th>'+(showUnits?'<th>中獎注數</th>':'')+(showDividend?'<th>每注獎金</th>':'')+'</tr></thead><tbody>'+rows+'</tbody></table>':'')+
      '<div class="m6-rfoot">'+(d.totalInvestment!=null&&d.totalInvestment!==''?'<div class="m6-stat"><div class="k">總投注額</div><div class="v">'+money(d.totalInvestment)+'</div></div>':'')+
      '<div class="m6-stat"><div class="k">下期攪珠</div><div class="v" style="font-size:12px;line-height:1.4">'+nextLine+'</div></div></div>';
    document.getElementById('m6-ticker').innerHTML='<strong>第 '+d.draw+' 期</strong> · '+d.numbers.join(' ')+' ＋'+d.special+' · '+cnDate(d.date)+(d.snowball?' · '+d.snowball:'');
  }
  function computeStats(periodKey){
    var win;if(periodKey==='ytd')win=HISTORY.filter(function(d){return d.date.slice(0,4)===LATEST_YEAR;});
    else{var n=parseInt(periodKey,10);win=HISTORY.slice(Math.max(0,HISTORY.length-n));}
    var count={},maxOm={},curOm={},run={};for(var i=1;i<=49;i++){count[i]=0;maxOm[i]=0;run[i]=0;}
    win.forEach(function(d){var has={};d.numbers.forEach(function(x){has[x]=1;});for(var v=1;v<=49;v++){if(has[v]){count[v]++;if(run[v]>maxOm[v])maxOm[v]=run[v];run[v]=0;}else run[v]++;}});
    for(var w=1;w<=49;w++)if(run[w]>maxOm[w])maxOm[w]=run[w];
    for(var t=1;t<=49;t++)curOm[t]=HISTORY.length;
    for(var z=1;z<=49;z++)for(var k2=HISTORY.length-1,gap=0;k2>=0;k2--,gap++)if(HISTORY[k2].numbers.indexOf(z)!==-1){curOm[z]=gap;break;}
    return{count:count,maxOm:maxOm,curOm:curOm};
  }
  function renderStats(){
    var s=computeStats(PERIOD),grid=document.getElementById('m6-numgrid'),maxCount=0;
    for(var i=1;i<=49;i++)if(s.count[i]>maxCount)maxCount=s.count[i];
    var order=[];for(var n=1;n<=49;n++)order.push(n);
    if(SORT==='hot')order.sort(function(a,b){return s.count[b]-s.count[a]||a-b;});
    else if(SORT==='due')order.sort(function(a,b){return s.curOm[b]-s.curOm[a]||a-b;});
    var html='';order.forEach(function(n){var heat=maxCount?(s.count[n]/maxCount):0;
      html+='<div class="m6-cell"><div class="heat" style="opacity:'+(0.15+heat*0.85).toFixed(2)+'"></div>'+ball(n,'sm',false)+
        '<div class="row"><span>開</span><b>'+s.count[n]+'</b></div><div class="row"><span>遺</span><b class="'+(s.curOm[n]>=10?'due':'')+'">'+s.curOm[n]+'</b></div><div class="row"><span>期</span><b>'+s.maxOm[n]+'</b></div></div>';});
    grid.innerHTML=html;
  }
  function buildSeg(id,items,getActive,onPick){
    var box=document.getElementById(id);
    box.innerHTML=items.map(function(it){return '<button data-v="'+it.v+'"'+(it.v===getActive()?' class="active":"')+'>'+it.label+'</button>';}).join('');
    box.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){onPick(b.getAttribute('data-v'));box.querySelectorAll('button').forEach(function(x){x.classList.remove('active');});b.classList.add('active');});});
  }
  function ballsHTML(nums,hits,sp){return '<div class="m6-nums">'+nums.map(function(n){return ballHit(n,hits,sp);}).join('')+'</div>';}
  function pillarsHTML(p,t){return '<div><b>'+t+'</b> '+p.year+' '+p.month+' '+p.day+' '+p.hour+' · 日主 '+p.dayMaster+'（'+(p.dayMasterWx||'')+'）</div>';}
  function panHTML(pan,t){var di=pan.di_pan,cells=[];[4,9,2,3,5,7,8,1,6].forEach(function(p){cells.push(p+':'+(di[p]||'-'));});
    return '<div><b>'+t+'</b> '+(pan.yang?'陽':'陰')+'遁'+pan.ju+'局 '+pan.yuan+' · 值符宮'+pan.zhi_fu_palace+(pan.shi_gan_palace!=null?' · 時乾宮'+pan.shi_gan_palace:'')+
      '<br><span class="m6-note">地盤 '+cells.join(' · ')+'</span>'+(pan.meta?'<br><span class="m6-note">節氣 '+pan.meta.jie+(pan.meta.fu_tou_gz?' 符頭'+pan.meta.fu_tou_gz:'')+' · '+(pan.meta.method||'')+'</span>':'')+'</div>';}
  function parseYMD(s){var a=s.split('-');return{y:+a[0],m:+a[1],d:+a[2]};}
  function runPure(){
    var ds=document.getElementById('drawDate').value;if(!ds){alert('請選攪珠日');return;}
    var p=parseYMD(ds),bz=E.pureBazi(p.y,p.m,p.d),qm=E.pureQimen(p.y,p.m,p.d);
    document.getElementById('methodBox').textContent='【純八字】\n起盤：'+bz.method.anchor+'\n權重：'+bz.method.weights+'\n收碼：'+bz.method.pick+
      '\n\n【純奇門】\n定局：'+qm.method.dingju+'\n取數：'+qm.method.extract+'\n收碼：'+qm.method.pick;
    document.getElementById('predBox').innerHTML='<div style="margin-bottom:12px">'+pillarsHTML(bz.pillars,'八字盤')+ballsHTML(bz.numbers)+'<span class="m6-note">純八字 15 碼</span></div><div>'+panHTML(qm.pan,'奇門盤')+ballsHTML(qm.numbers)+'<span class="m6-note">純奇門 15 碼</span></div>';
    var row=byDate[ds];
    if(!row){document.getElementById('cmpBox').innerHTML='<span class="m6-note">此日暫無官方結果。</span>';return;}
    var nums=row.numbers.slice(0,6),sp=row.special!=null?row.special:(row.numbers[6]||null);
    var sb=E.scorePred(bz.numbers,nums,sp),sq=E.scorePred(qm.numbers,nums,sp);
    document.getElementById('cmpBox').innerHTML='<div>官方：'+ballsHTML(nums.concat(sp?[sp]:[]),[],sp)+'</div>'+
      '<div class="m6-score '+(sb.score>=5?'hi':'')+'">八字 '+sb.score+' 字</div>'+ballsHTML(bz.numbers,sb.hit_zheng.concat(sb.hit_special&&sp?[sp]:[]),sp)+
      '<div class="m6-score '+(sq.score>=5?'hi':'')+'">奇門 '+sq.score+' 字</div>'+ballsHTML(qm.numbers,sq.hit_zheng.concat(sq.hit_special&&sp?[sp]:[]),sp);
  }
  function runHybrid(){
    var ds=document.getElementById('drawDate').value,pdt=document.getElementById('personalDT').value;
    if(!ds||!pdt){alert('請填攪珠日與個人出生時間');return;}
    var d=parseYMD(ds),m=pdt.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2})/);
    if(!m){alert('個人時間格式唔啱');return;}
    var py=+m[1],pm=+m[2],pd=+m[3],ph=+m[4];
    var pb=E.personalBazi(py,pm,pd,ph,d.y,d.m,d.d),pq=E.personalQimen(py,pm,pd,ph,d.y,d.m,d.d);
    document.getElementById('natalBox').innerHTML=pillarsHTML(pb.personal_pillars,'個人八字')+pillarsHTML(pb.draw_pillars,'攪珠日八字')+
      '<hr style="border:0;border-top:1px solid var(--rule);margin:10px 0">'+panHTML(pq.personal,'個人奇門（出生時）')+panHTML(pq.draw,'攪珠日奇門');
    var row=byDate[ds],nums=row?row.numbers.slice(0,6):[],sp=row?(row.special!=null?row.special:row.numbers[6]):null;
    var sb=row?E.scorePred(pb.numbers,nums,sp):null,sq=row?E.scorePred(pq.numbers,nums,sp):null;
    document.getElementById('hybridBox').innerHTML='<div><b>八字混合 15</b>'+(sb?' · <span class="m6-score">'+sb.score+' 字</span>':'')+'</div>'+ballsHTML(pb.numbers,sb?sb.hit_zheng:[],sp)+
      '<div style="margin-top:10px"><b>奇門混合 15</b>'+(sq?' · <span class="m6-score">'+sq.score+' 字</span>':'')+'</div>'+ballsHTML(pq.numbers,sq?sq.hit_zheng:[],sp);
  }
  function runBacktest(){
    if(!HISTORY.length){alert('歷史未載入');return;}
    document.getElementById('status').textContent='回測計算中…';
    var slice=HISTORY.slice(-100),sumB=0,sumQ=0,eq5B=0,eq5Q=0,maxB=0,maxQ=0;
    var tbody=document.querySelector('#btTable tbody');tbody.innerHTML='';
    var i=0;
    function step(){
      for(var k=0;k<8&&i<slice.length;k++,i++){
        var row=slice[i],p=parseYMD(row.date),nums=row.numbers.slice(0,6),sp=row.special!=null?row.special:row.numbers[6];
        var bz=E.pureBazi(p.y,p.m,p.d),qm=E.pureQimen(p.y,p.m,p.d);
        var sb=E.scorePred(bz.numbers,nums,sp),sq=E.scorePred(qm.numbers,nums,sp);
        sumB+=sb.score;sumQ+=sq.score;if(sb.score>=5)eq5B++;if(sq.score>=5)eq5Q++;
        if(sb.score>maxB)maxB=sb.score;if(sq.score>maxQ)maxQ=sq.score;
        var tr=document.createElement('tr');tr.innerHTML='<td>'+row.date+'</td><td class="m6-score">'+sb.score+'</td><td class="m6-score">'+sq.score+'</td><td>'+nums.join(',')+'+'+sp+'</td>';tbody.appendChild(tr);
      }
      if(i<slice.length){document.getElementById('status').textContent='回測 '+i+'/'+slice.length;setTimeout(step,0);}
      else{var n=slice.length;document.getElementById('btStats').innerHTML='<div class="m6-statgrid">'+
        '<div class="m6-statbox"><div class="k">純八字平均</div><div class="v">'+(sumB/n).toFixed(3)+'</div></div>'+
        '<div class="m6-statbox"><div class="k">純奇門平均</div><div class="v">'+(sumQ/n).toFixed(3)+'</div></div>'+
        '<div class="m6-statbox"><div class="k">八字≥5</div><div class="v">'+eq5B+'</div></div>'+
        '<div class="m6-statbox"><div class="k">奇門≥5</div><div class="v">'+eq5Q+'</div></div></div>';
        document.getElementById('status').textContent='回測完成 n='+n;}
    }
    step();
  }
  document.querySelectorAll('#modeTabs button').forEach(function(b){
    b.onclick=function(){
      mode=b.getAttribute('data-mode');
      document.querySelectorAll('#modeTabs button').forEach(function(x){x.classList.toggle('active',x===b);});
      document.getElementById('panelPure').classList.toggle('hidden',mode!=='pure');
      document.getElementById('panelHybrid').classList.toggle('hidden',mode!=='hybrid');
      document.getElementById('panelBT').classList.toggle('hidden',mode!=='backtest');
    };
  });
  document.getElementById('runBtn').onclick=function(){
    try{if(!E)throw new Error('引擎未載入');if(mode==='pure')runPure();else if(mode==='hybrid')runHybrid();else runBacktest();}
    catch(e){document.getElementById('status').innerHTML='<span style="color:var(--red)">'+e.message+'</span>';console.error(e);}
  };
  document.getElementById('loadLatest').onclick=function(){
    fetch(LATEST_URL).then(function(r){return r.json();}).then(function(d){
      if(d&&d.date)document.getElementById('drawDate').value=d.date.slice(0,10);
      document.getElementById('status').textContent='已載入最近一期 '+((d&&d.draw)||'');
    }).catch(function(){document.getElementById('status').textContent='載入 latest 失敗';});
  };
  function setupControls(){
    buildSeg('m6-periods',[{v:'10',label:'近10期'},{v:'50',label:'近50期'},{v:'100',label:'近100期'},{v:'500',label:'近500期'},{v:'ytd',label:'今年至今'}],function(){return PERIOD;},function(v){PERIOD=v;renderStats();});
    buildSeg('m6-sort',[{v:'num',label:'號碼'},{v:'hot',label:'最熱'},{v:'due',label:'最冷'}],function(){return SORT;},function(v){SORT=v;renderStats();});
  }
  function boot(){
    setupControls();
    Promise.all([
      fetch(LATEST_URL).then(function(r){if(!r.ok)throw 0;return r.json();}).catch(function(){return null;}),
      fetch(HISTORY_URL).then(function(r){if(!r.ok)throw 0;return r.json();}).catch(function(){return null;})
    ]).then(function(res){
      LATEST=res[0];HISTORY=(res[1]||[]).slice().sort(function(a,b){return a.date<b.date?-1:a.date>b.date?1:0;});
      HISTORY.forEach(function(row){byDate[row.date]=row;});
      LATEST_YEAR=HISTORY.length?HISTORY[HISTORY.length-1].date.slice(0,4):String(new Date().getUTCFullYear());
      renderResult();
      if(HISTORY.length){renderStats();document.getElementById('drawDate').value=HISTORY[HISTORY.length-1].date;}
      else document.getElementById('m6-numgrid').innerHTML='<div class="m6-state err">未能載入歷史。</div>';
      document.getElementById('status').textContent='歷史 '+HISTORY.length+' 期已載入';
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();

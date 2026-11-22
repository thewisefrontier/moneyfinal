"""운세 섹션 한국어 페이지 생성기 — ipo.html의 공용 head(사이트 기본 스타일)에 fortune.css를 붙이고, 페이지별 본문 템플릿을 넣는다.
실행: python scripts/gen_fortune.py  → fortune.html 등. 영어판은 build_en.py가 이 한국어 페이지에서 만든다."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://moneyfinal.pages.dev'


def head(page, title, desc):
    src = open(os.path.join(ROOT, 'ipo.html'), encoding='utf-8').read()
    h = src[:src.index('</head>')]
    h = re.sub(r'<link rel="alternate"[^>]*>\n?', '', h)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', h)
    h = h.replace(f'{SITE}/ipo', f'{SITE}/{page}')
    h = re.sub(r'(og:title|twitter:title)" content="[^"]*"', r'\1" content="' + title + ' | 머니파이널"', h)
    h = re.sub(r'(og:description|twitter:description)" content="[^"]*"', r'\1" content="' + desc + '"', h)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>',
               '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"%s","description":"%s","url":"%s/%s","inLanguage":"ko"}</script>'
               % (title, desc, SITE, page), h, flags=re.S)
    h = re.sub(r'<title>[^<]*</title>', f'<title>{title} | 머니파이널</title>', h)
    return h + '<link rel="stylesheet" href="fortune.css">\n</head>'


def shell(page, active, main, scripts=''):
    return f'''
<body class="fz-page">
<div class="ticker"><div class="ticker-inner" id="ticker-inner"></div></div>
<header><a href="index.html" class="logo">💰 머니파이널</a>
  <nav id="site-nav" data-active="{active}"></nav>
<script src="nav.js"></script>
  <div style="display:flex;gap:6px"><button class="theme-btn" onclick="toggleTheme()">🌙</button><button class="menu-btn" onclick="toggleNav()">☰</button></div></header>
<main class="fz-wrap">
{main}
</main>
<footer>© 2026 머니파이널 · 세상의 모든 재테크<br><a href="about.html">사이트 소개</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a></footer>
<script src="theme.js"></script>{scripts}<script src="ticker.js"></script>
<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "5ec3e89757844a3582c90d3524a2cead"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
'''


NOTE = '<p class="fz-note">⚠️ 운세 결과는 오락과 참고를 위한 것이며 특정 결과를 보장하지 않습니다. 중요한 결정의 근거로 삼지 마세요. 입력한 정보는 서버로 전송되지 않고 이 기기의 브라우저에서만 계산됩니다.</p>'

HUB = '''
<section class="fz-hero">
  <img src="assets/fortune/hero-room.webp" alt="등불이 켜진 조선시대 운세방에서 점괘를 살피는 젊은 역술인" width="1344" height="768" fetchpriority="high">
  <div class="fz-hero-body">
    <div class="fz-kicker">朝鮮 · 運勢房</div>
    <h1 class="fz-title">조선 역술인의 운세방</h1>
    <p class="fz-sub">저녁 등불 아래, 젊은 역술인이 오늘의 기운을 살펴 점괘를 써 드립니다. 띠별 운세, 사주, 타로를 무료로 보세요.</p>
    <a class="fz-btn" href="fortune-zodiac.html">오늘의 점괘 보기</a>
  </div>
</section>

<section class="fz-section">
  <h2 class="fz-h2">역술인의 한마디</h2>
  <div class="fz-diviner">
    <div class="fz-diviner-img"><img src="assets/fortune/diviner.webp" alt="산통을 든 젊은 역술인" width="640" height="640" loading="lazy"></div>
    <p class="fz-say">어서 오십시오, 길손이시여. 이곳은 별과 절기가 만나는 작은 운세방입니다. 오늘 하루의 기운이 궁금하시다면 아래에서 도구를 하나 골라 주십시오. 제가 두루마리에 점괘를 적어 드리겠습니다.<small>— 운세방 주인</small></p>
  </div>
</section>

<section class="fz-section">
  <h2 class="fz-h2">오늘의 도구</h2>
  <div class="fz-grid">
    <a class="fz-tool" href="fortune-zodiac.html">
      <div class="fz-tool-img"><img src="assets/fortune/tool-zodiac.webp" alt="열두 동물이 그려진 병풍" width="640" height="640" loading="lazy"></div>
      <div class="fz-tool-body"><div class="fz-tool-name">띠별 운세</div><div class="fz-tool-desc">병풍 속 열두 띠 중 내 띠를 고르면 오늘·이번 주·이번 달·올해의 운세를 바로 봅니다.</div></div>
    </a>
    <a class="fz-tool" href="fortune-saju.html">
      <div class="fz-tool-img"><img src="assets/fortune/tool-saju.webp" alt="붓과 두루마리가 놓인 낮은 책상" width="640" height="640" loading="lazy"></div>
      <div class="fz-tool-body"><div class="fz-tool-name">사주팔자</div><div class="fz-tool-desc">태어난 해·달·날·시로 네 기둥을 세워 타고난 기질과 오행의 균형을 풀어 드립니다.</div></div>
    </a>
    <a class="fz-tool" href="fortune-tarot.html">
      <div class="fz-tool-img"><img src="assets/fortune/tool-tarot.webp" alt="촛불 아래 펼쳐진 점괘 카드" width="640" height="640" loading="lazy"></div>
      <div class="fz-tool-body"><div class="fz-tool-name">타로 한 장</div><div class="fz-tool-desc">마음속 질문을 정하고 카드 한 장을 뽑아 오늘의 메시지를 확인합니다.</div></div>
    </a>
  </div>
</section>
''' + NOTE

ZODIAC = '''
<div class="fz-head"><span class="fz-seal">運</span><div><h1>띠별 운세</h1><p>병풍 속 열두 띠 중에서 내 띠를 고르세요. 오늘·이번 주·이번 달·올해의 점괘를 적어 드립니다.</p></div></div>
<div class="fz-signs" id="signs"></div>
<div class="fz-tabs" id="tabs"></div>
<div id="result" aria-live="polite"></div>
<div class="fz-share"><a class="fz-btn ghost" href="fortune.html">운세방으로 돌아가기</a><a class="fz-btn ghost" href="fortune-saju.html">사주도 보기</a></div>
''' + NOTE

ZODIAC_JS = '''<script src="fortune.bundle.js"></script><script src="fortune-lucky.js"></script><script>
const F=window.Fortune,$=id=>document.getElementById(id);
const FZ=window.FZ,EN=!!FZ,T=EN?FZ.T:(x=>x);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PERIODS=[['today','오늘'],['week','이번 주'],['month','이번 달'],['year','올해']];
const CATS=[['general','총운'],['love','애정운'],['money','금전운'],['health','건강운']];
const store={get(k){try{return localStorage.getItem(k)}catch(e){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
const q=new URLSearchParams(location.search);
let sign=(F.ZODIAC_SIGNS.some(z=>z.key===q.get('s'))&&q.get('s'))||store.get('fz_sign')||'rat';
if(!F.ZODIAC_SIGNS.some(z=>z.key===sign))sign='rat';
let per=PERIODS.some(p=>p[0]===q.get('p'))?q.get('p'):'today';
const ZN=z=>EN?FZ.data.zodiac[z.label]:z.label;
const stars=s=>{const n=Math.max(1,Math.min(5,Math.round((s-45)/10)));return '<span class="fz-stars" aria-label="5점 만점에 '+n+'점">'+'★'.repeat(n)+'<i>'+'★'.repeat(5-n)+'</i></span>';};
function drawSigns(){
  $('signs').innerHTML=F.ZODIAC_SIGNS.map(z=>`<button type="button" class="fz-sign" data-k="${z.key}" aria-pressed="${z.key===sign}"><span class="e">${z.emoji}</span><span class="n">${esc(ZN(z))}</span><span class="y">${EN?esc(z.years.split('·').slice(0,2).join(', ')):esc(z.years.split('·')[0])+'년생 외'}</span></button>`).join('');
  $('tabs').innerHTML=PERIODS.map(p=>`<button type="button" class="fz-tab" data-p="${p[0]}" aria-pressed="${p[0]===per}">${p[1]}</button>`).join('');
}
function draw(){
  const z=F.ZODIAC_SIGNS.find(x=>x.key===sign),pl=PERIODS.find(p=>p[0]===per)[1];
  const d=per==='today'?F.getDailyFortune(sign):F.getPeriodFortune(per,sign);
  const when=per==='today'?d.date+' (한국 시간 기준)':T(d.rangeLabel);
  const lucky=per==='today'
    ?`<span class="fz-chip"><b>행운의 색</b>${esc(T(d.luckyColor))}</span><span class="fz-chip"><b>행운의 숫자</b>${d.luckyNumber}</span><span class="fz-chip"><b>행운의 시간</b>${esc(T(d.luckyTime))}</span>`
    :`<span class="fz-chip"><b>행운의 색</b>${esc(T(d.luckyColor))}</span><span class="fz-chip"><b>행운의 숫자</b>${d.luckyNumber}</span><span class="fz-chip"><b>${esc(T(d.luckyExtra.label))}</b>${esc(T(d.luckyExtra.value))}</span>`;
  const tl=per==='today'||!d.timeline?'':`<div class="fz-cat"><div class="fz-cat-h"><b>흐름</b></div><div class="fz-tl">${d.timeline.map((t,i)=>`<div class="${i===d.bestIndex?'best':''}"><span style="height:${Math.max(8,Math.round((t.score-40)*1.4))}px"></span>${esc(T(t.label))}</div>`).join('')}</div></div>`;
  $('result').innerHTML=`<article class="fz-scroll"><div class="fz-scroll-top"><span class="fz-seal">${z.emoji}</span><div><h2>${EN?'Year of the '+esc(ZN(z))+' · '+pl:esc(z.label)+' · '+pl+'의 점괘'}</h2><div class="d">${esc(when)}</div></div></div>
  <p class="fz-say-line">${EN?'Born under the '+esc(ZN(z))+', I see. I have read the stars and the seasons and written down your fortune for '+pl.toLowerCase()+'.':esc(z.label)+'이시군요. 별과 절기를 살펴 '+pl+'의 기운을 적었습니다.'}</p>
  ${CATS.map(c=>`<div class="fz-cat"><div class="fz-cat-h"><b>${c[1]}</b>${stars(d[c[0]].score)}</div><p>${esc(T(d[c[0]].text))}</p><div class="fz-advice" data-l="역술인의 한마디">${esc(T(d[c[0]].advice))}</div></div>`).join('')}
  ${tl}<div class="fz-lucky">${lucky}</div><div id="lucky"></div></article>`;
  if(window.FZ_luckyMount)FZ_luckyMount($('lucky'),d.luckyItem);
}
document.addEventListener('click',e=>{
  const s=e.target.closest('.fz-sign'),t=e.target.closest('.fz-tab');
  if(s){sign=s.dataset.k;store.set('fz_sign',sign);}else if(t){per=t.dataset.p;}else return;
  drawSigns();draw();history.replaceState(null,'','?s='+sign+'&p='+per);
});
drawSigns();draw();
</script>'''

SAJU = '''
<div class="fz-head"><span class="fz-seal">命</span><div><h1>사주팔자</h1><p>태어난 해·달·날·시로 네 기둥을 세워 타고난 기질과 오행의 균형을 풀어 드립니다.</p></div></div>
<form class="fz-card" id="f" novalidate>
  <div class="fz-form">
    <label>달력<select id="cal"><option value="0">양력</option><option value="1">음력</option></select></label>
    <label class="fz-leap" id="leapw" hidden><input type="checkbox" id="leap"> 윤달</label>
    <label>태어난 해<input id="y" type="number" inputmode="numeric" min="1900" max="2100" placeholder="1990" required></label>
    <label>월<select id="m"></select></label>
    <label>일<select id="d"></select></label>
    <label>태어난 시각<select id="hh"></select></label>
    <label>분<input id="mm" type="number" inputmode="numeric" min="0" max="59" value="0"></label>
    <fieldset><legend>성별</legend><label><input type="radio" name="g" value="male" checked> 남</label> <label><input type="radio" name="g" value="female"> 여</label></fieldset>
  </div>
  <p class="fz-err" id="err" role="alert" hidden></p>
  <button class="fz-btn" type="submit">사주 보기</button> <button class="fz-btn ghost" type="button" id="clr">저장된 입력 지우기</button>
</form>
<div id="result" aria-live="polite"></div>
<div class="fz-share"><a class="fz-btn ghost" href="fortune.html">운세방으로 돌아가기</a><a class="fz-btn ghost" href="fortune-zodiac.html">띠별 운세 보기</a></div>
''' + NOTE

SAJU_JS = '''<script src="fortune.bundle.js"></script><script src="fortune-lucky.js"></script><script>
const F=window.Fortune,$=id=>document.getElementById(id);
const FZ=window.FZ,EN=!!FZ,T=EN?FZ.T:(x=>x);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const store={get(k){try{return localStorage.getItem(k)}catch(e){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(e){}},del(k){try{localStorage.removeItem(k)}catch(e){}}};
const ZD=EN?FZ.data:null;
const L={stem:s=>EN?ZD.stems[s][0]:s,br:b=>EN?ZD.branches[b][0]:b,el:k=>EN?ZD.elements[k]:k,tg:x=>EN?(ZD.tenGods[x]||x):x,pair:p=>EN&&p&&p.length===2?ZD.stems[p[0]][0]+'-'+ZD.branches[p[1]][0]:p};
const EL={'목':['木','#5aa86a'],'화':['火','#e0584f'],'토':['土','#c49a45'],'금':['金','#a5aab8'],'수':['水','#5b8fd9']};
$('m').innerHTML=Array.from({length:12},(_,i)=>`<option value="${i+1}">${i+1}월</option>`).join('');
$('d').innerHTML=Array.from({length:31},(_,i)=>`<option value="${i+1}">${i+1}일</option>`).join('');
$('hh').innerHTML='<option value="">모름</option>'+Array.from({length:24},(_,i)=>`<option value="${i}">${i}시</option>`).join('');
$('cal').addEventListener('change',()=>{$('leapw').hidden=$('cal').value!=='1';});
function err(t){const e=$('err');e.textContent=t;e.hidden=!t;}
function read(){
  const y=+$('y').value,m=+$('m').value,d=+$('d').value,lunar=$('cal').value==='1',hh=$('hh').value,mi=+$('mm').value||0;
  if(!Number.isInteger(y)||y<1900||y>2100)return {e:'태어난 해는 1900년부터 2100년 사이로 입력해 주세요.'};
  if(mi<0||mi>59)return {e:'분은 0부터 59 사이로 입력해 주세요.'};
  if(!lunar){const t=new Date(y,m-1,d);if(t.getFullYear()!==y||t.getMonth()!==m-1||t.getDate()!==d)return {e:'존재하지 않는 날짜입니다. 월과 일을 다시 확인해 주세요.'};}
  else if(d>30)return {e:'음력은 한 달이 30일까지입니다.'};
  return {in:{year:y,month:m,day:d,hour:hh===''?null:+hh,minute:mi,isLunar:lunar,isLeapMonth:lunar&&$('leap').checked,gender:document.querySelector('input[name=g]:checked').value},hasHour:hh!==''};
}
function pillar(p,tg,label){
  if(!p)return `<div class="fz-pil dim"><div class="l">${label}</div><div class="tg">—</div><div class="ch">—</div><div class="ch">—</div><div class="tg">—</div></div>`;
  const se=F.stemElement(p.stem),be=F.branchElement(p.branch);
  return `<div class="fz-pil"><div class="l">${label}</div><div class="tg">${esc(L.tg(tg.stem))}</div>
  <div class="ch" style="color:${EL[se][1]}">${F.stemHanja(p.stem)}<small>${EN?esc(L.stem(p.stem))+' · '+esc(L.el(se)):esc(p.stem)+'·'+EL[se][0]}</small></div>
  <div class="ch" style="color:${EL[be][1]}">${F.branchHanja(p.branch)}<small>${EN?esc(L.br(p.branch))+' · '+esc(ZD.branches[p.branch][1]):esc(p.branch)+'·'+EL[be][0]}</small></div><div class="tg">${esc(L.tg(tg.branch))}</div></div>`;
}
function show(r,hasHour){
  const it=F.interpretSaju(r),nick=F.DAY_MASTER_NICKNAME[r.dayPillar.stem]||{name:'',emoji:'🔮'};
  const tg=r.tenGods,max=Math.max(1,...Object.values(r.elementCounts));
  const els=Object.keys(EL).map(k=>`<div class="fz-el"><span>${EL[k][0]} ${esc(L.el(k))}</span><i><b style="width:${Math.round(r.elementCounts[k]/max*100)}%;background:${EL[k][1]}"></b></i><em>${r.elementCounts[k]}</em></div>`).join('');
  const luck=r.luckPillars?`<div class="fz-cat"><div class="fz-cat-h"><b>대운 흐름</b><span class="fz-chip"><b>시작</b>${r.luckPillars.startAge}${EN?'':'세'}</span></div><div class="fz-lucky">${r.luckPillars.pillars.slice(0,8).map(x=>`<span class="fz-chip"><b>${x.age}${EN?'':'세'}</b>${esc(L.pair(x.korean))}</span>`).join('')}</div></div>`:'';
  $('result').innerHTML=`<article class="fz-scroll"><div class="fz-scroll-top"><span class="fz-seal">${nick.emoji}</span><div><h2>${EN?'Your Saju · '+esc(L.stem(r.dayPillar.stem))+'-'+esc(L.br(r.dayPillar.branch))+' Day Pillar':'나의 사주 · '+esc(r.dayPillar.stem)+esc(r.dayPillar.branch)+'일주'}</h2><div class="d">${EN?'Your Day Master is '+esc(L.stem(r.dayPillar.stem))+' ('+esc(ZD.stems[r.dayPillar.stem][2])+' '+esc(L.el(F.stemElement(r.dayPillar.stem)))+'), like '+esc(T(nick.name))+'.':'일간은 '+esc(r.dayPillar.stem)+', 자연물로는 '+esc(nick.name)+'에 해당합니다'}</div></div></div>
  <p class="fz-say-line">태어난 날의 기운을 네 기둥으로 세워 보았습니다.${hasHour?'':' 태어난 시각을 모르시니 시주 없이 세 기둥으로 풀었습니다.'}</p>
  <div class="fz-pils">${pillar(r.hourPillar,tg.hour,'시주')}${pillar(r.dayPillar,tg.day,'일주')}${pillar(r.monthPillar,tg.month,'월주')}${pillar(r.yearPillar,tg.year,'년주')}</div>
  <div class="fz-cat"><div class="fz-cat-h"><b>타고난 기질</b></div><p>${esc(T(it.dayMasterText))}</p></div>
  <div class="fz-cat"><div class="fz-cat-h"><b>오행의 균형</b></div><div class="fz-els">${els}</div><p>${esc(T(it.elementSummaryText))}</p><div class="fz-lucky"><span class="fz-chip"><b>보완하는 색</b>${esc(T(it.luckyColor))}</span></div></div>
  ${luck}<div id="lucky"></div></article>`;
  if(window.FZ_luckyMount)FZ_luckyMount($('lucky'),it.luckyItem);
  $('result').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
}
$('f').addEventListener('submit',e=>{
  e.preventDefault();err('');
  const v=read();if(v.e){err(v.e);return;}
  try{const r=F.calculateSaju(v.in);store.set('fz_saju',JSON.stringify(v.in));show(r,v.hasHour);}
  catch(x){err('이 날짜로는 계산하지 못했습니다. 달력(양력·음력)과 윤달 선택을 다시 확인해 주세요.');}
});
$('clr').addEventListener('click',()=>{store.del('fz_saju');$('f').reset();$('leapw').hidden=true;$('result').innerHTML='';err('');});
try{const s=JSON.parse(store.get('fz_saju')||'null');if(s){$('cal').value=s.isLunar?'1':'0';$('leapw').hidden=!s.isLunar;$('leap').checked=!!s.isLeapMonth;$('y').value=s.year;$('m').value=s.month;$('d').value=s.day;$('hh').value=s.hour==null?'':s.hour;$('mm').value=s.minute||0;document.querySelector('input[name=g][value='+s.gender+']').checked=true;}}catch(e){}
</script>'''

TAROT = '''
<div class="fz-head"><span class="fz-seal">卦</span><div><h1>타로 한 장</h1><p>마음속 질문을 정하고, 카드 뒷면을 눌러 한 장을 뽑으세요. 카드는 매번 무작위로 뽑힙니다.</p></div></div>
<div class="fz-cats" id="cats" role="group" aria-label="질문 분야"></div>
<div class="fz-deck">
  <button type="button" class="fz-card3d" id="card" aria-label="카드 뒷면, 눌러서 한 장 뽑기">
    <span class="in"><span class="fz-face fz-back"><span class="tg"></span></span><span class="fz-face fz-front" id="front"></span></span>
  </button>
  <div class="fz-tarot-hint" id="hint">카드를 눌러 뽑아 보세요</div>
</div>
<div id="result" aria-live="polite"></div>
<div class="fz-share"><button class="fz-btn ghost" type="button" id="again" hidden>다시 뽑기</button><a class="fz-btn ghost" href="fortune.html">운세방으로 돌아가기</a><a class="fz-btn ghost" href="fortune-zodiac.html">띠별 운세 보기</a></div>
''' + NOTE

TAROT_JS = '''<script src="fortune.bundle.js"></script><script>
const F=window.Fortune,$=id=>document.getElementById(id);
const FZ=window.FZ,EN=!!FZ,T=EN?FZ.T:(x=>x);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const CATS=[['general','총운','✨'],['love','연애운','💕'],['career','직장운','💼'],['money','재물운','💰']];
const store={get(k){try{return localStorage.getItem(k)}catch(e){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
let cat=CATS.some(c=>c[0]===store.get('fz_tarot_cat'))?store.get('fz_tarot_cat'):'general',busy=false,drawn=false;
const calm=matchMedia('(prefers-reduced-motion: reduce)').matches;
function drawCats(){$('cats').innerHTML=CATS.map(c=>`<button type="button" class="fz-tab" data-c="${c[0]}" aria-pressed="${c[0]===cat}">${c[2]} ${c[1]}</button>`).join('');}
function reset(){drawn=false;$('card').classList.remove('flipped');$('result').innerHTML='';$('again').hidden=true;$('hint').textContent='카드를 눌러 뽑아 보세요';}
function pull(){
  if(busy)return;busy=true;
  if(drawn){reset();busy=false;return;}
  const d=F.drawTarotCard(),img='/assets/fortune/'+d.card.image.replace(/^\\/?/,'');
  $('front').className='fz-face fz-front'+(d.reversed?' rev':'');
  $('front').innerHTML=`<img src="${esc(img)}" alt="${esc(T(d.card.name))} 카드" onerror="this.remove()">`;
  $('card').classList.add('flipped');drawn=true;$('hint').textContent='';
  const lbl=CATS.find(c=>c[0]===cat)[1],txt=d.reversed?d.card.reversed:d.card.upright;
  const show=()=>{$('result').innerHTML=`<article class="fz-scroll fz-meaning"><div class="fz-scroll-top"><span class="fz-seal">${d.card.emoji}</span><div><h3>${esc(T(d.card.name))}</h3><span class="dir">${d.reversed?'역방향':'정방향'}</span></div></div>
  <div class="fz-cat"><div class="fz-cat-h"><b>카드의 뜻</b></div><p>${esc(T(txt))}</p></div>
  <div class="fz-cat"><div class="fz-cat-h"><b>${EN?(lbl==='Overall'?'In general':'In terms of '+lbl.toLowerCase()):lbl+'으로 읽으면'}</b></div><p>${esc(T(F.getCategoryPoint(d.card,d.reversed,cat)))}</p></div></article>`;$('again').hidden=false;busy=false;};
  calm?show():setTimeout(show,650);
}
document.addEventListener('click',e=>{const t=e.target.closest('.fz-tab');if(t){cat=t.dataset.c;store.set('fz_tarot_cat',cat);drawCats();if(drawn)reset();}});
$('card').addEventListener('click',pull);$('again').addEventListener('click',()=>{reset();});
drawCats();
</script>'''

INFO_ZODIAC = '''
<section class="fz-info">
<h2>열두 띠는 어떻게 정해지나요?</h2>
<p>띠는 태어난 해의 지지(地支)로 정해집니다. 지지는 자·축·인·묘·진·사·오·미·신·유·술·해 열두 글자이고, 각각 쥐·소·호랑이·토끼·용·뱀·말·양·원숭이·닭·개·돼지에 짝지어 12년마다 한 바퀴를 돕니다.</p>
<table><tr><th>쥐</th><th>소</th><th>호랑이</th><th>토끼</th><th>용</th><th>뱀</th></tr><tr><td>1996·2008</td><td>1997·2009</td><td>1998·2010</td><td>1999·2011</td><td>2000·2012</td><td>2001·2013</td></tr>
<tr><th>말</th><th>양</th><th>원숭이</th><th>닭</th><th>개</th><th>돼지</th></tr><tr><td>1990·2002</td><td>1991·2003</td><td>1992·2004</td><td>1993·2005</td><td>1994·2006</td><td>1995·2007</td></tr></table>
<p>1월이나 2월 초에 태어났다면 띠가 헷갈릴 수 있습니다. 일반적으로는 음력 설을 기준으로 하지만, 사주에서는 입춘(양력 2월 4일 무렵)에 해가 바뀐다고 봅니다. 두 기준이 다른 해에는 두 띠를 모두 살펴보셔도 좋습니다.</p>
<h2>자주 묻는 질문</h2>
<details><summary>같은 띠면 모두 같은 운세인가요?</summary><p>이 화면의 띠별 운세는 띠만 기준으로 한 가벼운 점괘라 같은 띠는 같은 결과를 봅니다. 내 생년월일시에 맞춘 풀이를 원하시면 사주팔자를 보세요.</p></details>
<details><summary>오늘 운세는 언제 바뀌나요?</summary><p>한국 시간 자정에 새 점괘로 바뀝니다. 같은 날에는 몇 번을 열어도 같은 결과가 나옵니다.</p></details>
<details><summary>이번 주·이번 달·올해는 어떻게 다른가요?</summary><p>기간이 길수록 하루하루의 기복보다 큰 흐름을 담습니다. 주·월 점괘에는 기간 안에서 가장 좋은 날이나 시기를 막대 그래프로 보여 드립니다.</p></details>
</section>
'''

INFO_SAJU = '''
<section class="fz-info">
<h2>사주팔자란?</h2>
<p>사주(四柱)는 태어난 연·월·일·시 네 개의 기둥이고, 각 기둥을 천간 한 글자와 지지 한 글자로 적기 때문에 모두 여덟 글자(팔자, 八字)가 됩니다. 천간은 갑·을·병·정·무·기·경·신·임·계 열 글자, 지지는 자·축·인·묘·진·사·오·미·신·유·술·해 열두 글자입니다.</p>
<h2>일간과 오행</h2>
<p>네 기둥 가운데 태어난 날의 천간을 일간(日干)이라 하며, 사주에서 '나'를 상징합니다. 모든 글자는 나무(木)·불(火)·흙(土)·쇠(金)·물(水)의 오행에 속하고, 여덟 글자에 오행이 얼마나 고르게 퍼져 있는지가 타고난 기질과 보완할 점을 읽는 단서가 됩니다.</p>
<h2>이 풀이는 어디까지 보나요?</h2>
<p>이 화면은 일간(성격 경향)과 오행 분포, 대운의 시작 나이처럼 만세력으로 기계적으로 계산되는 범위만 풀이합니다. 전문 명리학의 격국·용신 판단까지는 다루지 않으니 재미와 참고로 보시고, 중요한 결정의 근거로 삼지는 마세요.</p>
<h2>자주 묻는 질문</h2>
<details><summary>태어난 시각을 모르면 어떻게 하나요?</summary><p>시각 칸을 '모름'으로 두면 시주 없이 연·월·일 세 기둥으로 풀이합니다. 시주가 빠지므로 풀이 범위가 조금 줄어듭니다.</p></details>
<details><summary>양력과 음력 중 무엇으로 넣어야 하나요?</summary><p>아는 쪽으로 넣으시면 됩니다. 음력으로 넣을 때 그 달이 윤달이었다면 '윤달'을 체크하세요. 만세력이 양력과 음력을 서로 바꿔 계산합니다.</p></details>
<details><summary>입력한 정보는 저장되나요?</summary><p>서버로 전송되지 않고 이 기기의 브라우저에서만 계산됩니다. 다음에 다시 입력하지 않도록 이 기기에만 저장해 두며, '저장된 입력 지우기'로 언제든 지울 수 있습니다.</p></details>
</section>
'''

INFO_TAROT = '''
<section class="fz-info">
<h2>타로 카드, 이렇게 읽으세요</h2>
<p>여기서는 타로의 큰 줄기인 메이저 아르카나 22장을 씁니다. 바보(0번)에서 세계(21번)까지 인생의 큰 흐름을 담은 카드들이고, 카드가 바로 서 있으면 정방향, 거꾸로 서 있으면 역방향으로 읽습니다. 역방향은 나쁜 뜻이 아니라 같은 주제가 막혀 있거나 안으로 향해 있다는 신호로 보시면 됩니다.</p>
<p>질문은 '이번 달 직장에서 내가 기억할 점은?'처럼 열린 질문이 좋습니다. 같은 질문으로 계속 다시 뽑기보다 첫 카드를 곱씹어 보세요.</p>
<h2>카드 그림은 어디서 왔나요?</h2>
<p>카드 앞면은 1909년 파멜라 콜먼 스미스가 그린 라이더-웨이트-스미스 덱으로, 저작권이 만료된 퍼블릭 도메인 작품입니다.</p>
<h2>자주 묻는 질문</h2>
<details><summary>카드는 정말 무작위인가요?</summary><p>브라우저의 난수로 22장 중에서 한 장, 정·역방향을 각각 절반 확률로 고릅니다. 서버가 결과를 정하지 않습니다.</p></details>
<details><summary>분야를 바꾸면 카드도 바뀌나요?</summary><p>분야를 바꾸면 카드를 다시 뽑아야 하고, 같은 카드라도 분야에 따라 읽어 주는 말이 달라집니다.</p></details>
</section>
'''

INFO_HUB = '''
<section class="fz-info">
<h2>운세방은 이렇게 쓰세요</h2>
<p>띠만 고르면 바로 보는 가벼운 점괘는 띠별 운세, 생년월일시로 타고난 기질을 풀어 보고 싶다면 사주팔자, 지금 마음속 질문에 한 장으로 답을 얻고 싶다면 타로를 추천합니다. 결과는 오락과 참고를 위한 것이며, 입력한 정보는 서버로 보내지 않고 이 기기의 브라우저에서만 계산됩니다.</p>
</section>
'''

PAGES = {
    'fortune-tarot.html': dict(title='타로 한 장', desc='질문 분야를 고르고 카드 한 장을 뽑아 보세요. 라이더-웨이트 덱 메이저 아르카나 22장의 정방향·역방향 뜻과 분야별 해석을 알려 드립니다.',
                               active='fortune.html', main=TAROT.replace(NOTE, INFO_TAROT + NOTE), scripts=TAROT_JS),
    'fortune-saju.html': dict(title='사주팔자', desc='양력·음력 생년월일시를 입력하면 만세력으로 네 기둥을 세우고 일간 기질, 오행의 균형, 대운 흐름을 풀어 드립니다. 입력 정보는 서버로 보내지 않습니다.',
                              active='fortune.html', main=SAJU.replace(NOTE, INFO_SAJU + NOTE), scripts=SAJU_JS),
    'fortune.html': dict(title='조선 역술인의 운세방', desc='조선시대 역술인이 운영하는 운세방에서 띠별 운세, 사주팔자, 타로를 무료로 확인하세요. 입력 정보는 서버로 보내지 않습니다.',
                         active='fortune.html', main=HUB.replace(NOTE, INFO_HUB + NOTE)),
    'fortune-zodiac.html': dict(title='띠별 운세', desc='쥐띠부터 돼지띠까지, 내 띠를 고르면 오늘·이번 주·이번 달·올해의 총운, 애정운, 금전운, 건강운을 조선 역술인이 적어 드립니다.',
                                active='fortune.html', main=ZODIAC.replace(NOTE, INFO_ZODIAC + NOTE), scripts=ZODIAC_JS),
}

if __name__ == '__main__':
    for page, p in PAGES.items():
        open(os.path.join(ROOT, page), 'w', encoding='utf-8', newline='').write(
            head(page[:-5], p['title'], p['desc']) + shell(page[:-5], p['active'], p['main'], p.get('scripts', '')))
        print('wrote', page)

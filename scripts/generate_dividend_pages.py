"""
ETF/종목별 배당금 계산기 정적 페이지 생성기.
config/etf_dividend_tickers.py의 티커 목록을 기반으로 dividend-{ticker}.html 페이지를
일괄 생성한다. 데이터는 실행 시점의 data/dividends.json을 fetch()하는 것이 아니라
페이지 로드 시 브라우저에서 fetch하므로, 이 스크립트는 데이터 자체를 담지 않고
페이지 골격(메타태그/구조/JS)만 생성한다. 실행은 fetcher/exporter와 무관하게
티커 목록이 바뀔 때만 다시 돌리면 됨.
"""
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.etf_dividend_tickers import TICKERS
from scripts.page_common import CF_ANALYTICS, NAV, STYLE, TICKER_SCRIPT, THEME_SCRIPT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def page_html(ticker: str, name: str, category: str) -> str:
    slug = f"dividend-{ticker.lower()}"
    title = f"{ticker} 배당금 계산기 (실제 배당 이력) | 머니파이널"
    desc = f"{ticker}({name}) 실제 배당 이력을 바탕으로 보유 주수에 따른 예상 배당금과 세후 수령액을 계산합니다."
    url = f"https://moneyfinal.pages.dev/{slug}"

    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="머니파이널">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{ticker} 배당금 계산기","description":"{desc}","url":"{url}","inLanguage":"ko-KR","isPartOf":{{"@type":"WebSite","name":"머니파이널","url":"https://moneyfinal.pages.dev"}}}}</script>
<style>{STYLE}</style>
</head>
<body>
<div class="ticker"><div class="ticker-inner" id="ticker-inner"></div></div>
<header><a href="index.html" class="logo">💰 머니파이널</a>
  {NAV}
  <div style="display:flex;gap:6px"><button class="theme-btn" onclick="toggleTheme()">🌙</button><button class="menu-btn" onclick="toggleNav()">☰</button></div></header>
<main>
<div class="crumb"><a href="dividend-etf.html">배당ETF</a> &gt; {ticker}</div>
<h1>{ticker} 배당금 계산기</h1>
<div class="sub">{name} · {category} · 실제 배당 이력 기반</div>

<div class="card">
  <div class="sec-title">ℹ️ ETF 정보</div>
  <div id="profile-wrap"><div class="empty">데이터 불러오는 중...</div></div>
</div>

<div class="card">
  <div class="sec-title">📅 최근 배당 이력</div>
  <div id="hist-wrap"><div class="empty">데이터 불러오는 중...</div></div>
</div>

<div class="card">
  <div class="field"><label>보유 주수 (주)</label><input type="text" id="shares" inputmode="numeric" value="100" oninput="calc()"></div>
  <div class="grid2">
    <div class="field"><label>주당 배당금 (USD, 최근 배당 기준)</label><input type="text" id="dps" inputmode="decimal" value="" oninput="calc()"></div>
    <div class="field"><label>매수 단가 (USD, 현재가 자동입력·수정 가능)</label><input type="text" id="price" inputmode="decimal" value="" oninput="calc()"></div>
  </div>
  <div class="field"><label>과세 방식</label><select id="tax" onchange="calc()"><option value="15">미국 원천징수 (15%, 조세조약)</option><option value="0">비과세 가정</option><option value="custom">직접 입력</option></select></div>
  <div class="field" id="custom-tax-field" style="display:none"><label>세율 직접 입력 (%)</label><input type="number" id="custom-tax" value="15" step="0.1" min="0" max="50" oninput="calc()"></div>
</div>

<div class="card">
  <div class="result-hero">
    <div class="rh-label">세후 실수령 배당금 (연간 환산, USD)</div>
    <div class="rh-value" id="r-net">-</div>
  </div>
  <div class="brow"><span class="k">세전 배당금 (연간 환산)</span><span class="v" id="r-gross" style="color:var(--green)"></span></div>
  <div class="brow"><span class="k" id="r-tax-label">원천징수세</span><span class="v" id="r-tax" style="color:var(--red)"></span></div>
  <div class="brow"><span class="k">원화 환산 (세후, 참고)</span><span class="v" id="r-krw"></span></div>
  <div class="brow"><span class="k">투자 원금 (매수단가 기준)</span><span class="v" id="r-prin"></span></div>
  <div class="brow"><span class="k">배당수익률 (연 환산, 세전)</span><span class="v" id="r-yield"></span></div>
</div>

<div class="note">
  ⚠️ 본 페이지는 Yahoo Finance에서 수집한 {ticker}의 실제 배당 이력을 기반으로 하되, 향후 배당금은 참고용 추정치입니다. 실제 배당금은 기초자산 실적과 운용사 정책에 따라 매월 달라질 수 있습니다.<br>
  · "연간 환산"은 가장 최근 배당금 × 배당 횟수(월배당=12, 분기배당=4)로 단순 추정한 값입니다<br>
  · 미국 상장 ETF/종목 배당은 한미 조세조약에 따라 보통 15%가 현지에서 원천징수된 후 지급됩니다<br>
  · 국내 이자·배당소득 합계가 연 2천만원을 초과하면 금융소득종합과세 대상이 될 수 있습니다<br>
  · 원화 환산은 최신 원달러 환율(사이트 상단 티커)을 참고용으로 곱한 값입니다
</div>
</main>
<footer>© 2026 머니파이널 · 세상의 모든 재테크<br><a href="about.html">사이트 소개</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a></footer>
<script>
{THEME_SCRIPT}
function usd(v){{return '$'+v.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:4}});}}
function num(id){{return parseFloat((document.getElementById(id).value||'0').replace(/[^0-9.]/g,''))||0;}}
let payFreq=12;
let latestKrw=null;
function calc(){{
  const shares=num('shares');
  const dps=num('dps');
  const price=num('price');
  const taxSel=document.getElementById('tax').value;
  document.getElementById('custom-tax-field').style.display=taxSel==='custom'?'block':'none';
  const taxRate=taxSel==='custom'?(parseFloat(document.getElementById('custom-tax').value)||0)/100:parseFloat(taxSel)/100;
  if(!shares||!dps){{document.getElementById('r-net').textContent='-';return;}}
  const annualDps=dps*payFreq;
  const gross=shares*annualDps;
  const tax=gross*taxRate;
  const net=gross-tax;
  const principal=shares*price;
  const yieldPct=price>0?(annualDps/price*100):null;
  document.getElementById('r-gross').textContent='+'+usd(gross);
  document.getElementById('r-tax-label').textContent='원천징수세 ('+(taxRate*100).toFixed(1).replace(/\\.0$/,'')+'%)';
  document.getElementById('r-tax').textContent='-'+usd(tax);
  document.getElementById('r-krw').textContent=latestKrw?Math.round(net*latestKrw).toLocaleString('ko-KR')+'원':'-';
  document.getElementById('r-prin').textContent=price>0?usd(principal):'-';
  document.getElementById('r-yield').textContent=yieldPct!==null?yieldPct.toFixed(2)+'%':'-';
  document.getElementById('r-net').textContent=usd(net);
}}
let userEditedPrice=false;
document.getElementById('price').addEventListener('input',()=>{{userEditedPrice=true;}});
async function loadDividendData(){{
  try{{
    const r=await fetch('data/dividends.json');
    const d=await r.json();
    const rows=(d.by_ticker&&d.by_ticker['{ticker}'])||[];
    const wrap=document.getElementById('hist-wrap');
    if(rows.length){{
      if(rows.length>=2){{
        const d0=new Date(rows[0].ex_dividend_date), d1=new Date(rows[1].ex_dividend_date);
        const gapDays=(d0-d1)/86400000;
        payFreq=gapDays<=45?12:gapDays<=100?4:gapDays<=200?2:1;
      }}
      document.getElementById('dps').value=parseFloat(rows[0].amount).toFixed(4);
      let h='<table class="hist"><tr><th>배당락일</th><th>지급일</th><th style="text-align:right">주당 배당금</th></tr>';
      rows.slice(0,12).forEach(row=>{{h+=`<tr><td>${{row.ex_dividend_date}}</td><td>${{row.payment_date||'-'}}</td><td style="text-align:right">$${{parseFloat(row.amount).toFixed(4)}}</td></tr>`;}});
      h+='</table>';
      wrap.innerHTML=h;
    }}else{{
      wrap.innerHTML='<div class="empty">배당 이력 수집 예정입니다</div>';
    }}

    const priceInfo=(d.prices||{{}})['{ticker}'];
    if(priceInfo&&!userEditedPrice){{
      document.getElementById('price').value=parseFloat(priceInfo.price).toFixed(2);
    }}

    const pf=(d.profiles||{{}})['{ticker}'];
    const pwrap=document.getElementById('profile-wrap');
    if(pf){{
      const chgTxt=priceInfo?` <span class="${{priceInfo.change_pct>=0?'up':'down'}}" style="font-size:11px">(${{priceInfo.change_pct>=0?'+':''}}${{parseFloat(priceInfo.change_pct).toFixed(2)}}%)</span>`:'';
      let ph=`<div class="brow"><span class="k">현재가</span><span class="v">${{priceInfo?'$'+parseFloat(priceInfo.price).toFixed(2):'-'}}${{chgTxt}}</span></div>`;
      ph+=`<div class="brow"><span class="k">운용규모 (AUM)</span><span class="v">${{(pf.net_assets/1e8).toFixed(1)}}억 달러</span></div>`;
      ph+=`<div class="brow"><span class="k">총보수율</span><span class="v">${{(pf.expense_ratio*100).toFixed(2)}}%</span></div>`;
      ph+=`<div class="brow"><span class="k">공식 배당수익률</span><span class="v">${{(pf.dividend_yield*100).toFixed(2)}}%</span></div>`;
      ph+=`<div class="brow"><span class="k">설정일</span><span class="v">${{pf.inception_date||'-'}}</span></div>`;
      if(pf.top_holdings&&pf.top_holdings.length){{
        const list=pf.top_holdings.slice(0,5).map(h=>`${{h.symbol}} ${{(parseFloat(h.weight)*100).toFixed(1)}}%`).join(' · ');
        ph+=`<div class="brow"><span class="k">상위 구성종목</span><span class="v" style="font-weight:400;font-size:12px;text-align:right">${{list}}</span></div>`;
      }}
      pwrap.innerHTML=ph;
    }}else{{
      pwrap.innerHTML='<div class="empty">프로필 정보 수집 예정입니다</div>';
    }}
    calc();
  }}catch(e){{
    document.getElementById('hist-wrap').innerHTML='<div class="empty">배당 이력을 불러오지 못했습니다</div>';
    document.getElementById('profile-wrap').innerHTML='<div class="empty">정보를 불러오지 못했습니다</div>';
  }}
}}
loadDividendData();
{TICKER_SCRIPT}
fetch('data/market.json').then(r=>r.json()).then(d=>{{const u=(d.indicators||[]).find(i=>i.indicator_code==='USD_KRW');if(u){{latestKrw=parseFloat(u.value);calc();}}}}).catch(()=>{{}});
</script>
{CF_ANALYTICS}
</body>
</html>
"""


def json_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def hub_html() -> str:
    categories = sorted(set(c for _, _, c in TICKERS))
    cat_buttons = '<button class="ft active" data-cat="all" onclick="setCat(this)">전체</button>' + \
        "".join(f'<button class="ft" data-cat="{c}" onclick="setCat(this)">{c}</button>' for c in categories)

    # 정적 폴백(데이터 로드 실패/최초 렌더)용 - 티커 메타는 서버에서 미리 박아둔다
    ticker_meta_js = ",".join(
        f'{{ticker:"{t}",name:{json_str(n)},category:{json_str(c)}}}' for t, n, c in TICKERS
    )

    title = "월배당 ETF 배당금 계산기 모음 | 머니파이널"
    desc = "JEPI, QYLD, SCHD 등 월배당·분기배당 ETF와 리츠·BDC의 실시간 시세·배당수익률·운용정보를 한 표에서 비교합니다."
    url = "https://moneyfinal.pages.dev/dividend-etf"

    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="머니파이널">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"월배당 ETF 배당금 계산기 모음","description":"{desc}","url":"{url}","inLanguage":"ko-KR","isPartOf":{{"@type":"WebSite","name":"머니파이널","url":"https://moneyfinal.pages.dev"}}}}</script>
<style>{STYLE}
.toolbar{{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.ft{{font-size:12px;padding:3px 10px;border-radius:20px;border:1px solid var(--border);background:none;color:var(--text2);cursor:pointer;transition:all .15s}}
.ft.active,.ft:hover{{border-color:var(--accent);color:var(--accent);background:rgba(56,139,253,.1)}}
.search-box{{flex:1;min-width:160px;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:6px 12px;color:var(--text);font-size:13px;outline:none}}
table.etf-tbl{{width:100%;border-collapse:collapse;font-size:12px}}
table.etf-tbl th{{text-align:right;color:var(--text2);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--border);white-space:nowrap;cursor:pointer;position:sticky;top:0;background:var(--bg2)}}
table.etf-tbl th:hover{{color:var(--accent)}}
table.etf-tbl th:first-child,table.etf-tbl td:first-child{{text-align:left}}
table.etf-tbl td{{padding:8px 10px;border-bottom:1px solid var(--border);white-space:nowrap;text-align:right}}
table.etf-tbl td:first-child{{white-space:normal}}
table.etf-tbl tr:hover{{background:var(--bg3);cursor:pointer}}
table.etf-tbl tr:last-child td{{border-bottom:none}}
.tk-code{{font-weight:700}}
.tk-name{{font-size:11px;color:var(--text2);display:block;margin-top:1px}}
.tbl-wrap{{overflow-x:auto}}
</style>
</head>
<body>
<div class="ticker"><div class="ticker-inner" id="ticker-inner"></div></div>
<header><a href="index.html" class="logo">💰 머니파이널</a>
  {NAV}
  <div style="display:flex;gap:6px"><button class="theme-btn" onclick="toggleTheme()">🌙</button><button class="menu-btn" onclick="toggleNav()">☰</button></div></header>
<main style="max-width:1100px">
<h1>월배당 ETF 배당금 계산기</h1>
<div class="sub">실제 시세·배당 이력을 기반으로 한 티커별 배당금 계산기 ({len(TICKERS)}종목) · 티커를 클릭하면 상세 계산기로 이동합니다</div>
<div class="card">
  <div class="toolbar">
    {cat_buttons}
    <input type="text" class="search-box" id="q" placeholder="티커·이름 검색" oninput="renderTbl()">
  </div>
  <div class="tbl-wrap">
  <table class="etf-tbl">
    <thead><tr>
      <th data-k="ticker" onclick="setSort(this)">티커</th>
      <th data-k="price" onclick="setSort(this)">현재가</th>
      <th data-k="yield" onclick="setSort(this)">배당수익률</th>
      <th data-k="freq" onclick="setSort(this)">주기</th>
      <th data-k="aum" onclick="setSort(this)">운용규모</th>
      <th data-k="expense" onclick="setSort(this)">보수율</th>
    </tr></thead>
    <tbody id="tbody"><tr><td colspan="6" class="empty">로딩 중...</td></tr></tbody>
  </table>
  </div>
</div>
</main>
<footer>© 2026 머니파이널 · 세상의 모든 재테크<br><a href="about.html">사이트 소개</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a></footer>
<script>
{THEME_SCRIPT}
const TICKER_META=[{ticker_meta_js}];
let CAT='all',SORT_KEY='yield',SORT_DIR='desc';
let ROWS=[];
function setCat(btn){{CAT=btn.dataset.cat;btn.parentElement.querySelectorAll('.ft').forEach(b=>b.classList.remove('active'));btn.classList.add('active');renderTbl();}}
function setSort(th){{const k=th.dataset.k;if(SORT_KEY===k){{SORT_DIR=SORT_DIR==='desc'?'asc':'desc';}}else{{SORT_KEY=k;SORT_DIR='desc';}}renderTbl();}}
function usd(v){{return v===null||v===undefined?'-':'$'+v.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});}}
function pct(v){{return v===null||v===undefined?'-':v.toFixed(2)+'%';}}
function eokDollar(v){{return v===null||v===undefined?'-':(v/1e8).toLocaleString('ko-KR',{{maximumFractionDigits:1}})+'억 달러';}}
async function loadData(){{
  try{{
    const r=await fetch('data/dividends.json');const d=await r.json();
    const prices=d.prices||{{}},profiles=d.profiles||{{}},byTicker=d.by_ticker||{{}};
    ROWS=TICKER_META.map(m=>{{
      const p=prices[m.ticker],pf=profiles[m.ticker],rows=byTicker[m.ticker]||[];
      let freq=null,annualDps=null;
      if(rows.length>=2){{
        const d0=new Date(rows[0].ex_dividend_date),d1=new Date(rows[1].ex_dividend_date);
        const gapDays=(d0-d1)/86400000;
        freq=gapDays<=45?'월배당':gapDays<=100?'분기배당':gapDays<=200?'반기배당':'연배당';
      }}
      if(rows.length){{
        const n=freq==='월배당'?12:freq==='분기배당'?4:freq==='반기배당'?2:1;
        annualDps=parseFloat(rows[0].amount)*n;
      }}
      const price=p?parseFloat(p.price):null;
      const yieldPct=pf&&pf.dividend_yield?pf.dividend_yield*100:(price&&annualDps?annualDps/price*100:null);
      return{{...m,price,yieldPct,freq,aum:pf?pf.net_assets:null,expense:pf?pf.expense_ratio*100:null}};
    }});
  }}catch(e){{ROWS=TICKER_META.map(m=>({{...m,price:null,yieldPct:null,freq:null,aum:null,expense:null}}));}}
  renderTbl();
}}
function renderTbl(){{
  const q=document.getElementById('q').value.trim().toLowerCase();
  let list=ROWS.filter(r=>CAT==='all'||r.category===CAT);
  if(q)list=list.filter(r=>(r.ticker+' '+r.name).toLowerCase().includes(q));
  list=list.slice().sort((a,b)=>{{
    const map={{ticker:'ticker',price:'price',yield:'yieldPct',freq:'freq',aum:'aum',expense:'expense'}};
    const k=map[SORT_KEY];
    let av=a[k],bv=b[k];
    if(av===null||av===undefined)av=SORT_DIR==='desc'?-Infinity:Infinity;
    if(bv===null||bv===undefined)bv=SORT_DIR==='desc'?-Infinity:Infinity;
    if(typeof av==='string')return SORT_DIR==='asc'?av.localeCompare(bv):bv.localeCompare(av);
    return SORT_DIR==='asc'?av-bv:bv-av;
  }});
  const tbody=document.getElementById('tbody');
  if(!list.length){{tbody.innerHTML='<tr><td colspan="6" class="empty">조건에 맞는 ETF가 없습니다</td></tr>';return;}}
  tbody.innerHTML=list.map(r=>`<tr onclick="location.href='dividend-${{r.ticker.toLowerCase()}}.html'">
    <td><span class="tk-code">${{r.ticker}}</span><span class="tk-name">${{r.name}}</span></td>
    <td>${{usd(r.price)}}</td>
    <td class="${{r.yieldPct?'up':''}}">${{pct(r.yieldPct)}}</td>
    <td>${{r.freq||'-'}}</td>
    <td>${{eokDollar(r.aum)}}</td>
    <td>${{pct(r.expense)}}</td>
  </tr>`).join('');
}}
loadData();
{TICKER_SCRIPT}
</script>
{CF_ANALYTICS}
</body>
</html>
"""


def main():
    count = 0
    for ticker, name, category in TICKERS:
        path = os.path.join(ROOT, f"dividend-{ticker.lower()}.html")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(page_html(ticker, name, category))
        count += 1
    hub_path = os.path.join(ROOT, "dividend-etf.html")
    with open(hub_path, 'w', encoding='utf-8') as f:
        f.write(hub_html())
    print(f"생성 완료: {count}개 티커 페이지 + 허브 페이지 1개")


if __name__ == '__main__':
    main()

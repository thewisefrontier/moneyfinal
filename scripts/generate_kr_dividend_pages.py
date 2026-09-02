"""
국내 상장 배당 ETF 계산기 정적 페이지 생성기.
config/kr_dividend_etf_tickers.py 기반으로 dividend-kr-{code}.html을 생성한다.
US판(generate_dividend_pages.py)과 짝을 이루지만 세금 로직이 다르다:

- 미국 ETF는 매매차익을 계산하지 않고 분배금만 계산했음(원래부터 시세차익
  계산 범위 밖) - 국내 ETF도 동일하게 분배금 계산기로 범위를 맞춘다.
  이유: "기타 ETF"의 매매차익 과세는 Min(실제매매차익, 보유기간 과표기준가
  상승분) 방식인데, 과표기준가는 일반 투자자가 실시간으로 알 수 없는
  값이라 정확한 계산이 불가능함 - 잘못된 근사치를 보여주는 것보다 계산
  범위에서 빼고 "매매차익도 과세 대상" 뱃지로 안내하는 편이 안전.
- 분배금 세율은 국내주식형/기타형 관계없이 배당소득세 15.4%로 동일해서
  (삼성자산운용 공식 가이드로 확인), 분배금 계산 자체는 두 유형이 같은
  수식을 쓴다. 유형 차이는 "매매차익 과세 여부" 뱃지로만 안내한다.
"""
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.kr_dividend_etf_tickers import TICKERS
from scripts.page_common import CF_ANALYTICS, NAV, STYLE, TICKER_SCRIPT, THEME_SCRIPT, json_str

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def page_html(code: str, name: str, category: str, is_domestic_equity: bool) -> str:
    slug = f"dividend-kr-{code}"
    title = f"{name} 배당금 계산기 (실제 분배금 이력) | 머니파이널"
    desc = f"{name}({code}) 실제 분배금 이력을 바탕으로 보유 좌수에 따른 예상 분배금과 세후 수령액을 계산합니다."
    url = f"https://moneyfinal.pages.dev/{slug}"

    if is_domestic_equity:
        badge_html = '<span class="badge tax-free">국내주식형 · 매매차익 비과세</span>'
        type_note = "국내주식형 ETF로 분류되어 매매차익은 비과세이며, 분배금에만 배당소득세가 부과됩니다."
    else:
        badge_html = '<span class="badge tax-other">기타 ETF · 매매차익도 과세</span>'
        type_note = "국내주식형이 아닌 기타 ETF로 분류되어 매매차익도 배당소득세 과세 대상입니다(실제 매매차익과 보유기간 과표기준가 상승분 중 작은 금액 × 15.4% - 과표기준가는 실시간 확인이 어려워 본 페이지에서 매매차익은 계산하지 않습니다)."

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
<meta name="robots" content="noindex">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{name} 배당금 계산기","description":"{desc}","url":"{url}","inLanguage":"ko-KR","isPartOf":{{"@type":"WebSite","name":"머니파이널","url":"https://moneyfinal.pages.dev"}}}}</script>
<style>{STYLE}</style>
</head>
<body>
<div class="ticker"><div class="ticker-inner" id="ticker-inner"></div></div>
<header><a href="index.html" class="logo">💰 머니파이널</a>
  {NAV}
  <div style="display:flex;gap:6px"><button class="theme-btn" onclick="toggleTheme()">🌙</button><button class="menu-btn" onclick="toggleNav()">☰</button></div></header>
<main>
<div class="crumb"><a href="dividend-kr-etf.html">국내ETF</a> &gt; {name}</div>
<h1>{name} 배당금 계산기{badge_html}</h1>
<div class="sub">{code} · {category} · 실제 분배금 이력 기반</div>

<div class="card">
  <div class="sec-title">ℹ️ 종목 정보</div>
  <div id="profile-wrap"><div class="empty">데이터 불러오는 중...</div></div>
</div>

<div class="card">
  <div class="sec-title">📅 최근 분배금 이력</div>
  <div id="hist-wrap"><div class="empty">데이터 불러오는 중...</div></div>
</div>

<div class="card">
  <div class="field"><label>보유 좌수 (좌)</label><input type="text" id="shares" inputmode="numeric" value="100" oninput="calc()"></div>
  <div class="grid2">
    <div class="field"><label>좌당 분배금 (원, 최근 분배 기준)</label><input type="text" id="dps" inputmode="decimal" value="" oninput="calc()"></div>
    <div class="field"><label>매수 단가 (원, 현재가 자동입력·수정 가능)</label><input type="text" id="price" inputmode="decimal" value="" oninput="calc()"></div>
  </div>
</div>

<div class="card">
  <div class="result-hero">
    <div class="rh-label">세후 실수령 분배금 (연간 환산, 원)</div>
    <div class="rh-value" id="r-net">-</div>
  </div>
  <div class="brow"><span class="k">세전 분배금 (연간 환산)</span><span class="v" id="r-gross" style="color:var(--green)"></span></div>
  <div class="brow"><span class="k">배당소득세 (15.4%)</span><span class="v" id="r-tax" style="color:var(--red)"></span></div>
  <div class="brow"><span class="k">투자 원금 (매수단가 기준)</span><span class="v" id="r-prin"></span></div>
  <div class="brow"><span class="k">분배수익률 (연 환산, 세전)</span><span class="v" id="r-yield"></span></div>
</div>

<div class="note">
  ⚠️ 본 페이지는 Yahoo Finance에서 수집한 {name}의 실제 분배금 이력을 기반으로 하되, 향후 분배금은 참고용 추정치입니다. 실제 분배금은 기초자산 실적과 운용사 정책에 따라 매월 달라질 수 있습니다.<br>
  · {type_note}<br>
  · "연간 환산"은 가장 최근 분배금 × 분배 횟수(월분배=12, 분기분배=4)로 단순 추정한 값입니다<br>
  · 분배금은 배당소득에 해당하여 국내 이자·배당소득 합계가 연 2천만원을 초과하면 금융소득종합과세 대상이 될 수 있습니다<br>
  · 본 페이지는 분배금만 계산하며 매매차익(양도)은 계산 범위에 포함하지 않습니다
</div>
</main>
<footer>© 2026 머니파이널 · 세상의 모든 재테크<br><a href="about.html">사이트 소개</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a></footer>
<script>
{THEME_SCRIPT}
function krw(v){{return Math.round(v).toLocaleString('ko-KR')+'원';}}
function num(id){{return parseFloat((document.getElementById(id).value||'0').replace(/[^0-9.]/g,''))||0;}}
const TAX_RATE=0.154;
let payFreq=12;
function calc(){{
  const shares=num('shares');
  const dps=num('dps');
  const price=num('price');
  if(!shares||!dps){{document.getElementById('r-net').textContent='-';return;}}
  const annualDps=dps*payFreq;
  const gross=shares*annualDps;
  const tax=gross*TAX_RATE;
  const net=gross-tax;
  const principal=shares*price;
  const yieldPct=price>0?(annualDps/price*100):null;
  document.getElementById('r-gross').textContent='+'+krw(gross);
  document.getElementById('r-tax').textContent='-'+krw(tax);
  document.getElementById('r-prin').textContent=price>0?krw(principal):'-';
  document.getElementById('r-yield').textContent=yieldPct!==null?yieldPct.toFixed(2)+'%':'-';
  document.getElementById('r-net').textContent=krw(net);
}}
let userEditedPrice=false;
document.getElementById('price').addEventListener('input',()=>{{userEditedPrice=true;}});
async function loadDividendData(){{
  try{{
    const r=await fetch('data/kr_dividends.json');
    const d=await r.json();
    const rows=(d.by_ticker&&d.by_ticker['{code}'])||[];
    const wrap=document.getElementById('hist-wrap');
    if(rows.length){{
      if(rows.length>=2){{
        const d0=new Date(rows[0].ex_dividend_date), d1=new Date(rows[1].ex_dividend_date);
        const gapDays=(d0-d1)/86400000;
        payFreq=gapDays<=45?12:gapDays<=100?4:gapDays<=200?2:1;
      }}
      document.getElementById('dps').value=parseFloat(rows[0].amount).toFixed(0);
      let h='<table class="hist"><tr><th>분배락일</th><th style="text-align:right">좌당 분배금</th></tr>';
      rows.slice(0,12).forEach(row=>{{h+=`<tr><td>${{row.ex_dividend_date}}</td><td style="text-align:right">${{Math.round(row.amount).toLocaleString('ko-KR')}}원</td></tr>`;}});
      h+='</table>';
      wrap.innerHTML=h;
    }}else{{
      wrap.innerHTML='<div class="empty">분배금 이력 수집 예정입니다</div>';
    }}

    const priceInfo=(d.prices||{{}})['{code}'];
    const pwrap=document.getElementById('profile-wrap');
    if(priceInfo){{
      if(!userEditedPrice)document.getElementById('price').value=Math.round(priceInfo.price);
      const chgTxt=` <span class="${{priceInfo.change_pct>=0?'up':'down'}}" style="font-size:11px">(${{priceInfo.change_pct>=0?'+':''}}${{parseFloat(priceInfo.change_pct).toFixed(2)}}%)</span>`;
      let ph=`<div class="brow"><span class="k">현재가</span><span class="v">${{Math.round(priceInfo.price).toLocaleString('ko-KR')}}원${{chgTxt}}</span></div>`;
      ph+=`<div class="brow"><span class="k">기준일</span><span class="v">${{priceInfo.base_date||'-'}}</span></div>`;
      pwrap.innerHTML=ph;
    }}else{{
      pwrap.innerHTML='<div class="empty">시세 정보 수집 예정입니다</div>';
    }}
    calc();
  }}catch(e){{
    document.getElementById('hist-wrap').innerHTML='<div class="empty">분배금 이력을 불러오지 못했습니다</div>';
    document.getElementById('profile-wrap').innerHTML='<div class="empty">정보를 불러오지 못했습니다</div>';
  }}
}}
loadDividendData();
{TICKER_SCRIPT}
</script>
{CF_ANALYTICS}
</body>
</html>
"""


def hub_html() -> str:
    categories = sorted(set(c for _, _, c, _ in TICKERS))
    cat_buttons = '<button class="ft active" data-cat="all" onclick="setCat(this)">전체</button>' + \
        "".join(f'<button class="ft" data-cat="{c}" onclick="setCat(this)">{c}</button>' for c in categories)

    ticker_meta_js = ",".join(
        f'{{code:"{code}",name:{json_str(name)},category:{json_str(cat)},domestic:{"true" if dom else "false"}}}'
        for code, name, cat, dom in TICKERS
    )

    title = "국내 상장 배당 ETF 계산기 모음 | 머니파이널"
    desc = "TIGER 미국배당다우존스, KODEX 고배당주 등 국내 상장 배당 ETF의 실제 분배금 이력과 세후 수령액을 계산합니다."
    url = "https://moneyfinal.pages.dev/dividend-kr-etf.html"

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
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"국내 배당ETF","description":"{desc}","url":"{url}","inLanguage":"ko-KR","isPartOf":{{"@type":"WebSite","name":"머니파이널","url":"https://moneyfinal.pages.dev"}}}}</script>
<style>{STYLE}
.toolbar{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
.ft{{font-size:12px;padding:5px 12px;border-radius:20px;border:1px solid var(--border);background:none;color:var(--text2);cursor:pointer}}
.ft.active,.ft:hover{{border-color:var(--accent);color:var(--accent)}}
.tbl-wrap{{overflow-x:auto}}
table.etf-tbl{{width:100%;border-collapse:collapse;font-size:13px;min-width:600px}}
table.etf-tbl th{{text-align:right;color:var(--text2);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--border);white-space:nowrap}}
table.etf-tbl th:first-child,table.etf-tbl td:first-child{{text-align:left}}
table.etf-tbl td{{padding:10px;border-bottom:1px solid var(--border);text-align:right}}
table.etf-tbl tr:hover{{background:var(--bg3)}}
.tk-name{{font-weight:600}}
.tk-code{{color:var(--text2);font-size:11px}}
main{{max-width:1100px}}</style>
</head>
<body>
<div class="ticker"><div class="ticker-inner" id="ticker-inner"></div></div>
<header><a href="index.html" class="logo">💰 머니파이널</a>
  {NAV}
  <div style="display:flex;gap:6px"><button class="theme-btn" onclick="toggleTheme()">🌙</button><button class="menu-btn" onclick="toggleNav()">☰</button></div></header>
<main>
<div class="crumb"><a href="dividend-etf.html">배당ETF</a> &gt; 국내ETF</div>
<h1>국내 상장 배당 ETF 계산기</h1>
<div class="sub">실제 분배금 이력 기반 · 종목명을 클릭하면 상세 계산기로 이동합니다</div>
<div class="toolbar">{cat_buttons}</div>
<div class="tbl-wrap"><table class="etf-tbl" id="etf-tbl">
<thead><tr><th>종목</th><th>유형</th><th>현재가</th><th>최근 분배금</th><th>분배주기</th><th>분배수익률</th></tr></thead>
<tbody id="etf-tbody"><tr><td colspan="6" class="empty">로딩 중...</td></tr></tbody>
</table></div>
<div class="note" style="margin-top:20px">
  ⚠️ 국내주식형 ETF는 매매차익이 비과세이고, 그 외(해외지수·리츠 등 추종) ETF는 매매차익도 배당소득세 과세 대상입니다. 분배금은 유형과 무관하게 15.4% 배당소득세가 부과됩니다.<br>
  · 데이터는 Yahoo Finance 기반이며 국내 ETF는 운용규모·보수율 정보를 제공받지 못해 표시하지 않습니다.
</div>
</main>
<footer>© 2026 머니파이널 · 세상의 모든 재테크<br><a href="about.html">사이트 소개</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a></footer>
<script>
{THEME_SCRIPT}
const TICKER_META=[{ticker_meta_js}];
let CAT='all', ROWS=[];
function setCat(btn){{CAT=btn.dataset.cat;btn.parentElement.querySelectorAll('.ft').forEach(b=>b.classList.remove('active'));btn.classList.add('active');renderTbl();}}
function pct(v){{return v===null||v===undefined?'-':(v*100).toFixed(2)+'%';}}
async function loadData(){{
  try{{
    const r=await fetch('data/kr_dividends.json');
    const d=await r.json();
    const byTicker=d.by_ticker||{{}}, prices=d.prices||{{}};
    ROWS=TICKER_META.map(m=>{{
      const divs=byTicker[m.code]||[];
      const price=prices[m.code];
      let freq=null, yieldPct=null, lastAmt=null;
      if(divs.length){{
        lastAmt=parseFloat(divs[0].amount);
        if(divs.length>=2){{
          const gapDays=(new Date(divs[0].ex_dividend_date)-new Date(divs[1].ex_dividend_date))/86400000;
          freq=gapDays<=45?12:gapDays<=100?4:gapDays<=200?2:1;
        }}
        if(price&&price.price&&freq)yieldPct=(lastAmt*freq)/price.price;
      }}
      return {{...m,price:price?price.price:null,changePct:price?price.change_pct:null,lastAmt,freq,yieldPct}};
    }});
    renderTbl();
  }}catch(e){{document.getElementById('etf-tbody').innerHTML='<tr><td colspan="6" class="empty">데이터를 불러오지 못했습니다</td></tr>';}}
}}
function renderTbl(){{
  const rows=(CAT==='all'?ROWS:ROWS.filter(r=>r.category===CAT)).slice().sort((a,b)=>(b.yieldPct||0)-(a.yieldPct||0));
  document.getElementById('etf-tbody').innerHTML=rows.length?rows.map(r=>{{
    const freqTxt=r.freq===12?'월분배':r.freq===4?'분기':r.freq===2?'반기':r.freq===1?'연1회':'-';
    const badge=r.domestic?'<span class="badge tax-free" style="margin-left:0">국내주식형</span>':'<span class="badge tax-other" style="margin-left:0">기타</span>';
    return `<tr onclick="location.href='dividend-kr-${{r.code}}.html'" style="cursor:pointer">
    <td><div class="tk-name">${{r.name}}</div><div class="tk-code">${{r.code}} · ${{r.category}}</div></td>
    <td>${{badge}}</td>
    <td>${{r.price?Math.round(r.price).toLocaleString('ko-KR')+'원':'-'}}</td>
    <td>${{r.lastAmt?Math.round(r.lastAmt).toLocaleString('ko-KR')+'원':'-'}}</td>
    <td>${{freqTxt}}</td>
    <td class="${{r.yieldPct?'up':''}}">${{pct(r.yieldPct)}}</td>
  </tr>`;}}).join(''):'<tr><td colspan="6" class="empty">데이터 없음</td></tr>';
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
    for code, name, category, is_domestic_equity in TICKERS:
        path = os.path.join(ROOT, f"dividend-kr-{code}.html")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(page_html(code, name, category, is_domestic_equity))
        count += 1
    hub_path = os.path.join(ROOT, "dividend-kr-etf.html")
    with open(hub_path, 'w', encoding='utf-8') as f:
        f.write(hub_html())
    print(f"생성 완료: {count}개 국내 ETF 페이지 + 허브 페이지 1개")


if __name__ == '__main__':
    main()

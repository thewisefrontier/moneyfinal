"""
정적 페이지 생성기(generate_*.py)들이 공유하는 nav/style/공통 스크립트.
한 곳에서만 관리해서 생성기별로 NAV 등이 따로 놀다 구버전으로 되돌아가는
사고를 방지한다(2026-09-02, generate_dividend_pages.py의 NAV가 파이어 탭
승격 이전 버전으로 방치되어 재생성 시 82개 페이지 nav가 되돌아갈 뻔했음).

⚠️ 실제 페이지의 nav를 바꿀 때는 index.html 등 손으로 쓴 페이지와 이 파일을
반드시 같이 갱신할 것.
"""

CF_ANALYTICS = '<!-- Cloudflare Web Analytics --><script type=\'module\' src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "5ec3e89757844a3582c90d3524a2cead"}\'></script><!-- End Cloudflare Web Analytics -->'

NAV = '<nav><a href="index.html">홈</a><a href="invest.html">투자</a><a href="dividend-etf.html" class="active">배당ETF</a><a href="calc-fire-dividend.html">파이어</a><a href="rates.html">예금·적금</a><a href="loans.html">대출</a><a href="market.html">시장</a><a href="savings.html">ISA</a><a href="annuity.html">연금저축</a><a href="insurance.html">보험</a><a href="company.html">기업정보</a><a href="macro.html">경제지표</a><a href="calc.html">계산기</a></nav>'

STYLE = """:root[data-theme="dark"]{--bg:#0d1117;--bg2:#161b22;--bg3:#1c2128;--border:#30363d;--text:#e6edf3;--text2:#8b949e;--green:#3fb950;--red:#f85149;--yellow:#d29922;--blue:#388bfd;--accent:#388bfd}
:root[data-theme="light"]{--bg:#fff;--bg2:#f6f8fa;--bg3:#eaeef2;--border:#d0d7de;--text:#1f2328;--text2:#656d76;--green:#1a7f37;--red:#cf222e;--yellow:#9a6700;--blue:#0969da;--accent:#0969da}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.5}
a{color:inherit;text-decoration:none}
header{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 24px;height:52px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:30px;z-index:100}
.logo{font-size:18px;font-weight:700;color:var(--accent);letter-spacing:-0.5px;white-space:nowrap;flex-shrink:0}
nav{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none}nav::-webkit-scrollbar{display:none}nav a{flex-shrink:0}
nav a{color:var(--text2);text-decoration:none;padding:6px 10px;border-radius:6px;font-size:13px;font-weight:500;transition:all .15s;white-space:nowrap}
nav a:hover,nav a.active{color:var(--text);background:var(--bg3)}
.theme-btn{background:none;border:1px solid var(--border);color:var(--text2);padding:5px 10px;border-radius:6px;cursor:pointer;font-size:13px}
.menu-btn{display:none;background:none;border:1px solid var(--border);color:var(--text2);padding:5px 10px;border-radius:6px;cursor:pointer;font-size:15px;line-height:1}
@media(max-width:860px){.menu-btn{display:block}nav{display:none;position:fixed;top:82px;left:0;right:0;background:var(--bg2);border-bottom:1px solid var(--border);flex-direction:column;gap:0;padding:8px;max-height:calc(100vh - 82px);overflow-y:auto;z-index:102}nav.open{display:flex}nav a{padding:12px 14px;width:100%}}
main{max-width:720px;margin:0 auto;padding:24px 16px}
h1{font-size:20px;font-weight:700;margin-bottom:4px}
.sub{font-size:13px;color:var(--text2);margin-bottom:24px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:20px}
.field{margin-bottom:16px}
.field label{display:block;font-size:12px;color:var(--text2);font-weight:600;margin-bottom:6px}
.field input,.field select{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:6px;color:var(--text);padding:11px 12px;font-size:15px;outline:none}
.field input:focus,.field select:focus{border-color:var(--accent)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:600px){.grid2{grid-template-columns:1fr}}
.result-hero{text-align:center;padding:20px 0 12px}
.rh-label{font-size:12px;color:var(--text2);margin-bottom:6px}
.rh-value{font-size:32px;font-weight:700;color:var(--green);letter-spacing:-1px}
.brow{display:flex;justify-content:space-between;padding:10px 4px;border-bottom:1px solid var(--border);font-size:13px}
.brow:last-child{border-bottom:none}
.brow .k{color:var(--text2)}
.brow .v{font-weight:600}
.note{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px 16px;font-size:12px;color:var(--text2);line-height:1.7}
.sec-title{font-size:14px;font-weight:700;margin-bottom:10px}
table.hist{width:100%;border-collapse:collapse;font-size:12px}
table.hist th{text-align:left;color:var(--text2);font-weight:600;padding:6px 4px;border-bottom:1px solid var(--border)}
table.hist td{padding:6px 4px;border-bottom:1px solid var(--border)}
table.hist tr:last-child td{border-bottom:none}
.empty{color:var(--text2);text-align:center;padding:20px 0;font-size:13px}
.crumb{font-size:12px;color:var(--text2);margin-bottom:10px}
.crumb a{color:var(--accent)}
.badge{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;margin-left:6px}
.badge.tax-free{background:rgba(63,185,80,.15);color:var(--green)}
.badge.tax-other{background:rgba(210,153,34,.15);color:var(--yellow)}
footer{border-top:1px solid var(--border);padding:20px;text-align:center;font-size:11px;color:var(--text2);margin-top:40px}
.ticker{background:var(--bg2);border-bottom:1px solid var(--border);overflow:hidden;height:30px;display:flex;align-items:center;position:sticky;top:0;z-index:101}
.ticker-inner{display:flex;gap:28px;animation:ticker 50s linear infinite;white-space:nowrap;padding:0 16px}
@keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ti{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text2)}
.ti .name{color:var(--text);font-weight:500}
.ticker .up{color:var(--green)}.ticker .down{color:var(--red)}.ticker .neutral{color:var(--text2)}"""

TICKER_SCRIPT = "async function loadTicker(){try{const r=await fetch('data/market.json');const d=await r.json();const inds=d.indicators||[];const L={'USD_KRW':'원달러','BASE_RATE':'기준금리','FED_RATE':'미국금리','USD_INDEX':'달러인덱스','US_YIELD_CURVE':'장단기금리차','M2_TOTAL':'M2','KOSPI':'코스피','KOSDAQ':'코스닥','US_SP500':'S&P500','US_DJIA':'다우','US_NASDAQ':'나스닥'};const tf=(v,dg)=>parseFloat(v).toLocaleString('ko-KR',{minimumFractionDigits:dg,maximumFractionDigits:dg});const tc=s=>s==='red'?'down':s==='yellow'?'neutral':'up';let h='';inds.forEach(i=>{if(!L[i.indicator_code])return;const v=i.indicator_code==='M2_TOTAL'?(i.value/1000000).toFixed(1)+'조원':tf(i.value,['%','Index','pt','USD/배럴'].includes(i.unit)?2:0)+(i.unit?' '+i.unit:'');h+=`<div class=\"ti\"><span class=\"name\">${L[i.indicator_code]}</span><span class=\"${tc(i.signal)}\">${v}</span></div>`;});document.getElementById('ticker-inner').innerHTML=h+h;}catch(e){}}\nloadTicker();"

THEME_SCRIPT = "function toggleNav(){const n=document.querySelector('nav');if(n)n.classList.toggle('open');}\nfunction toggleTheme(){const h=document.documentElement;h.setAttribute('data-theme',h.getAttribute('data-theme')==='dark'?'light':'dark');document.querySelector('.theme-btn').textContent=h.getAttribute('data-theme')==='dark'?'🌙':'🌑';}"

# 원화 표시는 3자리 콤마가 아니라 억/만 단위로 끊어서 보여준다 (예: 1,508,069원 -> 150만8069원).
# calc-fire-dividend.html의 won()이 기준 구현. 새 원화 표시 페이지는 무조건 이 함수를 씀.
WON_SCRIPT = "function won(v){const n=Math.round(v);const sign=n<0?'-':'';const abs=Math.abs(n);const eok=Math.floor(abs/1e8);const man=Math.floor((abs%1e8)/1e4);const rest=abs%1e4;if(!eok&&!man)return sign+rest.toLocaleString('ko-KR')+'원';let s=sign;if(eok)s+=eok+'억';if(man)s+=man+'만';if(rest)s+=rest;return s+'원';}"


def json_str(s: str) -> str:
    import json
    return json.dumps(s, ensure_ascii=False)

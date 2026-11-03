# 영어판 전용 코드 수정(통화·세금 문구 등). 키는 파일명 또는 glob. 번역 문구 추출 전에 적용된다.
# old가 're:'로 시작하면 정규식(DOTALL)으로 치환한다.
import json
_NM = {'워런 버핏': 'Warren Buffett', '빌 애크먼': 'Bill Ackman', '마이클 버리': 'Michael Burry', '칼 아이칸': 'Carl Icahn', '세스 클라만': 'Seth Klarman',
       '스탠리 드러켄밀러': 'Stanley Druckenmiller', '데이비드 아인혼': 'David Einhorn', '데이비드 테퍼': 'David Tepper', '리 루': 'Li Lu', '하워드 막스': 'Howard Marks',
       '체이스 콜먼': 'Chase Coleman', '넬슨 펠츠': 'Nelson Peltz', '프렘 왓사': 'Prem Watsa', '브루스 버코위츠': 'Bruce Berkowitz', '글렌 그린버그': 'Glenn Greenberg',
       '톰 게이너': 'Tom Gayner', '빌 밀러': 'Bill Miller', '대니얼 로브': 'Daniel Loeb', '안드레아스 할보르센': 'Andreas Halvorsen', '스티븐 만델': 'Stephen Mandel',
       '브릿지워터': 'Bridgewater', '시타델': 'Citadel', '국민연금공단': 'Korea National Pension Service'}
_USD = "const u=[[1e12,'T'],[1e9,'B'],[1e6,'M'],[1e3,'K']].find(x=>v>=x[0]);const s=u?(v/u[0]).toFixed(v/u[0]>=100?0:v/u[0]>=10?1:2)+u[1]:Math.round(v)+'';"

PATCHES = {
    'dividend-*.html': [
        ('<option value="15">미국 원천징수 (15%, 조세조약)</option><option value="0">비과세 가정</option>',
         '<option value="30">US withholding for non-residents (30% default)</option><option value="15">Treaty rate (15%)</option><option value="0">No tax assumed</option>'),
        ('<div class="brow"><span class="k">원화 환산 (세후, 참고)</span><span class="v" id="r-krw"></span></div>\n  ', ''),
        ("  document.getElementById('r-krw').textContent=latestKrw?won(net*latestKrw):'-';\n", ''),
        ('<span class="v">${(pf.net_assets/1e8).toFixed(1)}억 달러</span>', '<span class="v">$${(pf.net_assets/1e9).toFixed(2)}B</span>'),
        ('  · "연간 환산"은 가장 최근 배당금 × 배당 횟수(월배당=12, 분기배당=4)로 단순 추정한 값입니다<br>\n'
         '  · 미국 상장 ETF/종목 배당은 한미 조세조약에 따라 보통 15%가 현지에서 원천징수된 후 지급됩니다<br>\n'
         '  · 국내 이자·배당소득 합계가 연 2천만원을 초과하면 금융소득종합과세 대상이 될 수 있습니다<br>\n'
         '  · 원화 환산은 최신 원달러 환율(사이트 상단 티커)을 참고용으로 곱한 값입니다\n',
         '  · “Annualized” is a simple estimate: the latest dividend × payments per year (monthly = 12, quarterly = 4)<br>\n'
         '  · Dividends from US-listed ETFs and stocks are normally subject to 30% US withholding for non-residents, often reduced to 15% under a tax treaty<br>\n'
         '  · Your own tax treatment depends on where you live; this calculator is not tax advice\n'),
    ],
    'dividend-etf.html': [
        ("function eokDollar(v){return v===null||v===undefined?'-':(v/1e8).toLocaleString('ko-KR',{maximumFractionDigits:1})+'억 달러';}",
         "function eokDollar(v){return v===null||v===undefined?'-':'$'+(v/1e9).toFixed(2)+'B';}"),
    ],
    'us-fin.html': [
        ("usd(x).replace('달러','주')", "usd(x).replace('$','')+' shares'"),
        ("const dlr=v=>v==null?'-':v.toFixed(2)+'달러';", "const dlr=v=>v==null?'-':(v<0?'-$'+(-v).toFixed(2):'$'+v.toFixed(2));"),
        ("re:function usd\\(n\\)\\{if\\(n==null\\)return'-';.*?'달러'\\;\\}",
         "function usd(n){if(n==null)return'-';const neg=n<0,v=Math.abs(n);" + _USD + "return(neg?'-':'')+'$'+s;}"),
    ],
    'compare.html': [
        ("re:function amt\\(n,unit\\)\\{.*?\\+unit;\\}",
         "function amt(n,unit){if(n==null)return'-';const neg=n<0,v=Math.abs(n);" + _USD.replace('const u=', 'const t=').replace('u[0]', 't[0]').replace('u[1]', 't[1]').replace('?(v', '?(v').replace('s=u?', 's=t?') + "return(neg?'-':'')+unit+s;}"),
        ("let M='kr',P='a'", "let M='us',P='a'"),
        ('<button class="tab active" data-m="kr">', '<button class="tab" data-m="kr">'),
        ('<button class="tab" data-m="us">', '<button class="tab active" data-m="us">'),  # 영어판은 미국 기업이 기본
        ("x=>x==null?'-':x.toFixed(2)+'달러'", "x=>x==null?'-':(M==='kr'?'₩':'$')+x.toFixed(2)"),
        ("kr?'원':'달러'", "kr?'₩':'$'"),
        ("Math.round(x)+'원'", "'₩'+Math.round(x)"),
    ],
    'superinvestor.html': [
        # 데이터의 투자자 이름이 한글이라 영어판에서만 영문 이름으로 바꿔 읽는다(JS에 한글이 남지 않도록 \u 이스케이프)
        ("const r=await fetch('data/superinvestors.json');const d=await r.json();",
         "const r=await fetch('data/superinvestors.json');let tx=await r.text();const NM=" + json.dumps(_NM, ensure_ascii=True) +
         ";Object.keys(NM).forEach(k=>{tx=tx.split(k).join(NM[k]);});const d=JSON.parse(tx);"),
        ("if(n>=1e12)return'$'+(n/1e12).toFixed(2)+'조';if(n>=1e8)return'$'+(n/1e8).toFixed(1)+'억';",
         "if(n>=1e12)return'$'+(n/1e12).toFixed(2)+'T';if(n>=1e9)return'$'+(n/1e9).toFixed(1)+'B';if(n>=1e6)return'$'+(n/1e6).toFixed(1)+'M';"),
    ],
    'congress.html': [
        ("re:function usd\\(n\\)\\{if\\(n==null\\)return'';.*?'달러'\\;\\}",
         "function usd(n){if(n==null)return'';if(n>=1e9)return'$'+(+(n/1e9).toFixed(2))+'B';if(n>=1e6)return'$'+(+(n/1e6).toFixed(2))+'M';return'$'+n.toLocaleString('en-US');}"),
        ("'의원 '+new Set(recent.map(t=>t.m)).size+'명'", "new Set(recent.map(t=>t.m)).size+' members'"),
        ("['의원 수',mem.size+'명','하원 거래 신고자']", "['Members',mem.size+'','House members who filed trades']"),
        ("['읽은 신고서',c.f+'건','읽지 못한 스캔본 '+c.u+'건']", "['Filings read',c.f+'','Unreadable scans: '+c.u]"),
        ("'최근 '+META.years.length+'년 신고 기준'", "'Filings from the last '+META.years.length+' years'"),
        ("['거래 건수',ALL.length.toLocaleString('ko-KR').replace(/,/g,'')", "['Trades',ALL.length.toLocaleString('en-US')"),
        ("['최근 30일 거래',recent.length+'건',", "['Trades, last 30 days',recent.length+'',"),
        ("re:행을 누르면 최근 거래 탭에서 그 \\$\\{by===.stock.\\?.종목.:.의원.\\}의 거래를 봅니다\\.",
         "Click a row to see that ${by==='stock'?'stock':'member'}’s trades in the Recent trades tab."),
    ],
    'ipo.html': [
        ("const W=n=>won(n).replace(/,/g,''),CNT=n=>won(n).replace(/,/g,'').replace(/원$/,'주');",
         "const W=n=>n>=1e8?'₩'+(n/1e9).toFixed(2)+'B':'₩'+n.toLocaleString('en-US'),CNT=n=>n.toLocaleString('en-US')+' shares';"),
    ],
}

# ---- 한국 종목·시장·재무·계산기 영어판 (원화 표기는 ₩ + K/M/B/T) ----
_ABB = "const t=[[1e12,'T'],[1e9,'B'],[1e6,'M'],[1e3,'K']].find(x=>abs>=x[0]);const s=t?(abs/t[0]).toFixed(abs/t[0]>=100?0:abs/t[0]>=10?1:2)+t[1]:String(Math.round(abs));"

# 한국 ETF 영문 이름(longest first) — 한글 이름이 페이지 문구·코드에 섞여 있어 영어판에서는 일괄 치환
_KR_ETF = [
    ('KODEX 미국배당커버드콜액티브', 'KODEX US Dividend Covered Call Active'), ('TIGER 은행고배당플러스TOP10', 'TIGER Bank High Dividend Plus TOP10'),
    ('SOL 금융지주플러스고배당', 'SOL Financial Holdings Plus High Dividend'), ('TIGER 미국S&P500배당귀족', 'TIGER US S&P500 Dividend Aristocrats'),
    ('TIGER 리츠부동산인프라', 'TIGER REITs Real Estate Infrastructure'), ('ACE 미국빅테크TOP7 Plus', 'ACE US Big Tech TOP7 Plus'),
    ('TIGER 미국배당다우존스', 'TIGER US Dividend Dow Jones'), ('KODEX 미국배당다우존스', 'KODEX US Dividend Dow Jones'),
    ('ACE 미국배당다우존스', 'ACE US Dividend Dow Jones'), ('SOL 미국배당다우존스', 'SOL US Dividend Dow Jones'),
    ('TIGER 코스피고배당', 'TIGER KOSPI High Dividend'), ('PLUS 고배당주', 'PLUS High Dividend Stocks'),
    ('KODEX 고배당주', 'KODEX High Dividend Stocks'), ('KODEX 배당가치', 'KODEX Dividend Value'), ('RISE 고배당', 'RISE High Dividend'),
]
_KR_CAT = [(' · 국내 금융지주 고배당 · 실제', ' · Korea financial holdings high dividend · 실제'), (' · 국내 은행 고배당 · 실제', ' · Korea bank high dividend · 실제'),
           (' · 국내 고배당 · 실제', ' · Korea high dividend · 실제'), (' · 국내 배당가치 · 실제', ' · Korea dividend value · 실제'),
           (' · 국내 리츠 · 실제', ' · Korea REITs · 실제'), (' · 미국 빅테크 · 실제', ' · US big tech · 실제'),
           (' · 미국배당 커버드콜 · 실제', ' · US dividend covered call · 실제'), (' · 미국배당 · 실제', ' · US dividend · 실제')]
PATCHES['dividend-kr-*.html'] = _KR_ETF + _KR_CAT + [
    ('  · "연간 환산"은 가장 최근 분배금 × 분배 횟수(월분배=12, 분기분배=4)로 단순 추정한 값입니다<br>\n'
     '  · 분배금은 배당소득에 해당하여 국내 이자·배당소득 합계가 연 2천만원을 초과하면 금융소득종합과세 대상이 될 수 있습니다<br>\n'
     '  · 본 페이지는 분배금만 계산하며 매매차익(양도)은 계산 범위에 포함하지 않습니다\n',
     '  · “Annualized” is a simple estimate: the latest distribution × distributions per year (monthly = 12, quarterly = 4)<br>\n'
     '  · Distributions are dividend income in Korea; if interest and dividend income together exceed ₩20 million a year, comprehensive financial income taxation may apply<br>\n'
     '  · This page calculates distributions only and does not cover capital gains on sale\n'),
]
PATCHES['calc-fire-dividend.html'] = _KR_ETF + [
    ("function fmtEok(v){if(Math.abs(v)>=100000000){const eok=v/100000000;return (Math.abs(eok)>=100?eok.toFixed(0):eok.toFixed(1).replace(/\.0$/,''))+'억원';}return won(v);}",
     "function fmtEok(v){const a=Math.abs(v);if(a>=1e9)return (v<0?'-':'')+'₩'+(+(a/1e9).toFixed(2))+'B';return won(v);}"),
]
PATCHES['calc-fire.html'] = [PATCHES['calc-fire-dividend.html'][-1]]
PATCHES['kr-fin.html'] = [
    ("re:function won\(m\)\{.*?'원';\}",
     "function won(m){if(m==null)return'-';const n=m*1e6,abs=Math.abs(n);" + _ABB + "return(n<0?'-':'')+'₩'+s;}"),
    ("re:const wonp=v=>[^\n]*\n", "const wonp=v=>v==null?'-':'₩'+Math.round(v).toLocaleString('en-US');\n"),
]
PATCHES['market.html'] = [
    ("re:function bigNum\(v\)\{[^\n]*\n",
     "function bigNum(v){const n=parseFloat(v);if(isNaN(n))return'-';const abs=Math.abs(n);" + _ABB + "return(n<0?'-':'')+s;}\n"),
    ("fmt(i.value,'원',0)", "'₩'+fmt(i.value,'',0)"),
]
PATCHES['macro.html'] = [
    ("re:function krWon\(v,unit\)\{.*?원`;\}",
     "function krWon(v,unit){const n=parseFloat(v);if(isNaN(n))return'-';const abs=Math.abs(n*(WON_MULT[unit]||1));" + _ABB + "return(n<0?'-':'')+'₩'+s;}"),
    ("re:function usdEok\(v\)\{[^\n]*\n",
     "function usdEok(v){const n=parseFloat(v);if(isNaN(n))return'-';const abs=Math.abs(n);" + _ABB + "return(n<0?'-':'')+'$'+s;}\n"),
]
PATCHES['macro-detail.html'] = [
    ("re:function krWon\(v,unit\)\{[^\n]*\n",
     "function krWon(v,unit){const n=parseFloat(v);if(isNaN(n))return'-';const mult={'백만원':1e6,'십억원':1e9,'원':1}[unit]||1;const abs=Math.abs(n*mult);" + _ABB + "return(n<0?'-':'')+'₩'+s;}\n"),
    ("return (i.value/1e8).toLocaleString('ko-KR',{maximumFractionDigits:1})+'억 달러';",
     "{const abs=Math.abs(i.value);" + _ABB + "return (i.value<0?'-':'')+'$'+s;}"),
]
PATCHES['stock-detail.html'] = [
    ("((n/1e12).toFixed(1)+'조원')", "('₩'+(n/1e12).toFixed(1)+'T')"),
    ("${IS_US?'':'원'}", ""),
    ("+(IS_US?'':'원')", ""),
    ("${IS_US?'$':''}${fmt(r.close_price", "${IS_US?'$':'₩'}${fmt(r.close_price"),
    ("(IS_US?'$':'')+fmt(last.close_price", "(IS_US?'$':'₩')+fmt(last.close_price"),
    ('<span class="v">${c.fiscal_year}년</span>', '<span class="v">${c.fiscal_year}</span>'),
    ('<span class="v">${fmt((c.revenue||0)/1e8,0)}억원</span>', '<span class="v">₩${fmt((c.revenue||0)/1e9,1)}B</span>'),
    ('<span class="v">${fmt((c.operating_profit||0)/1e8,0)}억원</span>', '<span class="v">₩${fmt((c.operating_profit||0)/1e9,1)}B</span>'),
    ('<span class="v">${fmt((c.net_profit||0)/1e8,0)}억원</span>', '<span class="v">₩${fmt((c.net_profit||0)/1e9,1)}B</span>'),
    ('<span class="v">${fmt(c.eps,0)}원</span>', '<span class="v">₩${fmt(c.eps,0)}</span>'),
]
PATCHES['sim.html'] = [
    ("re:function krw\(n\)\{.*?'원';\}",
     "function krw(n){n=Math.round(n);const neg=n<0,abs=Math.abs(n);if(abs===0)return'₩0';" + _ABB + "return(neg?'-':'')+'₩'+s;}"),
]
PATCHES['calc-fx.html'] = [("+'원'", "+' KRW'")]
PATCHES['calc-lotto-sim.html'] = [("cnt[i].toLocaleString('ko-KR')+'회'", "cnt[i].toLocaleString('ko-KR')+' times'")]
PATCHES['calc-freelancer.html'] = [("'0원 (과세최저한)'", "'₩0 (below the minimum taxable threshold)'")]
PATCHES['calc-loan.html'] = [("(m==='bullet'?' (원금 포함)':'')", "(m==='bullet'?' (incl. principal)':'')")]
PATCHES['calc-salary.html'] = [("'연 환산 약 '+won(net*12)", "'About '+won(net*12)+' per year'")]
PATCHES['calc-realty.html'] = [
    ("'최대 '+won(r.fee)", "'Max '+won(r.fee)"),
    ("extra+='거래금액(환산): '+won(amount)+'<br>'", "extra+='Transaction amount (converted): '+won(amount)+'<br>'"),
    ("'적용 상한요율 '+(r.rate*100).toFixed(1)+'% · 부가세(10%) 포함 시 '+won(r.fee*1.1)", "'Rate cap applied '+(r.rate*100).toFixed(1)+'% · including VAT (10%): '+won(r.fee*1.1)"),
]
PATCHES['calc-date.html'] = [("const WD=['일','월','화','수','목','금','토'];", "const WD=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];")]

# ---- 영어 이름 검색: en-names.js 의 enLc(한글이름)로 영문명도 함께 비교 ----
_EN_Q = "r[1].toLowerCase().includes(t)||r[0].includes(t)"
_EN_Q2 = "r[1].toLowerCase().includes(t)||r[0].includes(t)||(window.enLc&&enLc(r[1]).includes(t))"
PATCHES['kr-fin.html'] += [
    (_EN_Q, _EN_Q2),
    ("const c=r[0].toLowerCase(),nm=r[1].toLowerCase();return (c===t||nm===t)?0:nm.startsWith(t)?1:2;",
     "const c=r[0].toLowerCase(),nm=r[1].toLowerCase(),en=window.enLc?enLc(r[1]):'';return (c===t||nm===t||en===t)?0:(nm.startsWith(t)||en.startsWith(t))?1:2;"),
]
PATCHES['sim.html'] = PATCHES.get('sim.html', []) + [(_EN_Q, _EN_Q2)]
PATCHES['compare.html'] += [
    ("r.name.toLowerCase().includes(t))).sort(", "r.name.toLowerCase().includes(t)||(window.enLc&&enLc(r.name).includes(t)))).sort("),
    ("const id=r.id.toLowerCase(),n=r.name.toLowerCase();return (id===t||n===t)?0:n.startsWith(t)?1:id.startsWith(t)?2:3;",
     "const id=r.id.toLowerCase(),n=r.name.toLowerCase(),en=window.enLc?enLc(r.name):'';return (id===t||n===t||en===t)?0:(n.startsWith(t)||en.startsWith(t))?1:id.startsWith(t)?2:3;"),
]
PATCHES['ipo.html'] += [("x.corp.toLowerCase().includes(Q))", "x.corp.toLowerCase().includes(Q)||(window.enLc&&enLc(x.corp).includes(Q)))")]
PATCHES['compare.html'] += [
    ("if(u.get('m')==='us'){M='us';document.querySelectorAll('#mk .tab').forEach(x=>x.classList.toggle('active',x.dataset.m==='us'));}",
     "if(u.get('m')==='kr'){M='kr';document.querySelectorAll('#mk .tab').forEach(x=>x.classList.toggle('active',x.dataset.m==='kr'));}"),
]

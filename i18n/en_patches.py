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

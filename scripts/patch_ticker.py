#!/usr/bin/env python3
"""티커바 신규 삽입 + 구버전 티커 라벨 통일 (index.html 기준) — 실행 후 삭제할 임시 스크립트"""
import glob, re, sys

TICKER_CSS = """.ticker{background:var(--bg2);border-bottom:1px solid var(--border);overflow:hidden;height:30px;display:flex;align-items:center}
.ticker-inner{display:flex;gap:28px;animation:ticker 50s linear infinite;white-space:nowrap;padding:0 16px}
@keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ti{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text2)}
.ti .name{color:var(--text);font-weight:500}
.ticker .up{color:var(--green)}.ticker .down{color:var(--red)}.ticker .neutral{color:var(--text2)}
"""
TICKER_DIV = '\n<div class="ticker"><div class="ticker-inner" id="ticker-inner"></div></div>'
# 자체완결형 (외부 fmt/sc 의존 없음), 라벨은 index.html 최신 기준
TICKER_JS = """async function loadTicker(){try{const r=await fetch('data/market.json');const d=await r.json();const inds=d.indicators||[];const L={'USD_KRW':'원달러','BASE_RATE':'기준금리','FED_RATE':'미국금리','USD_INDEX':'달러인덱스','US_YIELD_CURVE':'장단기금리차','M2_TOTAL':'M2','KOSPI':'코스피','KOSDAQ':'코스닥','US_SP500':'S&P500','US_DJIA':'다우','US_NASDAQ':'나스닥'};const tf=(v,dg)=>parseFloat(v).toLocaleString('ko-KR',{minimumFractionDigits:dg,maximumFractionDigits:dg});const tc=s=>s==='red'?'down':s==='yellow'?'neutral':'up';let h='';inds.forEach(i=>{if(!L[i.indicator_code])return;const v=i.indicator_code==='M2_TOTAL'?(i.value/1000000).toFixed(1)+'조원':tf(i.value,['%','Index','pt','USD/배럴'].includes(i.unit)?2:0)+(i.unit?' '+i.unit:'');h+=`<div class="ti"><span class="name">${L[i.indicator_code]}</span><span class="${tc(i.signal)}">${v}</span></div>`;});document.getElementById('ticker-inner').innerHTML=h+h;}catch(e){}}"""

new_cnt = upd_cnt = 0
for f in sorted(glob.glob('*.html')):
    if f == 'alerts.html':
        continue
    src = open(f, encoding='utf-8').read()
    orig = src
    if 'ticker-inner' not in src:
        # 신규 삽입: CSS, div, JS
        assert '</style>' in src and '</header>' in src and '</script>' in src, f
        src = src.replace('</style>', TICKER_CSS + '</style>', 1)
        src = src.replace('</header>', '</header>' + TICKER_DIV, 1)
        p = src.rfind('</script>')
        src = src[:p] + TICKER_JS + '\nloadTicker();\n' + src[p:]
        new_cnt += 1
    elif 'US_SP500' not in src:
        # 구버전 라벨 → 최신 자체완결형으로 정의부만 교체 (호출부 loadTicker(); 유지)
        src2 = re.sub(r'async function loadTicker\(\)\{.*', TICKER_JS.replace('\\', '\\\\'), src, count=1)
        assert src2 != src, f
        src = src2
        upd_cnt += 1
    if src != orig:
        open(f, 'w', encoding='utf-8').write(src)

print(f'신규 삽입: {new_cnt}, 라벨 교체: {upd_cnt}')
assert new_cnt == 14 and upd_cnt == 6, '대상 수 불일치'

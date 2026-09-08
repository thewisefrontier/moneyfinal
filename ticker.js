/* 사이트 공용 상단 지표 티커. data/market.json을 읽어 #ticker-inner에 렌더링.
   예전엔 페이지마다 이 스크립트가 복붙돼 있었는데, 그중 한 버전(주로 배당
   ETF 템플릿 페이지 99개)이 M2 총유동성을 값/1,000,000으로 계산해서
   "4.2조원"처럼 실제 값(약 4,210조원)의 1/1000로 표시되는 버그가 있었다
   (2026-09-06 발견, DB 단위가 "십억원"이라 올바른 환산은 값/1,000). 이
   파일로 통일하면서 올바른 계산으로 맞춤. */
async function loadTicker() {
  try {
    const r = await fetch('data/market.json');
    const d = await r.json();
    const inds = d.indicators || [];
    const L = {
      'USD_KRW': '원달러', 'BASE_RATE': '기준금리', 'FED_RATE': '미국금리',
      'USD_INDEX': '달러인덱스', 'US_YIELD_CURVE': '장단기금리차', 'M2_TOTAL': 'M2',
      'KOSPI': '코스피', 'KOSDAQ': '코스닥', 'US_SP500': 'S&P500', 'US_DJIA': '다우',
      'US_NASDAQ': '나스닥', 'VIX': 'VIX', 'WTI': 'WTI', 'GOLD': '금'
    };
    const tf = (v, dg) => parseFloat(v).toLocaleString('ko-KR', { minimumFractionDigits: dg, maximumFractionDigits: dg });
    const tc = s => s === 'red' ? 'down' : s === 'yellow' ? 'neutral' : 'up';
    let h = '';
    inds.forEach(i => {
      if (!L[i.indicator_code]) return;
      const v = i.indicator_code === 'M2_TOTAL'
        ? Math.round(i.value / 1000).toLocaleString('ko-KR') + '조원'
        : tf(i.value, ['%', 'Index', 'pt', 'USD/배럴'].includes(i.unit) ? 2 : 0) + (i.unit ? ' ' + i.unit : '');
      h += `<div class="ti"><span class="name">${L[i.indicator_code]}</span><span class="${tc(i.signal)}">${v}</span></div>`;
    });
    document.getElementById('ticker-inner').innerHTML = h + h;
  } catch (e) { }
}
loadTicker();

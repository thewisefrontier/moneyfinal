/* 사이트 공용 카테고리 nav. 여기 한 곳만 고치면 모든 페이지에 반영된다.
   각 페이지는 <nav id="site-nav" data-active="이 페이지의 href"></nav> 자리만
   두고 이 파일을 <script src="nav.js"></script>로 불러 쓴다. */
(function () {
  var LINKS = [
    ['index.html', '홈'],
    ['invest.html', '투자'],
    ['dividend-etf.html', '배당ETF'],
    ['calc-fire-dividend.html', '파이어'],
    ['rates.html', '예금·적금'],
    ['loans.html', '대출'],
    ['market.html', '시장'],
    ['jp-market.html', '일본시장'],
    ['crypto.html', '코인'],
    ['savings.html', 'ISA'],
    ['annuity.html', '연금저축'],
    ['insurance.html', '보험'],
    ['company.html', '기업정보'],
    ['kr-fin.html', '한국재무'],
    ['us-fin.html', '미국재무'],
    ['compare.html', '기업비교'],
    ['superinvestor.html', '슈퍼인베스터'],
    ['congress.html', '의원거래'],
    ['bond.html', '채권'],
    ['ipo.html', 'IPO'],
    ['sim.html', '시뮬레이터'],
    ['macro.html', '경제지표'],
    ['calc.html', '계산기']
  ];
  // 영어판(/en/): 한국 전용 메뉴를 빼고 영어 라벨. 영어판에 있는 페이지만 언어 전환 링크를 보여준다.
  var EN = document.documentElement.lang === 'en';
  var LINKS_EN = [
    ['index.html', 'Home'],
    ['dividend-etf.html', 'Dividend ETFs'],
    ['us-fin.html', 'US Financials'],
    ['compare.html', 'Compare'],
    ['superinvestor.html', 'Superinvestors'],
    ['kr-fin.html', 'Korea Financials'],
    ['congress.html', 'Congress Trades'],
    ['ipo.html', 'IPO'],
    ['market.html', 'Markets'],
    ['jp-market.html', 'Japan'],
    ['macro.html', 'Indicators'],
    ['bond.html', 'Bonds'],
    ['crypto.html', 'Crypto'],
    ['sim.html', 'Simulator'],
    ['calc.html', 'Calculators']
  ];
  var EN_ONLY = ['about', 'privacy', 'terms', 'compare', 'congress', 'dividend-etf', 'ipo', 'superinvestor', 'us-fin', 'kr-fin', 'market', 'jp-market', 'macro',
    'macro-detail', 'indicator-detail', 'stock-detail', 'company', 'bond', 'crypto', 'sim', 'calc'];
  var path = location.pathname.replace(/\.html$/, '').replace(/\/$/, '');
  var isEn = /^\/en(\/|$)/.test(path), rest = path.replace(/^\/en/, '');
  var hasEn = rest === '' || EN_ONLY.indexOf(rest.slice(1)) >= 0 || /^\/(dividend|calc)-/.test(rest);
  var navs = document.querySelectorAll('#site-nav');
  for (var i = 0; i < navs.length; i++) {
    var nav = navs[i];
    var active = nav.getAttribute('data-active');
    var html = '';
    var list = EN ? LINKS_EN : LINKS;
    for (var j = 0; j < list.length; j++) {
      var href = list[j][0], label = list[j][1];
      var to = EN ? '/en/' + (href === 'index.html' ? '' : href.replace(/\.html$/, '')) : href;
      html += '<a href="' + to + '"' + (href === active ? ' class="active"' : '') + '>' + label + '</a>';
    }
    if (hasEn) {
      html += EN ? '<a href="' + (rest || '/') + '">한국어</a>' : '<a href="/en' + (rest || '/') + '">EN</a>';
    }
    nav.innerHTML = html;
  }
})();

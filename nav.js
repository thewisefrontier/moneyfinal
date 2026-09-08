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
    ['crypto.html', '코인'],
    ['savings.html', 'ISA'],
    ['annuity.html', '연금저축'],
    ['insurance.html', '보험'],
    ['company.html', '기업정보'],
    ['macro.html', '경제지표'],
    ['calc.html', '계산기']
  ];
  var navs = document.querySelectorAll('#site-nav');
  for (var i = 0; i < navs.length; i++) {
    var nav = navs[i];
    var active = nav.getAttribute('data-active');
    var html = '';
    for (var j = 0; j < LINKS.length; j++) {
      var href = LINKS[j][0], label = LINKS[j][1];
      html += '<a href="' + href + '"' + (href === active ? ' class="active"' : '') + '>' + label + '</a>';
    }
    nav.innerHTML = html;
  }
})();

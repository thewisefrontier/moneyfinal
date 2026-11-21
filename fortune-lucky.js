/* 한국어 운세 결과의 '오늘의 행운 아이템' 블록. 상품은 data/lucky_deals.json(핫딜월드 공개 피드에서 매일 갱신)에서 읽고,
   핫딜월드 상품 상세(/deal/{id})로 슬쩍 연결한다. 한국어 페이지에서만 불러오며 영어 페이지에는 싣지 않는다.
   사용: FZ_luckyMount(요소, 테마) — 테마는 계산 번들의 luckyItem({name, emoji, reason}). 상품 데이터가 늦게 도착해도 자동으로 다시 그린다. */
(function () {
  var DEALS = null, mounts = [];
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  // 만원 미만은 콤마 없이("8250원"), 이상은 만 단위 그룹("1만2300원")
  var won = function (n) { n = Math.round(n); if (n < 10000) return n + '원'; var m = Math.floor(n / 10000), r = n % 10000; return m + '만' + (r ? r : '') + '원'; };
  function html(theme) {
    if (!theme || !theme.name) return '';
    var ds = (DEALS && DEALS[theme.name]) || [];
    var cards = ds.map(function (d) {
      var off = d.originalPrice > d.price ? Math.round((1 - d.price / d.originalPrice) * 100) : 0;
      return '<a class="fz-deal" href="https://hotdealworld.kr/deal/' + d.id + '" target="_blank" rel="noopener">' +
        (d.imageUrl ? '<img src="' + esc(d.imageUrl) + '" alt="" loading="lazy" referrerpolicy="no-referrer">' : '<span class="ph">' + esc(theme.emoji) + '</span>') +
        '<span class="t">' + esc(d.title) + '</span><span class="p">' + won(d.price) + (off >= 5 ? ' <em>' + off + '%</em>' : '') + '</span></a>';
    }).join('');
    return '<div class="fz-luckyitem"><div class="fz-li-h"><span class="e">' + esc(theme.emoji) + '</span><div><small>오늘의 행운 아이템</small><b>' + esc(theme.name) + '</b></div></div>' +
      '<p>' + esc(theme.reason) + '</p>' + (cards ? '<div class="fz-deals">' + cards + '</div><div class="fz-li-note">핫딜월드에서 지금 판매 중인 상품이에요.</div>' : '') + '</div>';
  }
  window.FZ_luckyMount = function (el, theme) {
    if (!el) return;
    mounts = mounts.filter(function (m) { return m.el.isConnected && m.el !== el; });
    mounts.push({ el: el, theme: theme });
    el.innerHTML = html(theme);
  };
  fetch('data/lucky_deals.json').then(function (r) { return r.json(); }).then(function (j) {
    DEALS = j.themes || {};
    mounts.forEach(function (m) { if (m.el.isConnected) m.el.innerHTML = html(m.theme); });
  }).catch(function () { });
})();

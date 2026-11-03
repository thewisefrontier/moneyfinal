/* 영어판 전용: 페이지에 그려진 한글 이름(한국 기업명·지표·은행명)을 data/en_names.json 사전으로 영어로 바꿔 보여준다.
   - 텍스트 노드만 바꾸고, 사전에 없는 이름은 한글 그대로 둔다.
   - 동적으로 다시 그려지는 표·목록도 MutationObserver로 따라간다. 사전 생성: scripts/build_en_names.py */
(function () {
  var HAN = /[가-힣]/, N = null, T = [], busy = false;
  function tr(s) {
    var t = s.trim();
    if (N[t]) return s.replace(t, N[t]);
    var pm = t.match(/^(.+?)우(B|\(전환\))?$/);  // 우선주: 삼성전자우 -> Samsung Electronics (preferred)
    if (pm && N[pm[1]]) return s.replace(t, N[pm[1]] + ' (preferred)');
    var o = s;
    for (var i = 0; i < T.length; i++) o = o.replace(T[i][0], T[i][1]);
    return o;
  }
  function walk(root) {
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), n, list = [];
    while ((n = w.nextNode())) { if (HAN.test(n.nodeValue)) list.push(n); }
    list.forEach(function (x) { var v = tr(x.nodeValue); if (v !== x.nodeValue) x.nodeValue = v; });
  }
  fetch('/data/en_names.json').then(function (r) { return r.json(); }).then(function (d) {
    N = d.n; T = d.t.map(function (x) { return [new RegExp(x[0], 'g'), x[1]]; });
    walk(document.body);
    new MutationObserver(function () {
      if (busy) return; busy = true;
      setTimeout(function () { busy = false; walk(document.body); }, 60);
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  }).catch(function () { });
})();

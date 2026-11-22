/* 영어 운세 표시 계층 — scripts/build_fortune_en.py가 이 템플릿의 __DATA__ 를 사전(JSON)으로 채워 fortune-en.js 를 만든다.
   계산 로직은 한국어 그대로 두고, 화면에 보일 때만 FZ.T(한국어)로 영어를 얻는다. 용어 표는 FZ.data 에 있다. */
(function () {
  var E = __DATA__;
  var MON = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var PH = /\$\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}/g;
  var TP = E.tpl.map(function (t) { return { re: new RegExp(t.re), en: t.en, ph: t.ph }; });
  function dyn(s) {  // 라이브러리가 값으로 조립하는 라벨(기간·월·주)
    var m;
    if ((m = s.match(/^(\d{4})년 (\d{1,2})월$/))) return MON[+m[2]] + ' ' + m[1];
    if ((m = s.match(/^(\d{4})년$/))) return m[1];
    if ((m = s.match(/^(\d{1,2})월$/))) return MON[+m[1]];
    if ((m = s.match(/^(\d)주$/))) return 'Wk ' + m[1];
    return null;
  }
  function tpl(s) {  // `${...}`가 든 문구: 한국어 템플릿에 맞으면 영어 템플릿의 자리표시자를 캡처 값의 번역으로 채운다
    for (var i = 0; i < TP.length; i++) {
      var m = s.match(TP[i].re);
      if (m) {
        var t = TP[i];
        return t.en.replace(PH, function (ph) {
          for (var q = 0; q < t.ph.length; q++) { if (t.ph[q][0] === ph) { var g = t.ph[q][1]; return g < 0 ? '' : T(m[g + 1]); } }
          return ph;
        }).replace(/ {2,}/g, ' ');
      }
    }
    return null;
  }
  function one(s) {
    if (E.D[s] !== undefined) return E.D[s];
    var a = tpl(s);
    return a !== null ? a : dyn(s);
  }
  function T(s) {
    if (s == null) return '';
    s = String(s);
    var t = s.trim(), a = one(t);
    if (a !== null) return a;
    var parts = t.split(/(?<=[.!?])\s+/);  // 여러 문장이 이어 붙은 문구는 문장별로
    if (parts.length > 1) return parts.map(function (p) { var x = one(p); return x === null ? p : x; }).join(' ');
    return s;
  }
  window.FZ = { T: T, data: E, missing: function (s) { return /[가-힣]/.test(T(s)); } };
})();

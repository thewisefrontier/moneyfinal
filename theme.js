/* 사이트 공용 다크/라이트 테마 + 모바일 nav 토글.
   기존엔 페이지마다 이 스크립트가 복붙돼 있었는데, about/개인정보/이용약관
   3개 페이지만 localStorage에 테마를 저장하고 나머지 128개는 저장을
   안 해서 새로고침·페이지 이동할 때마다 다크모드로 초기화되는 버그가 있었다
   (2026-09-06 발견). 이 파일로 통일하면서 저장 방식으로 맞춤. */
/* 스크롤바: 사이트 테마색(CSS 변수)을 따라가는 얇은 스크롤바. 페이지·표·자동완성 목록 등 전체에 적용.
   표준 속성(scrollbar-*)을 우선 쓰고, 지원하지 않는 구형 WebKit만 ::-webkit-scrollbar로 대체한다.
   페이지 CSS의 nav{scrollbar-width:none}처럼 요소 선택자가 있는 규칙은 이 규칙보다 우선한다. */
(function () {
  var st = document.createElement('style');
  st.textContent =
    '*{scrollbar-width:thin;scrollbar-color:var(--border) transparent}' +
    '*{scrollbar-color:color-mix(in srgb,var(--text2) 45%,transparent) transparent}' +
    '@supports not (scrollbar-color:auto){' +
    '*::-webkit-scrollbar{width:8px;height:8px}' +
    '*::-webkit-scrollbar-track{background:transparent}' +
    '*::-webkit-scrollbar-thumb{background:var(--border);border-radius:8px}' +
    '*::-webkit-scrollbar-thumb:hover{background:var(--text2)}}';
  document.head.appendChild(st);
})();

(function () {
  var saved = localStorage.getItem('theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  var btn = document.querySelector('.theme-btn');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '🌙' : '🌑';
})();

function toggleTheme() {
  var h = document.documentElement;
  var next = h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  h.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  var btn = document.querySelector('.theme-btn');
  if (btn) btn.textContent = next === 'dark' ? '🌙' : '🌑';
}

function toggleNav() {
  var n = document.querySelector('nav');
  if (n) n.classList.toggle('open');
}

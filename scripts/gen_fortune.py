"""운세 섹션 한국어 페이지 생성기 — ipo.html의 공용 head(사이트 기본 스타일)에 fortune.css를 붙이고, 페이지별 본문 템플릿을 넣는다.
실행: python scripts/gen_fortune.py  → fortune.html 등. 영어판은 build_en.py가 이 한국어 페이지에서 만든다."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://moneyfinal.pages.dev'


def head(page, title, desc):
    src = open(os.path.join(ROOT, 'ipo.html'), encoding='utf-8').read()
    h = src[:src.index('</head>')]
    h = re.sub(r'<link rel="alternate"[^>]*>\n?', '', h)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', h)
    h = h.replace(f'{SITE}/ipo', f'{SITE}/{page}')
    h = re.sub(r'(og:title|twitter:title)" content="[^"]*"', r'\1" content="' + title + ' | 머니파이널"', h)
    h = re.sub(r'(og:description|twitter:description)" content="[^"]*"', r'\1" content="' + desc + '"', h)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>',
               '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"%s","description":"%s","url":"%s/%s","inLanguage":"ko"}</script>'
               % (title, desc, SITE, page), h, flags=re.S)
    h = re.sub(r'<title>[^<]*</title>', f'<title>{title} | 머니파이널</title>', h)
    return h + '<link rel="stylesheet" href="fortune.css">\n</head>'


def shell(page, active, main, scripts=''):
    return f'''
<body class="fz-page">
<div class="ticker"><div class="ticker-inner" id="ticker-inner"></div></div>
<header><a href="index.html" class="logo">💰 머니파이널</a>
  <nav id="site-nav" data-active="{active}"></nav>
<script src="nav.js"></script>
  <div style="display:flex;gap:6px"><button class="theme-btn" onclick="toggleTheme()">🌙</button><button class="menu-btn" onclick="toggleNav()">☰</button></div></header>
<main class="fz-wrap">
{main}
</main>
<footer>© 2026 머니파이널 · 세상의 모든 재테크<br><a href="about.html">사이트 소개</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a></footer>
<script src="theme.js"></script>{scripts}<script src="ticker.js"></script>
<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "5ec3e89757844a3582c90d3524a2cead"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
'''


NOTE = '<p class="fz-note">⚠️ 운세 결과는 오락과 참고를 위한 것이며 특정 결과를 보장하지 않습니다. 중요한 결정의 근거로 삼지 마세요. 입력한 정보는 서버로 전송되지 않고 이 기기의 브라우저에서만 계산됩니다.</p>'

HUB = '''
<section class="fz-hero">
  <img src="assets/fortune/hero-room.webp" alt="등불이 켜진 조선시대 운세방에서 점괘를 살피는 젊은 역술인" width="1344" height="768" fetchpriority="high">
  <div class="fz-hero-body">
    <div class="fz-kicker">朝鮮 · 運勢房</div>
    <h1 class="fz-title">조선 역술인의 운세방</h1>
    <p class="fz-sub">저녁 등불 아래, 젊은 역술인이 오늘의 기운을 살펴 점괘를 써 드립니다. 띠별 운세, 사주, 타로를 무료로 보세요.</p>
    <a class="fz-btn" href="fortune-zodiac.html">오늘의 점괘 보기</a>
  </div>
</section>

<section class="fz-section">
  <h2 class="fz-h2">역술인의 한마디</h2>
  <div class="fz-diviner">
    <div class="fz-diviner-img"><img src="assets/fortune/diviner.webp" alt="산통을 든 젊은 역술인" width="640" height="640" loading="lazy"></div>
    <p class="fz-say">어서 오십시오, 길손이시여. 이곳은 별과 절기가 만나는 작은 운세방입니다. 오늘 하루의 기운이 궁금하시다면 아래에서 도구를 하나 골라 주십시오. 제가 두루마리에 점괘를 적어 드리겠습니다.<small>— 운세방 주인</small></p>
  </div>
</section>

<section class="fz-section">
  <h2 class="fz-h2">오늘의 도구</h2>
  <div class="fz-grid">
    <a class="fz-tool" href="fortune-zodiac.html">
      <div class="fz-tool-img"><img src="assets/fortune/tool-zodiac.webp" alt="열두 동물이 그려진 병풍" width="640" height="640" loading="lazy"></div>
      <div class="fz-tool-body"><div class="fz-tool-name">띠별 운세</div><div class="fz-tool-desc">병풍 속 열두 띠 중 내 띠를 고르면 오늘·이번 주·이번 달·올해의 운세를 바로 봅니다.</div></div>
    </a>
    <a class="fz-tool" href="fortune-saju.html">
      <div class="fz-tool-img"><img src="assets/fortune/tool-saju.webp" alt="붓과 두루마리가 놓인 낮은 책상" width="640" height="640" loading="lazy"></div>
      <div class="fz-tool-body"><div class="fz-tool-name">사주팔자</div><div class="fz-tool-desc">태어난 해·달·날·시로 네 기둥을 세워 타고난 기질과 오행의 균형을 풀어 드립니다.</div></div>
    </a>
    <a class="fz-tool" href="fortune-tarot.html">
      <div class="fz-tool-img"><img src="assets/fortune/tool-tarot.webp" alt="촛불 아래 펼쳐진 점괘 카드" width="640" height="640" loading="lazy"></div>
      <div class="fz-tool-body"><div class="fz-tool-name">타로 한 장</div><div class="fz-tool-desc">마음속 질문을 정하고 카드 한 장을 뽑아 오늘의 메시지를 확인합니다.</div></div>
    </a>
  </div>
</section>
''' + NOTE

PAGES = {
    'fortune.html': dict(title='조선 역술인의 운세방', desc='조선시대 역술인이 운영하는 운세방에서 띠별 운세, 사주팔자, 타로를 무료로 확인하세요. 입력 정보는 서버로 보내지 않습니다.',
                         active='fortune.html', main=HUB),
}

if __name__ == '__main__':
    for page, p in PAGES.items():
        open(os.path.join(ROOT, page), 'w', encoding='utf-8', newline='').write(
            head(page[:-5], p['title'], p['desc']) + shell(page[:-5], p['active'], p['main'], p.get('scripts', '')))
        print('wrote', page)

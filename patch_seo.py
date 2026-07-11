"""SEO/AdSense 준비 일괄 패치 (idempotent).

처리 대상: 모든 *.html (privacy/terms/about/alerts 제외)
- description이 없는 페이지에 기본 description 삽입
- <link rel="canonical"> + favicon
- Open Graph (og:*), Twitter Card
- JSON-LD WebPage 구조화 데이터
- footer에 privacy/terms/about 링크 추가

이미 canonical/링크가 있는 경우 각 단계 skip.
실행 후 이 파일과 임시 워크플로우는 웹 UI에서 삭제.
"""
import glob, re, sys

BASE_URL = "https://moneyfinal.pages.dev"

# description이 없는 페이지 기본값 (검색 결과 미리보기용, 최대 155자)
DEFAULT_DESC = {
    'index.html':     '세상의 모든 재테크. 공공 금융 데이터 기반 예금·적금·대출 금리 비교, 시장 지표, 재테크 계산기를 무료로 제공하는 개인 프로젝트.',
    'market.html':    '코스피·코스닥·미국 주식 시가총액 상위 종목, 지수 시세, RSI 기술 지표, 기업 재무지표를 한눈에 확인.',
    'savings.html':   'ISA 계좌 은행별 금리·수익률·가입액 비교. 절세·연금 관련 금융상품 정보를 한 곳에서.',
    'insurance.html': '실손보험 상품별 손해율과 보험료 상승률을 비교하는 참고 자료.',
    'company.html':   'DART 공시 정보, 불성실 공시, 주요사항보고 등 상장기업 공시 현황을 실시간으로 확인.',
    'macro.html':     '국내외 거시경제 지표 - 기준금리, 통화량, 환율, 채권 금리, 국제 원자재 시세를 한눈에.',
}

EXCLUDE = {'privacy.html', 'terms.html', 'about.html', 'alerts.html'}
FOOTER_LINKS = '<br><a href="about.html">사이트 소개</a> · <a href="privacy.html">개인정보처리방침</a> · <a href="terms.html">이용약관</a>'

esc = lambda s: s.replace('"', '&quot;')

pages = sorted(set(glob.glob('*.html')) - EXCLUDE)
print(f"대상 파일 {len(pages)}개")

changed = 0
for path in pages:
    src = open(path, encoding='utf-8').read()
    orig = src

    # 1) description 없는 페이지에 기본값 삽입 (viewport 다음 줄)
    if 'name="description"' not in src and path in DEFAULT_DESC:
        d = DEFAULT_DESC[path]
        src, n = re.subn(
            r'(<meta name="viewport"[^>]*>\n)',
            r'\1<meta name="description" content="' + d + '">\n',
            src, count=1
        )
        if n == 1:
            print(f'  {path}: description 추가')

    # 2) canonical + og + twitter + JSON-LD + favicon (없으면)
    if 'rel="canonical"' not in src:
        tm = re.search(r'<title>([^<]+)</title>', src)
        dm = re.search(r'name="description"\s+content="([^"]+)"', src)
        if tm and dm:
            title = tm.group(1)
            desc = dm.group(1)
            slug = path.replace('.html', '')
            url = f"{BASE_URL}/" if path == 'index.html' else f"{BASE_URL}/{slug}"
            short_name = title.split(' | ')[0]
            seo = (
                f'<link rel="canonical" href="{url}">\n'
                f'<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
                f'<meta property="og:type" content="website">\n'
                f'<meta property="og:site_name" content="머니파이널">\n'
                f'<meta property="og:locale" content="ko_KR">\n'
                f'<meta property="og:title" content="{esc(title)}">\n'
                f'<meta property="og:description" content="{esc(desc)}">\n'
                f'<meta property="og:url" content="{url}">\n'
                f'<meta name="twitter:card" content="summary">\n'
                f'<meta name="twitter:title" content="{esc(title)}">\n'
                f'<meta name="twitter:description" content="{esc(desc)}">\n'
                f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{esc(short_name)}","description":"{esc(desc)}","url":"{url}","inLanguage":"ko-KR","isPartOf":{{"@type":"WebSite","name":"머니파이널","url":"{BASE_URL}"}}}}</script>\n'
            )
            src, n = re.subn(
                r'(<meta name="description"[^>]*>\n)',
                r'\1' + seo,
                src, count=1
            )
            if n == 1:
                print(f'  {path}: canonical/og/twitter/JSON-LD 추가')

    # 3) favicon만 별도 추가 (canonical 있는데 favicon 없는 케이스 방어)
    if 'favicon.svg' not in src:
        src, n = re.subn(
            r'(<meta charset="UTF-8">\n)',
            r'\1<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n',
            src, count=1
        )
        if n == 1:
            print(f'  {path}: favicon 추가 (fallback)')

    # 4) footer에 privacy/terms/about 링크 추가 (아직 없으면)
    footer_match = re.search(r'<footer[^>]*>(.*?)</footer>', src, re.DOTALL)
    if footer_match and 'privacy.html' not in footer_match.group(1):
        src = src.replace(footer_match.group(0),
                          footer_match.group(0).replace('</footer>', FOOTER_LINKS + '</footer>'))
        print(f'  {path}: footer 링크 추가')

    if src != orig:
        open(path, 'w', encoding='utf-8').write(src)
        changed += 1

print(f'\n총 {changed}개 파일 수정 완료')
sys.exit(0)

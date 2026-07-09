"""계산기 페이지에 SEO 메타 태그 일괄 추가 (일회성).
- canonical URL
- og:* (title/description/url/type/locale/site_name)
- twitter:* (card/title/description)
- WebApplication JSON-LD
이미 canonical이 있는 파일은 건너뛴다 (idempotent).
실행 후 이 파일과 임시 워크플로우는 웹 UI에서 직접 삭제.
"""
import glob
import re
import sys

BASE_URL = "https://moneyfinal.pages.dev"

PAGES = sorted(glob.glob("calc*.html"))
print(f"대상 파일 {len(PAGES)}개: {PAGES}")

changed = 0
for path in PAGES:
    src = open(path, encoding="utf-8").read()
    if "rel=\"canonical\"" in src:
        print(f"SKIP {path} (이미 canonical 존재)")
        continue

    tm = re.search(r"<title>([^<]+)</title>", src)
    dm = re.search(r'name="description"\s+content="([^"]+)"', src)
    if not tm or not dm:
        print(f"WARN {path}: title/description 미검출, 건너뜀")
        continue
    title = tm.group(1)
    desc = dm.group(1)
    url = f"{BASE_URL}/{path.replace('.html','')}"

    def esc(s):
        return s.replace('"', '&quot;')

    seo_block = f"""<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="머니파이널">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebApplication","name":"{esc(title.split(' | ')[0])}","description":"{esc(desc)}","url":"{url}","applicationCategory":"FinanceApplication","operatingSystem":"Any","offers":{{"@type":"Offer","price":"0"}},"publisher":{{"@type":"Organization","name":"머니파이널"}}}}</script>
"""

    new_src, n = re.subn(
        r'(<meta name="description"[^>]*>\n)',
        r'\1' + seo_block,
        src,
        count=1,
    )
    if n != 1:
        print(f"WARN {path}: description 태그 위치 못 찾음, 건너뜀")
        continue

    open(path, "w", encoding="utf-8").write(new_src)
    print(f"OK   {path}")
    changed += 1

print(f"\n총 {changed}개 파일 SEO 태그 추가 완료")
sys.exit(0)

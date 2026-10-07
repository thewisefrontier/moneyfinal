"""sitemap.xml 재생성. noindex 페이지는 제외하고, lastmod는 페이지가 불러오는 data/*.json의
updated_at(없으면 기존 lastmod 유지, 신규 페이지는 오늘)을 쓴다 - 날짜를 일괄로 찍으면 Google이 lastmod를 무시함.
daily.yml에서 export 직후 실행."""
import glob, json, os, re
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://moneyfinal.pages.dev'
today = datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d')
# 신규 페이지 기본값: (changefreq, priority)
NEW = {'bond': ('daily', '0.8'), 'crypto': ('daily', '0.7'), 'superinvestor': ('monthly', '0.7'), 'dividend-kr-etf': ('weekly', '0.7')}

old = {}
sm = os.path.join(ROOT, 'sitemap.xml')
if os.path.exists(sm):
    for loc, lm, cf, pr in re.findall(r'<loc>([^<]+)</loc><lastmod>([^<]*)</lastmod><changefreq>([^<]*)</changefreq><priority>([^<]*)</priority>', open(sm, encoding='utf-8').read()):
        old[loc.replace(BASE, '').strip('/')] = (lm, cf, pr)

def json_date(html):
    ds = []
    for j in set(re.findall(r'data/([a-z_]+\.json)', html)):
        try:
            ds.append(json.load(open(os.path.join(ROOT, 'data', j), encoding='utf-8'))['updated_at'][:10])
        except Exception:
            pass
    return max(ds) if ds else None

rows = []
for p in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
    name = os.path.basename(p)[:-5]
    html = open(p, encoding='utf-8').read()
    if 'content="noindex' in html:
        continue
    lm, cf, pr = old.get(name if name != 'index' else '', (None, *NEW.get(name, ('weekly', '0.7'))))
    lm = json_date(html) or lm or today
    rows.append((name, lm, cf, pr))
rows.sort(key=lambda r: (r[0] != 'index', -float(r[3]), r[0]))
out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for name, lm, cf, pr in rows:
    loc = BASE + '/' + ('' if name == 'index' else name)
    out.append(f'  <url><loc>{loc}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq><priority>{pr}</priority></url>')
out.append('</urlset>')
open(sm, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print(f'sitemap.xml: {len(rows)} URLs')

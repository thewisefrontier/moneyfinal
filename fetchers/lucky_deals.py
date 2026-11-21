"""운세 결과의 '행운의 아이템'에 슬쩍 곁들일 핫딜월드 상품을 받아 둔다(한국어 페이지 전용).

핫딜월드 공개 피드(/api/feed, 서버 스냅샷 응답)를 페이지로 읽어, data/lucky_themes.json(핫딜월드 lib/luckyItem.ts의 테마)과
핫딜월드와 같은 규칙으로 맞춘다: 카테고리 일치 → 상품명에 keywords 포함 → excludeKeywords 제외 → 평점 높은 순·낮은 가격 순 상위 2개.
출력: data/lucky_deals.json {updated_at, themes: {테마이름: [{id,title,price,originalPrice,imageUrl}]}}. 하루 한 번만 돈다(피드 호출 수십 건).
"""
import json
import os
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = 'https://hotdealworld.kr/api/feed'
UA = {'User-Agent': 'moneyfinal-lucky-deals (+https://moneyfinal.pages.dev)'}
MAX_DEALS = 1500


def load_all():
    items, offset = [], 0
    while offset < MAX_DEALS:
        r = requests.get(FEED, params={'limit': 60, 'offset': offset}, headers=UA, timeout=30)
        r.raise_for_status()
        j = r.json()
        items += j['items']
        offset += 60
        if offset >= j['total'] or not j['items']:
            break
        time.sleep(0.3)
    return items


def match(theme, deals):
    def has(title, ks):
        return any(k.lower() in title for k in ks)
    out = [d for d in deals if d['category'] == theme['category']]
    out = [d for d in out if not theme.get('keywords') or has(d['title'].lower(), theme['keywords'])]
    out = [d for d in out if not theme.get('excludeKeywords') or not has(d['title'].lower(), theme['excludeKeywords'])]
    out.sort(key=lambda d: (-d['rating'], d['price']))
    return out[:2]


def main():
    themes = json.load(open(os.path.join(ROOT, 'data', 'lucky_themes.json'), encoding='utf-8'))
    deals = load_all()
    res = {}
    for t in themes:
        ms = match(t, deals)
        if ms:
            res[t['name']] = [{'id': d['id'], 'title': d['title'], 'price': d['price'], 'originalPrice': d['originalPrice'], 'imageUrl': d.get('imageUrl')} for d in ms]
    path = os.path.join(ROOT, 'data', 'lucky_deals.json')
    json.dump({'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d'), 'source': 'hotdealworld.kr', 'themes': res}, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'핫딜 {len(deals)}건 중 테마 {len(res)}/{len(themes)}개에 상품 연결')


if __name__ == '__main__':
    main()

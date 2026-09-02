"""
미국 시장 뉴스 수집기 (Finnhub)
출처: finnhub.io - /news?category=general (무료티어 포함)

이 테이블은 의도적으로 공개 SELECT 정책이 없다 (market_news 마이그레이션 참고).
사이트 자체 화면에는 쓰지 않고, 다른 프로젝트(뉴스파이널)가 Cloudflare Pages
Function(/api/market-news, X-Api-Key 게이트)을 통해서만 읽어가는 용도.
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FINNHUB_API_KEY', '')
BASE_URL = "https://finnhub.io/api/v1"
MAX_ITEMS = 40


def fetch_news() -> list:
    try:
        res = requests.get(f"{BASE_URL}/news", params={'category': 'general', 'token': API_KEY}, timeout=15)
        if res.status_code >= 400:
            logger.error(f"뉴스 조회 오류 HTTP {res.status_code}: {res.text[:200]}")
            return []
        data = res.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"뉴스 조회 예외: {type(e).__name__} - {e}")
        return []


def main():
    logger.info("=== 미국 시장 뉴스 수집 시작 (Finnhub) ===")
    items = fetch_news()
    if not items:
        logger.warning("수집된 뉴스 없음. 종료.")
        return

    results = []
    for it in items[:MAX_ITEMS]:
        url = it.get('url')
        headline = it.get('headline')
        if not url or not headline:
            continue
        ts = it.get('datetime')
        published_at = None
        if ts:
            try:
                published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
            except (ValueError, OSError):
                published_at = None
        results.append({
            'headline':     headline,
            'summary':      it.get('summary') or '',
            'source':       it.get('source') or '',
            'url':          url,
            'category':     it.get('category') or 'general',
            'image_url':    it.get('image') or '',
            'published_at': published_at,
            'fetched_at':   now_kst()
        })

    if results:
        supabase_upsert('market_news', results)
        logger.info(f"✅ 시장 뉴스 {len(results)}건 저장")
    logger.info("=== 미국 시장 뉴스 수집 완료 ===")


if __name__ == '__main__': main()

"""
금융시장동향 수집기
출처: 금융감독원 오픈API (fmtInfo.jsp)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, fss_open_api_get

logger = logging.getLogger(__name__)
AUTH_KEY = os.environ.get('FSS_API_KEY', '')

def main():
    logger.info("=== 금융시장동향 수집 시작 ===")
    try:
        res = fss_open_api_get('fnncMrkt', AUTH_KEY, days_back=14)
        res.raise_for_status()
        data = res.json()
        items = data.get('result', {}).get('list', []) if isinstance(data, dict) else []
        if not items:
            logger.warning("금융시장동향: 데이터 없음")
            return
        results = []
        for item in items:
            results.append({
                'category': '금융시장동향',
                'title': item.get('title', item.get('TITLE', '')),
                'content_summary': item.get('cn', item.get('CN', ''))[:500],
                'post_date': item.get('regDate', item.get('REG_DATE', now_kst()[:10])),
                'source_url': item.get('url', item.get('URL', '')),
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('fss_news', results)
            logger.info(f"✅ 금융시장동향 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"금융시장동향 수집 오류: {type(e).__name__} - {e}")
    logger.info("=== 금융시장동향 수집 완료 ===")

if __name__ == '__main__': main()

"""
금융권 일자리정보 수집기
출처: 금융감독원 오픈API (recrtInfo.jsp)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, fss_open_api_get

logger = logging.getLogger(__name__)
AUTH_KEY = os.environ.get('FSS_API_KEY', '')

def main():
    logger.info("=== 금융권 일자리정보 수집 시작 ===")
    try:
        res = fss_open_api_get('recrtInfo', AUTH_KEY, days_back=30)
        res.raise_for_status()
        data = res.json()
        items = data.get('result', {}).get('list', []) if isinstance(data, dict) else []
        if not items:
            logger.warning("일자리정보: 데이터 없음")
            return
        results = []
        for item in items:
            results.append({
                'company_name': item.get('orgnNm', item.get('ORGN_NM', '')),
                'title': item.get('title', item.get('TITLE', '')),
                'post_date': item.get('regDate', item.get('REG_DATE', now_kst()[:10])),
                'deadline_date': item.get('endDate', item.get('END_DATE', None)),
                'source_url': item.get('url', item.get('URL', '')),
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('fss_jobs', results)
            logger.info(f"✅ 일자리정보 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"일자리정보 수집 오류: {type(e).__name__} - {e}")
    logger.info("=== 금융권 일자리정보 수집 완료 ===")

if __name__ == '__main__': main()

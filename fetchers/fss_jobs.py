"""
금융권 일자리정보 수집기
출처: 금융감독원 오픈API (recruitInfo.jsp)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, fss_open_api_get

logger = logging.getLogger(__name__)
AUTH_KEY = os.environ.get('FSS_API_KEY', '')

def main():
    logger.info("=== 금융권 일자리정보 수집 시작 ===")
    try:
        res = fss_open_api_get('recruitInfo', AUTH_KEY, days_back=30)
        res.raise_for_status()
        data = res.json()
        # 주의: FSS 응답 키는 "response"가 아니라 오타난 "reponse"
        items = data.get('reponse', {}).get('result', []) if isinstance(data, dict) else []
        if not items:
            logger.warning("일자리정보: 데이터 없음")
            return
        results = []
        for item in items:
            results.append({
                'company_name': item.get('instNm', ''),
                'title': item.get('titl', ''),
                'post_date': item.get('recpStrtDay', now_kst()[:10]),
                'deadline_date': item.get('recpEndDay') or None,
                'source_url': item.get('originUrl', ''),
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('fss_jobs', results)
            logger.info(f"✅ 일자리정보 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"일자리정보 수집 오류: {type(e).__name__} - {e}")
    logger.info("=== 금융권 일자리정보 수집 완료 ===")

if __name__ == '__main__': main()

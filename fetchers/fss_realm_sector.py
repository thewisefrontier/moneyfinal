"""
분야별 감독제도 수집기
출처: 금융감독원 오픈API (fealmMng.jsp)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, fss_open_api_get

logger = logging.getLogger(__name__)
AUTH_KEY = os.environ.get('FSS_API_KEY', '')

def main():
    logger.info("=== 분야별 감독제도 수집 시작 ===")
    try:
        res = fss_open_api_get('fealmMng', AUTH_KEY, days_back=30)
        res.raise_for_status()
        data = res.json()
        # 주의: FSS 응답 키는 "response"가 아니라 오타난 "reponse"
        items = data.get('reponse', {}).get('result', []) if isinstance(data, dict) else []
        if not items:
            logger.warning("분야별감독제도: 데이터 없음")
            return
        results = []
        for item in items:
            results.append({
                'category': '분야별감독제도',
                'title': item.get('subject', ''),
                'content_summary': item.get('contentKor', '')[:500],
                'post_date': item.get('regDate', now_kst()[:10])[:10],
                'source_url': item.get('originUrl', ''),
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('fss_news', results)
            logger.info(f"✅ 분야별감독제도 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"분야별감독제도 수집 오류: {type(e).__name__} - {e}")
    logger.info("=== 분야별 감독제도 수집 완료 ===")

if __name__ == '__main__': main()

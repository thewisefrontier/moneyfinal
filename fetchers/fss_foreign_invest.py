"""
외국인 국내투자동향 수집기
출처: 금융감독원 오픈API (invtTrend.jsp)
실측 확인: 국가별 투자금액을 주는 수치형 API가 아니라, 다른 fss_* API들과 동일한
게시판형(제목/본문/첨부파일 URL) 응답이다 (월간 동향 게시글). 원래 코드는
natnNm/amt 필드로 시장지표(market_indicators)에 저장하도록 짜여 있었으나
그런 필드 자체가 존재하지 않아 항상 0건이었음 - fss_press.py 등과 동일한
fss_news 게시판 패턴으로 재작성.
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, fss_open_api_get

logger = logging.getLogger(__name__)
AUTH_KEY = os.environ.get('FSS_API_KEY', '')

def main():
    logger.info("=== 외국인 국내투자동향 수집 시작 ===")
    try:
        res = fss_open_api_get('invtTrend', AUTH_KEY, days_back=30)
        res.raise_for_status()
        data = res.json()
        # 주의: FSS 응답 키는 "response"가 아니라 오타난 "reponse"
        items = data.get('reponse', {}).get('result', []) if isinstance(data, dict) else []
        if not items:
            logger.warning("외국인투자동향: 데이터 없음")
            return
        results = []
        for item in items:
            results.append({
                'category': '외국인국내투자동향',
                'title': item.get('subject', ''),
                'content_summary': item.get('contentKor', '')[:500],
                'post_date': item.get('regDate', now_kst()[:10])[:10],
                'source_url': item.get('originUrl', ''),
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('fss_news', results)
            logger.info(f"✅ 외국인투자동향 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"외국인투자동향 수집 오류: {type(e).__name__} - {e}")
    logger.info("=== 외국인 국내투자동향 수집 완료 ===")

if __name__ == '__main__': main()

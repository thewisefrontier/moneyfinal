"""
외국인 국내투자동향 수집기
출처: 금융감독원 오픈API (frnInvInfo.jsp)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, fss_open_api_get

logger = logging.getLogger(__name__)
AUTH_KEY = os.environ.get('FSS_API_KEY', '')

def main():
    logger.info("=== 외국인 국내투자동향 수집 시작 ===")
    try:
        res = fss_open_api_get('frnInvInfo', AUTH_KEY, days_back=30)
        res.raise_for_status()
        data = res.json()
        items = data.get('result', {}).get('list', []) if isinstance(data, dict) else []
        if not items:
            logger.warning("외국인투자동향: 데이터 없음")
            return
        results = []
        for item in items:
            results.append({
                'indicator_code': f"FRN_INV_{item.get('natnNm', item.get('NATN_NM',''))[:15]}",
                'indicator_name': f"외국인투자 {item.get('natnNm', item.get('NATN_NM',''))}",
                'category': '외국인국내투자',
                'value': float(item.get('amt', item.get('AMT', 0)) or 0),
                'unit': '백만달러',
                'signal': 'green',
                'source': '금융감독원 오픈API',
                'reference_date': today_kst(),
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('market_indicators', results)
            logger.info(f"✅ 외국인투자동향 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"외국인투자동향 수집 오류: {type(e).__name__} - {e}")
    logger.info("=== 외국인 국내투자동향 수집 완료 ===")

if __name__ == '__main__': main()

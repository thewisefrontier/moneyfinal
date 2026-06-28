"""
외국인직접투자(FDI) 통계 수집기
- 대한무역투자진흥공사_한국산업별외국인직접투자통계 (공공데이터포털)
"""
import logging, requests, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/B553718/KOTRA_FDI_INDUSTRY_STAT"


def fetch_fdi() -> list:
    url = f"{BASE_URL}/getFdiIndustryStat"
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 20,
        'pageNo': 1,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning("FDI 통계: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            results.append({
                'indicator_code': f"FDI_{item.get('indutyNm','').replace(' ','_')[:20]}",
                'indicator_name': f"외국인투자 {item.get('indutyNm','')}",
                'category': '외국인직접투자',
                'value': float(item.get('fdiAmt', 0) or 0),
                'unit': '백만달러',
                'signal': 'green',
                'source': '대한무역투자진흥공사 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"FDI 통계 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 외국인직접투자 통계 수집 시작 ===")
    results = fetch_fdi()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ FDI 통계 {len(results)}건 저장")
    logger.info("=== FDI 통계 수집 완료 ===")


if __name__ == '__main__':
    main()

"""
금융통계 국내은행 정보 수집기
- 금융위원회_금융통계국내은행정보 (공공데이터포털)
- NIM, 수익성, 건전성 지표
"""
import logging, requests, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetFinancialStatsDomBankInfoService"


def fetch_bank_stats() -> list:
    url = f"{BASE_URL}/getFinancialStatsDomBankInfo"
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 50,
        'pageNo': 1,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning("국내은행통계: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            results.append({
                'indicator_code': f"BANK_{item.get('sttsItemNm','').replace(' ','_')[:20]}",
                'indicator_name': item.get('sttsItemNm', ''),
                'category': '은행통계',
                'value': float(item.get('sttsVl', 0) or 0),
                'unit': item.get('untNm', ''),
                'signal': 'green',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"국내은행통계 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 금융통계 국내은행 수집 시작 ===")
    results = fetch_bank_stats()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 국내은행통계 {len(results)}건 저장")
    logger.info("=== 금융통계 국내은행 수집 완료 ===")


if __name__ == '__main__':
    main()

"""
국제거래 종목 정보 수집기
- 금융위원회_국제거래종목정보 (공공데이터포털)
"""
import logging, requests, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetIntlTradingItemInfoService"


def fetch_intl_stocks() -> list:
    url = f"{BASE_URL}/getIntlTradingItemInfo"
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 100,
        'pageNo': 1,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning("국제거래종목: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            results.append({
                'stock_code': item.get('isinCd', ''),
                'stock_name': item.get('itmsNm', ''),
                'market_type': '해외',
                'industry': item.get('natnNm', ''),
                'corp_name': item.get('itmsNm', ''),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"국제거래종목 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 국제거래 종목 수집 시작 ===")
    results = fetch_intl_stocks()
    if results:
        supabase_upsert('stocks', results)
        logger.info(f"✅ 국제거래종목 {len(results)}건 저장")
    logger.info("=== 국제거래 종목 수집 완료 ===")


if __name__ == '__main__':
    main()

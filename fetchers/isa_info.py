"""
ISA 다모아 정보 수집기
- 금융위원회_ISA다모아정보 (공공데이터포털)
"""
import logging, requests, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetIsaProductInfoService"


def fetch_isa_products() -> list:
    """ISA 상품 정보 수집"""
    url = f"{BASE_URL}/getIsaProductInfo"
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
            logger.warning("ISA 상품: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            results.append({
                'indicator_code': f"ISA_{item.get('prdtNm','').replace(' ','_')[:20]}",
                'indicator_name': f"ISA {item.get('prdtNm', '')}",
                'category': 'ISA',
                'value': float(item.get('erngRt', 0) or 0),
                'unit': '%',
                'signal': 'green',
                'source': '금융위원회 ISA다모아 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{item.get('fncoNm','')} {item.get('prdtNm','')}",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"ISA 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== ISA 정보 수집 시작 ===")
    results = fetch_isa_products()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ ISA 상품 {len(results)}건 저장")
    logger.info("=== ISA 정보 수집 완료 ===")


if __name__ == '__main__':
    main()

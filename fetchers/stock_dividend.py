"""
주식 배당 정보 수집기
- 금융위원회_주식배당정보 (공공데이터포털)
"""
import logging, requests, os, sys
from datetime import datetime
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockDividendInfoService"


def fetch_dividends() -> list:
    url = f"{BASE_URL}/getStockDividendInfo"
    now = datetime.now(KST)
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 100,
        'pageNo': 1,
        'basDt': now.strftime('%Y%m%d'),
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning("배당정보: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            base_dt = item.get('basDt', '')
            results.append({
                'stock_code': item.get('srtnCd', ''),
                'stock_name': item.get('itmsNm', ''),
                'base_date': f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:8]}" if len(base_dt) == 8 else today_kst(),
                'dps': float(item.get('dps', 0) or 0),
                'dividend_type': item.get('dvdnKindNm', '현금'),
                'fiscal_year': int(item.get('bizYear', 0) or 0),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"배당정보 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 주식 배당정보 수집 시작 ===")
    results = fetch_dividends()
    if results:
        supabase_upsert('stock_dividends', results)
        logger.info(f"✅ 배당정보 {len(results)}건 저장")
    logger.info("=== 주식 배당정보 수집 완료 ===")


if __name__ == '__main__':
    main()

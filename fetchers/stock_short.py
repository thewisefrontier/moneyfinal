"""
주식 대차(공매도) 정보 수집기
- 금융위원회_주식대차정보 (공공데이터포털)
"""
import logging, requests, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockLendingInfoService"


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_short_data(base_date: str) -> list:
    url = f"{BASE_URL}/getStockLendingInfo"
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 100,
        'pageNo': 1,
        'basDt': base_date,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"대차정보 {base_date}: 데이터 없음")
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
                'short_volume': int(item.get('lendBalQty', 0) or 0),
                'short_amount': int(item.get('lendBalAmt', 0) or 0),
                'short_ratio': float(item.get('lendBalQtyRto', 0) or 0),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"대차정보 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 주식 대차정보 수집 시작 ===")
    base_date = get_base_date()
    results = fetch_short_data(base_date)
    if results:
        supabase_upsert('stock_short', results)
        logger.info(f"✅ 대차정보 {len(results)}건 저장")
    logger.info("=== 주식 대차정보 수집 완료 ===")


if __name__ == '__main__':
    main()

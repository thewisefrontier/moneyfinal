"""
주식 발행 정보 수집기 (유상증자 등)
- 금융위원회_주식발행정보 (공공데이터포털)
"""
import logging, requests, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockIssuanceInfoService"


def fetch_issuance() -> list:
    url = f"{BASE_URL}/getStockIssuanceInfo"
    now = datetime.now(KST)
    begin = (now - timedelta(days=30)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 100,
        'pageNo': 1,
        'beginBasDt': begin,
        'endBasDt': end,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning("주식발행: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            dt = item.get('basDt', '')
            results.append({
                'stock_code': item.get('srtnCd', ''),
                'corp_name': item.get('corpNm', ''),
                'issuance_date': f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}" if len(dt) == 8 else today_kst(),
                'issuance_type': item.get('issuKindNm', ''),
                'issuance_price': float(item.get('issuPrc', 0) or 0),
                'issuance_quantity': int(item.get('issuQty', 0) or 0),
                'purpose': item.get('issuPurpNm', ''),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"주식발행 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 주식 발행정보 수집 시작 ===")
    results = fetch_issuance()
    if results:
        supabase_upsert('stock_issuance', results)
        logger.info(f"✅ 발행정보 {len(results)}건 저장")
    logger.info("=== 주식 발행정보 수집 완료 ===")


if __name__ == '__main__':
    main()

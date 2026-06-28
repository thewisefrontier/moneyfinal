"""
파생상품 시세 정보 수집기
- 금융위원회_파생상품시세정보 (공공데이터포털)
"""
import logging, requests, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetDerivativeProductInfoService"


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_derivatives(base_date: str) -> list:
    url = f"{BASE_URL}/getDerivativeProductInfo"
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 20,
        'pageNo': 1,
        'basDt': base_date,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"파생상품 {base_date}: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        results = []
        for item in items:
            results.append({
                'indicator_code': f"DERIV_{item.get('isinCd','')[:15]}",
                'indicator_name': item.get('itmsNm', ''),
                'category': '파생상품',
                'value': float(item.get('clpr', 0) or 0),
                'prev_value': float(item.get('vs', 0) or 0),
                'unit': 'pt',
                'signal': 'green',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"파생상품 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 파생상품 시세 수집 시작 ===")
    base_date = get_base_date()
    results = fetch_derivatives(base_date)
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 파생상품 {len(results)}건 저장")
    logger.info("=== 파생상품 시세 수집 완료 ===")


if __name__ == '__main__':
    main()

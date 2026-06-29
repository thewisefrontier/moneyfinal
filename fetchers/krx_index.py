"""
KRX 주식 지수 수집기
- 공공데이터포털 금융위원회_지수시세정보 API
- KOSPI, KOSDAQ, KOSPI200 지수 시세
출처: data.go.kr
"""
import logging
import os
import sys
from datetime import datetime, timedelta
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')

BASE_URL = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"

INDICES = [
    {'idxNm': '코스피',    'indicator_code': 'KOSPI',    'indicator_name': '코스피 지수'},
    {'idxNm': '코스닥',    'indicator_code': 'KOSDAQ',   'indicator_name': '코스닥 지수'},
    {'idxNm': '코스피 200','indicator_code': 'KOSPI200', 'indicator_name': '코스피 200'},
]


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_index(index: dict, base_date: str) -> dict | None:
    params = {
        'resultType': 'json',
        'numOfRows': 1,
        'pageNo': 1,
        'basDt': base_date,
        'idxNm': index['idxNm'],
    }
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"{index['idxNm']}: 데이터 없음")
            return None
        items = body.get('items', {}).get('item', [])
        if not items:
            return None
        item = items[0] if isinstance(items, list) else items
        value = float(item.get('clpr', 0) or 0)
        vs = float(item.get('vs', 0) or 0)
        flt_rt = float(item.get('fltRt', 0) or 0)
        signal = 'red' if flt_rt <= -3 else 'yellow' if flt_rt <= -1 else 'green'
        return {
            'indicator_code': index['indicator_code'],
            'indicator_name': index['indicator_name'],
            'category': '주식지수',
            'value': value,
            'prev_value': round(value - vs, 2),
            'unit': 'pt',
            'signal': signal,
            'source': '금융위원회 (공공데이터포털)',
            'reference_date': today_kst(),
            'summary_text': f"{index['idxNm']} {value:.2f}pt ({flt_rt:+.2f}%)",
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"{index['idxNm']} HTTP 오류: {e}")
        return None


def main():
    logger.info("=== KRX 지수 수집 시작 ===")
    base_date = get_base_date()
    logger.info(f"기준일: {base_date}")
    results = []
    for index in INDICES:
        result = fetch_index(index, base_date)
        if result:
            results.append(result)
            logger.info(f"✅ {index['idxNm']}: {result['value']}pt")
        else:
            logger.warning(f"❌ {index['idxNm']}: 수집 실패")
    if results:
        supabase_upsert('market_indicators', results)
    logger.info(f"=== KRX 수집 완료: {len(results)}/{len(INDICES)}건 ===")


if __name__ == '__main__':
    main()

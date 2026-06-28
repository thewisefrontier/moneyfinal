"""
KRX 주식 지수 수집기
- 공공데이터포털 금융위원회_지수시세정보 API
- KOSPI, KOSDAQ 지수 시세
출처: data.go.kr
"""
import logging
import requests
import os
import sys
from datetime import datetime, timedelta
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
KRX_API_KEY = os.environ.get('KRX_API_KEY', os.environ.get('FSS_API_KEY', ''))
KST = pytz.timezone('Asia/Seoul')

# 공공데이터포털 지수시세정보 API
BASE_URL = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"

# 수집할 지수 목록
INDICES = [
    {'isin': 'KRX300', 'name': '코스피', 'code': 'KOSPI'},
    {'isin': 'KOSDAQ', 'name': '코스닥', 'code': 'KOSDAQ'},
]


def fetch_index(index: dict, base_date: str) -> dict | None:
    params = {
        'serviceKey': KRX_API_KEY,
        'resultType': 'json',
        'basDt': base_date,
        'idxNm': index['name'],
        'numOfRows': 1,
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()

        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        if not items:
            logger.warning(f"{index['name']}: 데이터 없음")
            return None

        item = items[0] if isinstance(items, list) else items
        value = float(item.get('clpr', 0) or 0)
        prev = float(item.get('vs', 0) or 0)
        change_rate = float(item.get('fltRt', 0) or 0)

        signal = 'green'
        if change_rate <= -3:
            signal = 'red'
        elif change_rate <= -1:
            signal = 'yellow'
        elif change_rate >= 1:
            signal = 'green'

        return {
            'indicator_code': index['code'],
            'indicator_name': index['name'] + ' 지수',
            'category': '주식지수',
            'value': value,
            'prev_value': value - prev,
            'unit': 'pt',
            'signal': signal,
            'source': '한국거래소 KRX',
            'reference_date': today_kst(),
            'summary_text': f"{index['name']} {value:.2f}pt ({change_rate:+.2f}%)",
            'fetched_at': now_kst()
        }

    except Exception as e:
        logger.error(f"{index['name']} 수집 오류: {type(e).__name__}")
        return None


def main():
    logger.info("=== KRX 지수 수집 시작 ===")

    now = datetime.now(pytz.timezone('Asia/Seoul'))
    # 주말이면 금요일로
    if now.weekday() == 5:  # 토
        base_date = (now - timedelta(days=1)).strftime('%Y%m%d')
    elif now.weekday() == 6:  # 일
        base_date = (now - timedelta(days=2)).strftime('%Y%m%d')
    else:
        base_date = now.strftime('%Y%m%d')

    logger.info(f"기준일: {base_date}")
    results = []

    for index in INDICES:
        result = fetch_index(index, base_date)
        if result:
            results.append(result)
            logger.info(f"✅ {index['name']}: {result['value']}pt")
        else:
            logger.warning(f"❌ {index['name']}: 수집 실패")

    if results:
        supabase_upsert('market_indicators', results)

    logger.info(f"=== KRX 수집 완료: {len(results)}/{len(INDICES)}건 ===")


if __name__ == '__main__':
    main()

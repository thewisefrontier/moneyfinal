"""
FRED (미국 연준) 글로벌 지표 수집기
- 미국 기준금리, CPI, 달러 인덱스 등
- 출처: fred.stlouisfed.org
"""
import logging
import requests
import os
import sys
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)

FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# 수집할 FRED 시리즈
SERIES = [
    {
        'series_id': 'FEDFUNDS',
        'indicator_code': 'FED_RATE',
        'indicator_name': '미국 기준금리 (Fed Funds Rate)',
        'unit': '%',
        'category': '금리'
    },
    {
        'series_id': 'CPIAUCSL',
        'indicator_code': 'US_CPI',
        'indicator_name': '미국 소비자물가지수 (CPI)',
        'unit': 'Index',
        'category': '물가'
    },
    {
        'series_id': 'DTWEXBGS',
        'indicator_code': 'USD_INDEX',
        'indicator_name': '달러 인덱스',
        'unit': 'Index',
        'category': '환율'
    },
    {
        'series_id': 'T10Y2Y',
        'indicator_code': 'US_YIELD_CURVE',
        'indicator_name': '미국 장단기 금리차 (10Y-2Y)',
        'unit': '%',
        'category': '금리'
    },
]


def fetch_fred_series(series: dict) -> dict | None:
    """FRED 시리즈 최신값 수집"""
    today = datetime.utcnow()
    start = (today - timedelta(days=60)).strftime('%Y-%m-%d')
    end = today.strftime('%Y-%m-%d')

    params = {
        'series_id': series['series_id'],
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start,
        'observation_end': end,
        'sort_order': 'desc',
        'limit': 2
    }

    try:
        res = requests.get(FRED_BASE_URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()

        observations = data.get('observations', [])
        # 유효한 값만 필터
        valid = [o for o in observations if o.get('value') != '.']

        if not valid:
            logger.warning(f"{series['indicator_name']}: 유효 데이터 없음")
            return None

        latest = valid[0]
        prev = valid[1] if len(valid) >= 2 else None

        value = float(latest['value'])
        prev_value = float(prev['value']) if prev else None

        # 신호등 판단
        signal = 'green'
        if series['indicator_code'] == 'FED_RATE':
            if value >= 5.0:
                signal = 'red'
            elif value >= 4.0:
                signal = 'yellow'
        elif series['indicator_code'] == 'US_YIELD_CURVE':
            if value < 0:
                signal = 'red'  # 장단기 역전 = 경기침체 신호
            elif value < 0.5:
                signal = 'yellow'

        return {
            'indicator_code': series['indicator_code'],
            'indicator_name': series['indicator_name'],
            'category': series['category'],
            'value': value,
            'prev_value': prev_value,
            'unit': series['unit'],
            'signal': signal,
            'source': 'FRED (미국 연준)',
            'reference_date': latest['date'],
            'fetched_at': now_kst()
        }

    except Exception as e:
        logger.error(f"{series['indicator_name']} 수집 오류: {e}")
        return None


def main():
    logger.info("=== FRED 글로벌 지표 수집 시작 ===")
    results = []

    for series in SERIES:
        result = fetch_fred_series(series)
        if result:
            results.append(result)
            logger.info(f"✅ {series['indicator_name']}: {result['value']} {series['unit']}")
        else:
            logger.warning(f"❌ {series['indicator_name']}: 수집 실패")

    if results:
        supabase_upsert('market_indicators', results)

    logger.info(f"=== FRED 수집 완료: {len(results)}/{len(SERIES)}건 ===")


if __name__ == '__main__':
    main()

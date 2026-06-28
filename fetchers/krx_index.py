"""
KRX 주식 지수 수집기
- 공공데이터포털 금융위원회_지수시세정보 API
- KOSPI, KOSDAQ 지수 시세
출처: data.go.kr
주의: 데이터 갱신은 영업일 기준 익일 오후 1시 이후
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

BASE_URL = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"

INDICES = [
    {'idxNm': '코스피', 'indicator_code': 'KOSPI', 'indicator_name': '코스피 지수'},
    {'idxNm': '코스닥', 'indicator_code': 'KOSDAQ', 'indicator_name': '코스닥 지수'},
    {'idxNm': '코스피 200', 'indicator_code': 'KOSPI200', 'indicator_name': '코스피 200'},
]


def get_base_date() -> str:
    """영업일 기준 조회 날짜 계산 (전 영업일)"""
    now = datetime.now(KST)
    # 오늘이 월요일이면 금요일, 일요일이면 금요일, 토요일이면 금요일
    if now.weekday() == 0:  # 월
        base = now - timedelta(days=3)
    elif now.weekday() == 6:  # 일
        base = now - timedelta(days=2)
    elif now.weekday() == 5:  # 토
        base = now - timedelta(days=1)
    else:
        base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_index(index: dict, base_date: str) -> dict | None:
    params = {
        'serviceKey': KRX_API_KEY,
        'resultType': 'json',
        'numOfRows': 1,
        'pageNo': 1,
        'basDt': base_date,
        'idxNm': index['idxNm'],
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()

        # 응답 구조: response.body.items.item
        body = data.get('response', {}).get('body', {})
        total = body.get('totalCount', 0)

        if not total or total == 0:
            logger.warning(f"{index['idxNm']}: 데이터 없음 (totalCount=0, 영업일 데이터 미갱신)")
            return None

        items = body.get('items', {}).get('item', [])
        if not items:
            logger.warning(f"{index['idxNm']}: items 비어있음")
            return None

        item = items[0] if isinstance(items, list) else items

        value = float(item.get('clpr', 0) or 0)
        vs = float(item.get('vs', 0) or 0)
        flt_rt = float(item.get('fltRt', 0) or 0)

        signal = 'green'
        if flt_rt <= -3:
            signal = 'red'
        elif flt_rt <= -1:
            signal = 'yellow'

        return {
            'indicator_code': index['indicator_code'],
            'indicator_name': index['indicator_name'],
            'category': '주식지수',
            'value': value,
            'prev_value': round(value - vs, 2),
            'unit': 'pt',
            'signal': signal,
            'source': '한국거래소 KRX (공공데이터포털)',
            'reference_date': today_kst(),
            'summary_text': f"{index['idxNm']} {value:.2f}pt ({flt_rt:+.2f}%)",
            'fetched_at': now_kst()
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"{index['idxNm']} HTTP 오류: {e.response.status_code} - {e.response.text[:300]}")
        return None
    except Exception as e:
        logger.error(f"{index['idxNm']} 수집 오류: {type(e).__name__} - {e}")
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
            logger.info(f"✅ {index['idxNm']}: {result['value']}pt ({result['summary_text']})")
        else:
            logger.warning(f"❌ {index['idxNm']}: 수집 실패")

    if results:
        supabase_upsert('market_indicators', results)

    logger.info(f"=== KRX 수집 완료: {len(results)}/{len(INDICES)}건 ===")


if __name__ == '__main__':
    main()

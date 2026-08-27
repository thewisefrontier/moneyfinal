"""
한국은행 ECOS API - 기준금리
출처: https://ecos.bok.or.kr
매주 실행 (금통위 회의일을 하드코딩해서 그 앞뒤로만 돌리면 임시회의·일정변경
시 다음 발표까지 갱신이 끊기는 문제가 있어, 일정을 추정하지 않는 방식으로 변경)
"""
import logging
import requests
import os
import sys
from datetime import datetime, timedelta
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, has_recent_data

logger = logging.getLogger(__name__)
ECOS_API_KEY = os.environ.get('ECOS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')

INDICATOR = {
    'stat_code': '722Y001',
    'cycle': 'D',
    'item_code': '0101000',
    'indicator_code': 'BASE_RATE',
    'indicator_name': '한국은행 기준금리',
    'unit': '%',
    'category': '금리',
    'start_days': 30
}


def fetch_ecos_stat(indicator: dict):
    now = datetime.now(KST)
    days = indicator.get('start_days', 90)
    cycle = indicator['cycle']
    start = (now - timedelta(days=days)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')

    # ECOS는 조회기간 내 데이터를 오래된 순으로 반환하므로, 행 구간(1/N)이
    # 실제 건수보다 작으면 rows[-1]이 "최신값"이 아니라 그 구간 안에서 가장
    # 오래된 쪽의 값이 된다. start_days=30 + 일별(D) 주기 조합에서 구간을
    # 1/10으로 뒀다가 기준금리가 항상 ~20영업일 전 값으로 고정되는 버그가 있었음
    # (2026-07-28 인상분을 8/27까지 못 잡음). 여유 있게 크게 잡아 항상 전체를 받는다.
    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch"
        f"/{ECOS_API_KEY}/json/kr/1/1000"
        f"/{indicator['stat_code']}/{cycle}"
        f"/{start}/{end}/{indicator['item_code']}"
    )

    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()

        if 'RESULT' in data:
            logger.warning(f"{indicator['indicator_name']}: API 오류 - {data['RESULT'].get('MESSAGE','')}")
            return None

        rows = data.get('StatisticSearch', {}).get('row', [])
        valid = [r for r in rows if r.get('DATA_VALUE') and r['DATA_VALUE'] not in ('0', '', None)]
        if not valid:
            logger.warning(f"{indicator['indicator_name']}: 유효 데이터 없음")
            return None

        latest = valid[-1]
        prev = valid[-2] if len(valid) >= 2 else None
        value = float(latest.get('DATA_VALUE', 0) or 0)
        prev_value = float(prev.get('DATA_VALUE', 0) or 0) if prev else None

        signal = 'green'
        if value >= 3.5:
            signal = 'red'
        elif value >= 2.5:
            signal = 'yellow'

        return {
            'indicator_code': indicator['indicator_code'],
            'indicator_name': indicator['indicator_name'],
            'category': indicator['category'],
            'value': value,
            'prev_value': prev_value,
            'unit': indicator['unit'],
            'signal': signal,
            'source': '한국은행 ECOS',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        }

    except Exception as e:
        logger.error(f"{indicator['indicator_name']} 수집 오류: {type(e).__name__}")
        return None


def main():
    logger.info("=== ECOS 기준금리 수집 시작 ===")
    if has_recent_data('market_indicators', {'indicator_code': 'eq.BASE_RATE'}, 'reference_date', 5):
        logger.info("최근 5일 내 수집 완료 - 스킵 (매주 크론이라 중복 방지)")
        return
    result = fetch_ecos_stat(INDICATOR)
    if result:
        logger.info(f"✅ {INDICATOR['indicator_name']}: {result['value']} {INDICATOR['unit']}")
        supabase_upsert('market_indicators', [result])
    else:
        logger.warning(f"❌ {INDICATOR['indicator_name']}: 수집 실패")
    logger.info("=== ECOS 기준금리 수집 완료 ===")


if __name__ == '__main__':
    main()

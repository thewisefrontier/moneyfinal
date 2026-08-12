"""
한국은행 ECOS API - 가계신용 (분기별 발표)
출처: https://ecos.bok.or.kr
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
    'stat_code': '151Y001',
    'cycle': 'Q',
    'item_code': '1000000',
    'indicator_code': 'HOUSEHOLD_CREDIT',
    'indicator_name': '가계신용 잔액',
    'unit': '십억원',
    'category': '가계부채',
    'start_days': 400
}


def fetch_ecos_stat(indicator: dict):
    now = datetime.now(KST)
    days = indicator.get('start_days', 90)
    start_dt = now - timedelta(days=days)
    start_q = (start_dt.month - 1) // 3 + 1
    end_q = (now.month - 1) // 3 + 1
    start = f"{start_dt.year}Q{start_q}"
    end = f"{now.year}Q{end_q}"

    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch"
        f"/{ECOS_API_KEY}/json/kr/1/10"
        f"/{indicator['stat_code']}/{indicator['cycle']}"
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

        return {
            'indicator_code': indicator['indicator_code'],
            'indicator_name': indicator['indicator_name'],
            'category': indicator['category'],
            'value': value,
            'prev_value': prev_value,
            'unit': indicator['unit'],
            'signal': 'green',
            'source': '한국은행 ECOS',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        }

    except Exception as e:
        logger.error(f"{indicator['indicator_name']} 수집 오류: {type(e).__name__}")
        return None


def main():
    logger.info("=== ECOS 가계신용 수집 시작 ===")
    if has_recent_data('market_indicators', {'indicator_code': 'eq.HOUSEHOLD_CREDIT'}, 'reference_date', 6):
        logger.info("이미 이번 분기 수집 완료 - 스킵 (재시도 크론 중복 방지)")
        return
    result = fetch_ecos_stat(INDICATOR)
    if result:
        logger.info(f"✅ {INDICATOR['indicator_name']}: {result['value']} {INDICATOR['unit']}")
        supabase_upsert('market_indicators', [result])
    else:
        logger.warning(f"❌ {INDICATOR['indicator_name']}: 수집 실패")
    logger.info("=== ECOS 가계신용 수집 완료 ===")


if __name__ == '__main__':
    main()

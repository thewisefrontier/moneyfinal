"""
한국은행 ECOS API 거시지표 수집기
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
ECOS_API_KEY = os.environ.get('ECOS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')

INDICATORS = [
    {
        'stat_code': '101Y004',   # M2 광의통화
        'cycle': 'M',
        'item_code': 'BBLA00',
        'indicator_code': 'M2_TOTAL',
        'indicator_name': '시중 유동성(M2)',
        'unit': '십억원',
        'category': '유동성',
        'start_days': 90
    },
    {
        'stat_code': '722Y001',   # 기준금리
        'cycle': 'D',
        'item_code': '0101000',
        'indicator_code': 'BASE_RATE',
        'indicator_name': '한국은행 기준금리',
        'unit': '%',
        'category': '금리',
        'start_days': 30
    },
    {
        'stat_code': '036Y001',   # 거주자외화예금
        'cycle': 'M',
        'item_code': 'A',
        'indicator_code': 'FOREIGN_DEPOSIT',
        'indicator_name': '거주자 외화예금',
        'unit': '백만달러',
        'category': '외화',
        'start_days': 90
    },
    {
        'stat_code': '731Y003',   # 원달러환율
        'cycle': 'M',
        'item_code': '0000001',
        'indicator_code': 'USD_KRW',
        'indicator_name': '원달러 환율',
        'unit': '원',
        'category': '환율',
        'start_days': 90
    },
]


def fetch_ecos_stat(indicator: dict):
    now = datetime.now(KST)
    days = indicator.get('start_days', 90)

    if indicator['cycle'] == 'M':
        start = (now - timedelta(days=days)).strftime('%Y%m')
        end = now.strftime('%Y%m')
    else:
        start = (now - timedelta(days=days)).strftime('%Y%m%d')
        end = now.strftime('%Y%m%d')

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
            msg = data['RESULT'].get('MESSAGE', '')
            logger.warning(f"{indicator['indicator_name']}: API 오류 - {msg}")
            return None

        rows = data.get('StatisticSearch', {}).get('row', [])
        if not rows:
            logger.warning(f"{indicator['indicator_name']}: 데이터 없음")
            return None

        # 유효한 값만 필터
        valid = [r for r in rows if r.get('DATA_VALUE') and r['DATA_VALUE'] != '0']
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
        logger.error(f"{indicator['indicator_name']} 수집 오류: {e}")
        return None


def main():
    logger.info("=== ECOS 거시지표 수집 시작 ===")
    results = []

    for indicator in INDICATORS:
        result = fetch_ecos_stat(indicator)
        if result:
            results.append(result)
            logger.info(f"✅ {indicator['indicator_name']}: {result['value']} {indicator['unit']}")
        else:
            logger.warning(f"❌ {indicator['indicator_name']}: 수집 실패")

    if results:
        supabase_upsert('market_indicators', results)

    logger.info(f"=== ECOS 수집 완료: {len(results)}/{len(INDICATORS)}건 ===")


if __name__ == '__main__':
    main()

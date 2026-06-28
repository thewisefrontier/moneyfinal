"""
한국은행 ECOS API 거시지표 수집기
출처: https://ecos.bok.or.kr
URL 형식: /api/StatisticSearch/{키}/json/kr/{시작건수}/{종료건수}/{통계코드}/{주기}/{시작일}/{종료일}/{항목코드}
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
        'stat_code': '101Y004',
        'cycle': 'M',
        'item_code': 'BBLA00',
        'indicator_code': 'M2_TOTAL',
        'indicator_name': '시중 유동성(M2)',
        'unit': '십억원',
        'category': '유동성'
    },
    {
        'stat_code': '722Y001',
        'cycle': 'D',
        'item_code': '0101000',
        'indicator_code': 'BASE_RATE',
        'indicator_name': '한국은행 기준금리',
        'unit': '%',
        'category': '금리'
    },
    {
        'stat_code': '036Y001',
        'cycle': 'M',
        'item_code': 'A',
        'indicator_code': 'FOREIGN_DEPOSIT',
        'indicator_name': '거주자 외화예금',
        'unit': '백만달러',
        'category': '외화'
    },
]


def fetch_ecos_stat(indicator: dict):
    now = datetime.now(KST)

    if indicator['cycle'] == 'M':
        start = (now - timedelta(days=90)).strftime('%Y%m')
        end = now.strftime('%Y%m')
    else:
        start = (now - timedelta(days=30)).strftime('%Y%m%d')
        end = now.strftime('%Y%m%d')

    # 올바른 URL 형식: 시작건수/종료건수 가 통계코드 앞에 와야 함
    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch"
        f"/{ECOS_API_KEY}/json/kr/1/10"
        f"/{indicator['stat_code']}/{indicator['cycle']}"
        f"/{start}/{end}/{indicator['item_code']}"
    )

    logger.info(f"ECOS 요청: {indicator['indicator_name']}")

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

        latest = rows[-1]
        prev = rows[-2] if len(rows) >= 2 else None
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

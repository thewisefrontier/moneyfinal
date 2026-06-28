"""
한국은행 ECOS API 거시지표 수집기
출처: https://ecos.bok.or.kr
URL: /api/StatisticSearch/{키}/json/kr/1/10/{통계코드}/{주기}/{시작}/{종료}/{항목코드}
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

# ECOS 통계코드 (통계표 파일 및 사이트에서 직접 확인)
INDICATORS = [
    {
        'stat_code': '722Y001',   # 한국은행 기준금리 (검증됨)
        'cycle': 'D',
        'item_code': '0101000',
        'indicator_code': 'BASE_RATE',
        'indicator_name': '한국은행 기준금리',
        'unit': '%',
        'category': '금리',
        'start_days': 30
    },
    {
        'stat_code': '161Y006',   # M2 상품별 구성내역(평잔, 원계열)
        'cycle': 'M',
        'item_code': 'BBHA00',
        'indicator_code': 'M2_TOTAL',
        'indicator_name': '시중 유동성(M2, 평잔)',
        'unit': '십억원',
        'category': '유동성',
        'start_days': 120
    },
    {
        'stat_code': '731Y001',   # 주요국 통화의 대원화환율 (일별)
        'cycle': 'D',
        'item_code': '0000001',
        'indicator_code': 'USD_KRW',
        'indicator_name': '원달러 환율',
        'unit': '원',
        'category': '환율',
        'start_days': 30
    },
    {
        'stat_code': '151Y001',   # 가계신용(업권별, 분기)
        'cycle': 'Q',
        'item_code': '1000000',
        'indicator_code': 'HOUSEHOLD_CREDIT',
        'indicator_name': '가계신용 잔액',
        'unit': '십억원',
        'category': '가계부채',
        'start_days': 400
    },
]


def fetch_ecos_stat(indicator: dict):
    now = datetime.now(KST)
    days = indicator.get('start_days', 90)
    cycle = indicator['cycle']

    if cycle == 'M':
        start = (now - timedelta(days=days)).strftime('%Y%m')
        end = now.strftime('%Y%m')
    elif cycle == 'Q':
        # 분기 형식: YYYYQn (예: 2025Q1 = 2025년 1분기)
        start_dt = now - timedelta(days=days)
        start_q = (start_dt.month - 1) // 3 + 1
        end_q = (now.month - 1) // 3 + 1
        start = f"{start_dt.year}Q{start_q}"
        end = f"{now.year}Q{end_q}" 
    else:  # D
        start = (now - timedelta(days=days)).strftime('%Y%m%d')
        end = now.strftime('%Y%m%d')

    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch"
        f"/{ECOS_API_KEY}/json/kr/1/10"
        f"/{indicator['stat_code']}/{cycle}"
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

        valid = [r for r in rows if r.get('DATA_VALUE') and r['DATA_VALUE'] not in ('0', '', None)]
        if not valid:
            logger.warning(f"{indicator['indicator_name']}: 유효 데이터 없음")
            return None

        latest = valid[-1]
        prev = valid[-2] if len(valid) >= 2 else None
        value = float(latest.get('DATA_VALUE', 0) or 0)
        prev_value = float(prev.get('DATA_VALUE', 0) or 0) if prev else None

        signal = 'green'
        if indicator['indicator_code'] == 'BASE_RATE':
            if value >= 3.5:
                signal = 'red'
            elif value >= 2.5:
                signal = 'yellow'
        elif indicator['indicator_code'] == 'USD_KRW':
            if value >= 1400:
                signal = 'red'
            elif value >= 1300:
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

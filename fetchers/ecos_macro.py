"""
한국은행 ECOS API 거시지표 수집기
- M2 유동성, 외화예금, 기준금리 등
- 출처: https://ecos.bok.or.kr
"""
import logging
import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)

ECOS_API_KEY = os.environ.get('ECOS_API_KEY', '')
ECOS_BASE_URL = f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_API_KEY}/json/kr"

# 수집할 ECOS 통계 목록
# (통계표코드, 주기, 항목코드, 지표명, 단위, 카테고리)
INDICATORS = [
    {
        'stat_code': '101Y004',    # M2 (광의통화)
        'cycle': 'M',              # 월별
        'item_code': 'BBLA00',
        'indicator_code': 'M2_TOTAL',
        'indicator_name': '시중 유동성(M2)',
        'unit': '십억원',
        'category': '유동성'
    },
    {
        'stat_code': '036Y001',    # 거주자외화예금
        'cycle': 'M',
        'item_code': '*AA',
        'indicator_code': 'FOREIGN_DEPOSIT',
        'indicator_name': '거주자 외화예금 (달러 엑소더스 지수)',
        'unit': '백만달러',
        'category': '외화'
    },
    {
        'stat_code': '722Y001',    # 기준금리
        'cycle': 'D',
        'item_code': '0101000',
        'indicator_code': 'BASE_RATE',
        'indicator_name': '한국은행 기준금리',
        'unit': '%',
        'category': '금리'
    },
    {
        'stat_code': '064Y001',    # 원달러 환율
        'cycle': 'D',
        'item_code': '0000001',
        'indicator_code': 'USD_KRW',
        'indicator_name': '원달러 환율',
        'unit': '원',
        'category': '환율'
    },
]


def fetch_ecos_stat(indicator: dict) -> dict | None:
    """ECOS 통계 최신값 1건 수집"""
    from datetime import datetime, timedelta
    import pytz

    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)

    # 월별은 최근 2개월, 일별은 최근 30일
    if indicator['cycle'] == 'M':
        start = (now - timedelta(days=60)).strftime('%Y%m')
        end = now.strftime('%Y%m')
    else:
        start = (now - timedelta(days=30)).strftime('%Y%m%d')
        end = now.strftime('%Y%m%d')

    url = (
        f"{ECOS_BASE_URL}/{indicator['stat_code']}/{indicator['cycle']}/"
        f"{start}/{end}/{indicator['item_code']}/1/5"
    )

    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()

        rows = data.get('StatisticSearch', {}).get('row', [])
        if not rows:
            logger.warning(f"{indicator['indicator_name']}: 데이터 없음")
            return None

        # 최신값
        latest = rows[-1]
        prev = rows[-2] if len(rows) >= 2 else None

        value = float(latest.get('DATA_VALUE', 0) or 0)
        prev_value = float(prev.get('DATA_VALUE', 0) or 0) if prev else None
        ref_date = latest.get('TIME', '')

        # 신호등 판단 (간단 로직, 추후 정교화)
        signal = 'green'
        if indicator['indicator_code'] == 'M2_TOTAL':
            # M2 증가율 5% 초과 시 yellow, 10% 초과 시 red
            if prev_value and prev_value > 0:
                growth = (value - prev_value) / prev_value * 100
                if growth > 10:
                    signal = 'red'
                elif growth > 5:
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
            'reference_date': ref_date[:10] if len(ref_date) >= 8 else today_kst(),
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

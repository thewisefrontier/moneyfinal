"""
국내 석유 전자상거래시장 시세 수집기
출처: 공공데이터포털 금융위원회_일반상품시세정보 (getOilPriceInfo)
- 휘발유/등유/경유 유종별 가중평균가격(경쟁매매 기준) 제공
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getOilPriceInfo"

OIL_TYPES = {
    '휘발유': {'indicator_code': 'OIL_GASOLINE', 'indicator_name': '휘발유 가격'},
    '등유':   {'indicator_code': 'OIL_KEROSENE', 'indicator_name': '등유 가격'},
    '경유':   {'indicator_code': 'OIL_DIESEL',   'indicator_name': '경유 가격'},
}


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_oil(base_date: str) -> list:
    params = {'resultType': 'json', 'numOfRows': 10, 'pageNo': 1, 'basDt': base_date}
    results = []
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning("석유시세: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        for item in items:
            oil_ctg = item.get('oilCtg', '')
            meta = OIL_TYPES.get(oil_ctg)
            if not meta:
                continue
            value = float(item.get('wtAvgPrcCptn', 0) or 0)
            results.append({
                'indicator_code': meta['indicator_code'],
                'indicator_name': meta['indicator_name'],
                'category': '원자재',
                'value': value,
                'prev_value': None,
                'unit': '원/L',
                'signal': 'green',
                'source': '금융위원회 (공공데이터포털, 석유전자상거래시장)',
                'reference_date': today_kst(),
                'summary_text': f"{oil_ctg} {value:,.2f}원/L (경쟁매매 가중평균)",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"석유시세 수집 오류: {e}")
        return []


def main():
    logger.info("=== 석유시세 수집 시작 ===")
    base_date = get_base_date()
    logger.info(f"기준일: {base_date}")
    results = fetch_oil(base_date)
    if results:
        supabase_upsert('market_indicators', results)
    logger.info(f"=== 석유시세 수집 완료: {len(results)}건 ===")


if __name__ == '__main__':
    main()

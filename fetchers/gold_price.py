"""
KRX 금시장 금시세 수집기
출처: 공공데이터포털 금융위원회_일반상품시세정보 (getGoldPriceInfo)
- FRED의 GOLDAMGBD228NLBM(LBMA 금가격)이 대체 없이 폐지되어 대체 소스로 도입
- KRX 금시장 "금 99.99_1Kg" 종목 기준 (원/g 단위)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getGoldPriceInfo"
ITMS_NM = "금 99.99_1Kg"


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_gold(base_date: str) -> dict | None:
    params = {'resultType': 'json', 'numOfRows': 1, 'pageNo': 1, 'basDt': base_date, 'itmsNm': ITMS_NM}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning("금시세: 데이터 없음")
            return None
        items = body.get('items', {}).get('item', [])
        item = items[0] if isinstance(items, list) and items else items
        value = float(item.get('clpr', 0) or 0)
        vs = float(item.get('vs', 0) or 0)
        flt_rt = float(item.get('fltRt', 0) or 0)
        return {
            'indicator_code': 'GOLD',
            'indicator_name': '금 가격 (KRX 99.99_1Kg)',
            'category': '원자재',
            'value': value,
            'prev_value': round(value - vs, 2),
            'unit': '원/g',
            'signal': 'green',
            'source': '금융위원회 (공공데이터포털, KRX 금시장)',
            'reference_date': today_kst(),
            'summary_text': f"금 {value:,.0f}원/g ({flt_rt:+.2f}%)",
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"금시세 수집 오류: {e}")
        return None


def main():
    logger.info("=== KRX 금시세 수집 시작 ===")
    base_date = get_base_date()
    logger.info(f"기준일: {base_date}")
    result = fetch_gold(base_date)
    if result:
        logger.info(f"✅ 금 {result['value']}원/g")
        supabase_upsert('market_indicators', [result])
    else:
        logger.warning("❌ 금시세 수집 실패")
    logger.info("=== KRX 금시세 수집 완료 ===")


if __name__ == '__main__':
    main()

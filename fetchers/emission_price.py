"""
탄소배출권(KAU) 시세 수집기
출처: 공공데이터포털 금융위원회_일반상품시세정보 (getCertifiedEmissionReductionPriceInfo)
- 종목명은 KAU+할당연도 2자리 형식 (예: KAU22, KAU23)
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 최신 basDt 값만 채택 (krx_index.py와 동일 패턴)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getCertifiedEmissionReductionPriceInfo"


def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')


def fetch_emission(begin_date: str) -> dict | None:
    itms_nm = f"KAU{datetime.now(KST).strftime('%y')}"
    params = {'resultType': 'json', 'numOfRows': 10, 'pageNo': 1, 'beginBasDt': begin_date, 'itmsNm': itms_nm}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"배출권시세({itms_nm}): 데이터 없음")
            return None
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict): items = [items]
        item = max(items, key=lambda x: x.get('basDt', ''))
        value = float(item.get('clpr', 0) or 0)
        vs = float(item.get('vs', 0) or 0)
        flt_rt = float(item.get('fltRt', 0) or 0)
        return {
            'indicator_code': 'CARBON_EMISSION',
            'indicator_name': f'탄소배출권 ({itms_nm})',
            'category': '원자재',
            'value': value,
            'prev_value': round(value - vs, 2),
            'unit': '원/톤',
            'signal': 'green',
            'source': '금융위원회 (공공데이터포털, 탄소배출권시장)',
            'reference_date': today_kst(),
            'summary_text': f"{itms_nm} {value:,.0f}원 ({flt_rt:+.2f}%)",
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"배출권시세 수집 오류: {e}")
        return None


def main():
    logger.info("=== 탄소배출권 시세 수집 시작 ===")
    begin_date = get_recent_date(10)
    logger.info(f"조회 시작일: {begin_date}")
    result = fetch_emission(begin_date)
    if result:
        logger.info(f"✅ {result['summary_text']}")
        supabase_upsert('market_indicators', [result])
    else:
        logger.warning("❌ 배출권시세 수집 실패")
    logger.info("=== 탄소배출권 시세 수집 완료 ===")


if __name__ == '__main__':
    main()

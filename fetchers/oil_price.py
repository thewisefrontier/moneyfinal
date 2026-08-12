"""
국내 석유 전자상거래시장 시세 수집기
출처: 공공데이터포털 금융위원회_일반상품시세정보 (getOilPriceInfo)
- 휘발유/등유/경유 유종별 가중평균가격 제공
- wtAvgPrcCptn(경쟁매매)은 거래 자체가 없는 날이 많아 0으로 내려옴 -> 그 경우
  wtAvgPrcDisc(협의매매) 값으로 대체 (실측 확인: 경쟁매매 0, 협의매매 실거래가)
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 유종별 최신 basDt 값만 채택 (krx_index.py와 동일 패턴)
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


def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')


def fetch_oil(begin_date: str) -> list:
    params = {'resultType': 'json', 'numOfRows': 30, 'pageNo': 1, 'beginBasDt': begin_date}
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
        # 유종별로 basDt가 가장 최신인 항목만 채택
        latest_by_type = {}
        for item in items:
            oil_ctg = item.get('oilCtg', '')
            if oil_ctg not in OIL_TYPES:
                continue
            cur = latest_by_type.get(oil_ctg)
            if cur is None or item.get('basDt', '') > cur.get('basDt', ''):
                latest_by_type[oil_ctg] = item
        for oil_ctg, item in latest_by_type.items():
            meta = OIL_TYPES[oil_ctg]
            cptn = float(item.get('wtAvgPrcCptn', 0) or 0)
            disc = float(item.get('wtAvgPrcDisc', 0) or 0)
            value = cptn if cptn > 0 else disc
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
                'summary_text': f"{oil_ctg} {value:,.2f}원/L (가중평균, {'경쟁매매' if cptn > 0 else '협의매매'})",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"석유시세 수집 오류: {e}")
        return []


def main():
    logger.info("=== 석유시세 수집 시작 ===")
    begin_date = get_recent_date(10)
    logger.info(f"조회 시작일: {begin_date}")
    results = fetch_oil(begin_date)
    if results:
        supabase_upsert('market_indicators', results)
    logger.info(f"=== 석유시세 수집 완료: {len(results)}건 ===")


if __name__ == '__main__':
    main()

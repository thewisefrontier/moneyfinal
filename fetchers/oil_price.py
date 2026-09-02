"""
국내 석유 전자상거래시장 시세 수집기
1차 출처: 공공데이터포털 금융위원회_일반상품시세정보 (getOilPriceInfo)
- 휘발유/등유/경유 유종별 가중평균가격 제공
- wtAvgPrcCptn(경쟁매매)은 거래 자체가 없는 날이 많아 0으로 내려옴 -> 그 경우
  wtAvgPrcDisc(협의매매) 값으로 대체 (실측 확인: 경쟁매매 0, 협의매매 실거래가)
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 유종별 최신 basDt 값만 채택 (krx_index.py와 동일 패턴)

2차(폴백) 출처: 오피넷(한국석유공사 Open API, opinet.co.kr avgAllPrice) - 1차 API가
장애/차단된 경우에만 사용. [[moneyfinal_krx_backup_pipeline_research]] 조사 결과에
따른 백업. 금융위원회/KRX와 완전히 다른 기관(한국석유공사)이 직접 운영하는 API라
이번 라이선스 이슈와 무관. 전국 주유소 평균 소매가(원/L) 기준으로 1차의 석유
전자상거래시장 가중평균가와 성격은 다르지만(도매 e-market vs 소매 평균) 같은
"국내 유가" 카테고리 목적은 충분히 대체함.
⚠️ PRODCD 매핑은 실측으로 검증함(2026-09-02, 실제 키로 라이브 호출 확인) -
문서상 등유=K015로 나온 자료가 있었으나 실제로는 K015=자동차용부탄이었고
등유는 C004(실내등유)였음 - 문서만 보고 하드코딩했으면 등유에 부탄 가격이
들어가는 오류가 날 뻔함, 반드시 실측 확인할 것.
"""
import logging, os, sys, requests
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
OPINET_API_KEY = os.environ.get('OPINET_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetGeneralProductInfoService/getOilPriceInfo"
OPINET_URL = "https://www.opinet.co.kr/api/avgAllPrice.do"

OIL_TYPES = {
    '휘발유': {'indicator_code': 'OIL_GASOLINE', 'indicator_name': '휘발유 가격'},
    '등유':   {'indicator_code': 'OIL_KEROSENE', 'indicator_name': '등유 가격'},
    '경유':   {'indicator_code': 'OIL_DIESEL',   'indicator_name': '경유 가격'},
}

# 오피넷 상품코드 -> 위 OIL_TYPES 키 매핑 (실측 확인된 값)
OPINET_PRODCD_MAP = {
    'B027': '휘발유',   # 휘발유 (고급휘발유 B034는 제외)
    'D047': '경유',     # 자동차용경유
    'C004': '등유',     # 실내등유
}


def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')


def fetch_oil_primary(begin_date: str) -> list:
    params = {'resultType': 'json', 'numOfRows': 30, 'pageNo': 1, 'beginBasDt': begin_date}
    results = []
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
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
        logger.warning(f"석유시세 1차(data.go.kr) 실패: {type(e).__name__}")
        return []


def fetch_oil_fallback() -> list:
    if not OPINET_API_KEY:
        logger.error("석유시세 2차(오피넷) 실패: OPINET_API_KEY 미설정")
        return []
    try:
        res = requests.get(OPINET_URL, params={'out': 'json', 'certkey': OPINET_API_KEY}, timeout=15)
        res.raise_for_status()
        data = res.json()
        rows = data.get('RESULT', {}).get('OIL', [])
        results = []
        for row in rows:
            oil_key = OPINET_PRODCD_MAP.get(row.get('PRODCD'))
            if not oil_key:
                continue
            meta = OIL_TYPES[oil_key]
            value = float(row.get('PRICE', 0) or 0)
            diff = float(row.get('DIFF', 0) or 0)
            results.append({
                'indicator_code': meta['indicator_code'],
                'indicator_name': meta['indicator_name'],
                'category': '원자재',
                'value': value,
                'prev_value': round(value - diff, 2),
                'unit': '원/L',
                'signal': 'green',
                'source': '오피넷 한국석유공사 (data.go.kr 장애 시 폴백, 전국 소매 평균가)',
                'reference_date': today_kst(),
                'summary_text': f"{oil_key} {value:,.2f}원/L (전국 평균, {diff:+.2f})",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"석유시세 2차(오피넷) 실패: {type(e).__name__}")
        return []


def main():
    logger.info("=== 석유시세 수집 시작 ===")
    begin_date = get_recent_date(10)
    logger.info(f"조회 시작일: {begin_date}")
    results = fetch_oil_primary(begin_date)
    if not results:
        logger.warning("석유시세: 1차 실패 -> 오피넷 폴백 시도")
        results = fetch_oil_fallback()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 석유시세 {len(results)}건 저장")
    else:
        logger.error("❌ 석유시세 수집 실패 (1차/2차 모두 실패)")
    logger.info(f"=== 석유시세 수집 완료 ===")


if __name__ == '__main__':
    main()

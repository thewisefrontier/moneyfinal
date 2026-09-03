"""
채권 시세 수집기
1차 출처: 공공데이터포털 금융위원회_채권시세정보 (GetBondSecuritiesInfoService/getBondPriceInfo)
  - 개별 채권 종목(ISIN)별 수익률
2차(폴백) 출처: 한국은행 ECOS 시장금리(일별) 통계표 817Y002 - 1차 API가 장애/차단된
  경우에만 사용. [[moneyfinal_krx_backup_pipeline_research]] 조사 결과에 따른 백업.
  개별 종목이 아닌 국고채 3/5/10년 + 회사채(AA-) 3년 대표 벤치마크 금리로 대체 -
  macro-detail.html "채권금리" 카테고리의 실질 목적(대표 금리 수준 표시)은 이걸로 충분.
  ECOS는 data.go.kr/KRX와 무관한 한국은행 자체 API라 이번 라이선스 이슈와 무관.
  ⚠️ ECOS StatisticItemList로 항목코드를 런타임에 이름 매칭해서 찾음(하드코딩 안 함,
  ECOS_API_KEY가 로컬에 없어 실측 테스트 못 함 - 최초 운영 실행 시 로그로 매칭 결과 확인 필요).
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 종목별 최신 basDt 값만 채택 (krx_index.py와 동일 패턴,
  실측 확인: category='채권금리' 데이터가 한 번도 DB에 저장된 적 없었음)
"""
import logging, os, sys, requests
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
ECOS_API_KEY = os.environ.get('ECOS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetBondSecuritiesInfoService/getBondPriceInfo"

# ECOS 817Y002(시장금리, 일별) 항목명에 포함될 것으로 예상되는 키워드 -> 우리 지표코드 매핑
# (항목코드를 하드코딩하지 않고 StatisticItemList 조회 결과에서 이름으로 매칭)
ECOS_BOND_TARGETS = [
    {'indicator_code': 'BOND_KTB3Y',    'indicator_name': '국고채(3년)',      'keywords': ['국고채', '3년']},
    {'indicator_code': 'BOND_KTB5Y',    'indicator_name': '국고채(5년)',      'keywords': ['국고채', '5년']},
    {'indicator_code': 'BOND_KTB10Y',   'indicator_name': '국고채(10년)',     'keywords': ['국고채', '10년']},
    {'indicator_code': 'BOND_CORPAA3Y', 'indicator_name': '회사채(AA-, 3년)', 'keywords': ['회사채', 'AA', '3년']},
]


def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')


def fetch_bonds_primary(begin_date: str) -> list:
    params = {'resultType':'json','numOfRows':500,'pageNo':1,'beginBasDt':begin_date}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        latest_by_code = {}
        for item in items:
            code = item.get('isinCd','')
            cur = latest_by_code.get(code)
            if cur is None or item.get('basDt','') > cur.get('basDt',''):
                latest_by_code[code] = item
        results = []
        for item in latest_by_code.values():
            ytm = float(item.get('clprBnfRt',0) or 0)
            results.append({
                'indicator_code': f"BOND_{item.get('isinCd','')[:10]}",
                'indicator_name': item.get('itmsNm',''),
                'category': '채권금리',
                'value': ytm,
                'unit': '%',
                'signal': 'green' if ytm<4 else 'yellow' if ytm<5 else 'red',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{item.get('mrktCtg','')} 종가 {item.get('clprPrc','')}",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.warning(f"채권시세 1차(data.go.kr) 실패: {type(e).__name__}")
        return []


def ecos_find_item_code(keywords: list) -> tuple | None:
    """817Y002 통계표의 세부항목 목록에서 keywords를 모두 포함하는 첫 항목을 찾는다."""
    url = f"https://ecos.bok.or.kr/api/StatisticItemList/{ECOS_API_KEY}/json/kr/1/500/817Y002"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()
        rows = data.get('StatisticItemList', {}).get('row', [])
        for row in rows:
            name = row.get('ITEM_NAME', '')
            if all(kw in name for kw in keywords):
                return row.get('ITEM_CODE'), name
        return None
    except Exception as e:
        logger.error(f"ECOS 항목목록 조회 실패: {type(e).__name__}")
        return None


def fetch_bonds_fallback() -> list:
    if not ECOS_API_KEY:
        logger.error("채권시세 2차(ECOS) 실패: ECOS_API_KEY 미설정")
        return []
    now = datetime.now(KST)
    start = (now - timedelta(days=10)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    results = []
    for target in ECOS_BOND_TARGETS:
        found = ecos_find_item_code(target['keywords'])
        if not found:
            logger.warning(f"ECOS 폴백: '{target['indicator_name']}' 항목 매칭 실패 (키워드 {target['keywords']})")
            continue
        item_code, matched_name = found
        url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_API_KEY}/json/kr/1/100"
               f"/817Y002/D/{start}/{end}/{item_code}")
        try:
            res = requests.get(url, timeout=15)
            res.raise_for_status()
            data = res.json()
            rows = data.get('StatisticSearch', {}).get('row', [])
            valid = [r for r in rows if r.get('DATA_VALUE') not in (None, '', '0')]
            if not valid:
                logger.warning(f"ECOS 폴백: '{matched_name}' 유효 데이터 없음")
                continue
            latest = valid[-1]
            ytm = float(latest.get('DATA_VALUE', 0) or 0)
            results.append({
                'indicator_code': target['indicator_code'],
                'indicator_name': target['indicator_name'],
                'category': '채권금리',
                'value': ytm,
                'unit': '%',
                'signal': 'green' if ytm<4 else 'yellow' if ytm<5 else 'red',
                'source': '한국은행 ECOS (data.go.kr 장애 시 폴백, 개별종목 아닌 대표금리)',
                'reference_date': today_kst(),
                'summary_text': f"{matched_name} {ytm:.2f}%",
                'fetched_at': now_kst()
            })
            logger.info(f"✅ ECOS 폴백: '{matched_name}' = {ytm}%")
        except Exception as e:
            logger.error(f"ECOS 폴백 '{matched_name}' 조회 실패: {type(e).__name__}")
    return results


def main():
    logger.info("=== 채권 시세 수집 시작 ===")
    results = fetch_bonds_fallback()
    if not results:
        logger.warning("채권시세: ECOS 1차 실패 -> data.go.kr 폴백 시도")
        begin_date = get_recent_date(10)
        results = fetch_bonds_primary(begin_date)
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 채권시세 {len(results)}건 저장")
    else:
        logger.error("❌ 채권시세 수집 실패 (1차/2차 모두 실패)")
    logger.info("=== 채권 시세 수집 완료 ===")


if __name__ == '__main__': main()

"""
ISA 다모아정보 수집기
출처: 공공데이터포털 금융위원회_ISA다모아정보 (GetISAInfoService_V2)
정확한 서비스명: 이전 코드는 GetIsaProductInfoService로 잘못 추측됨
- getMPBenefitRateInfo_V2, getJoinStatus_V2 모두 basDt가 매일 갱신되지 않을 수 있어
  beginBasDt 범위 조회 후 basDt 최신값만 채택
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/GetISAInfoService_V2"

def get_recent_date(days_back: int = 90) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')

def latest_by_key(results: list) -> list:
    """indicator_code별로 basDt(YYYYMMDD)가 가장 최신인 항목만 채택"""
    latest = {}
    for r in results:
        key = r['indicator_code']
        if key not in latest or r['_basDt'] > latest[key]['_basDt']:
            latest[key] = r
    for r in latest.values():
        r.pop('_basDt', None)
    return list(latest.values())

def collect_mp_benefit_rate() -> list:
    """ISAMP대표수익률 (getMPBenefitRateInfo_V2) - 실제 수익률 제공"""
    url = f"{BASE_URL}/getMPBenefitRateInfo_V2"
    params = {'resultType':'json','numOfRows':100,'pageNo':1,'beginBasDt':get_recent_date(90)}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("ISAMP대표수익률: 데이터 없음")
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            if item.get('trm') != '6개월':  # 중복 방지용 기간 필터
                continue
            rt = float(item.get('bnfRt',0) or 0)
            results.append({
                'indicator_code': f"ISA_{item.get('cmpyNm','')}_{item.get('mpTp','')}"[:50],
                'indicator_name': f"{item.get('cmpyNm','')} {item.get('mpNm','')} ({item.get('mpTp','')})",
                'category': 'ISA',
                'value': rt,
                'unit': '%',
                'signal': 'green' if rt>=0 else 'red',
                'source': '금융투자협회 ISA다모아 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"6개월 수익률",
                'fetched_at': now_kst(),
                '_basDt': item.get('basDt','')
            })
        return latest_by_key(results)
    except Exception as e:
        logger.error(f"ISAMP대표수익률 수집 오류: {type(e).__name__}")
        return []

def collect_join_status() -> list:
    """ISA업권별가입현황 (getJoinStatus_V2)"""
    url = f"{BASE_URL}/getJoinStatus_V2"
    params = {'resultType':'json','numOfRows':100,'pageNo':1,'beginBasDt':get_recent_date(90)}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0): return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            amt = float(item.get('invAmt',0) or 0)
            if amt <= 0: continue
            results.append({
                'indicator_code': f"ISA_JOIN_{item.get('isaForm','')}_{item.get('ctg','')}"[:50],
                'indicator_name': f"ISA 가입현황 {item.get('isaForm','')} ({item.get('ctg','')})",
                'category': 'ISA',
                'value': amt,
                'unit': '원',
                'signal': 'green',
                'source': '금융투자협회 ISA다모아 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"가입자수 {item.get('jnpnCnt','')}명, 회사수 {item.get('cmpyCnt','')}개",
                'fetched_at': now_kst(),
                '_basDt': item.get('basDt','')
            })
        return latest_by_key(results)
    except Exception as e:
        logger.error(f"ISA가입현황 수집 오류: {type(e).__name__}")
        return []

def main():
    logger.info("=== ISA 다모아 수집 시작 ===")
    results = collect_mp_benefit_rate() + collect_join_status()
    if results:
        # 두 collector 결과를 합친 뒤에도 혹시 모를 중복 키 재확인
        deduped = list({r['indicator_code']: r for r in results}.values())
        if len(deduped) != len(results):
            logger.warning(f"중복 제거: {len(results)}건 -> {len(deduped)}건")
        supabase_upsert('market_indicators', deduped)
        logger.info(f"✅ ISA 정보 {len(deduped)}건 저장")
    logger.info("=== ISA 다모아 수집 완료 ===")

if __name__ == '__main__': main()

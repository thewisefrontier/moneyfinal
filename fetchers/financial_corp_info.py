"""
금융회사 기본정보 / 재무신용정보 수집기
출처: 공공데이터포털
  - 기본정보: GetFnCoBasiInfoService/getFnCoOutl
  - 재무정보: GetFnCoFinaStatCredInfoService_V2/getFnCoSummFinaStat_V2
정확한 서비스명: 이전 코드는 GetFinancialCompanyInfoService 등으로 잘못 추측됨.
bisRto(BIS비율) 필드는 존재하지 않으며, fncoDebtRto(부채비율)가 정확한 필드임
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get, has_recent_data

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service"

def fetch_financial_corps() -> list:
    url = f"{BASE_URL}/GetFnCoBasiInfoService/getFnCoOutl"
    params = {'resultType':'json','numOfRows':100,'pageNo':1}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0): return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        return [{
            'stock_code':    f"FIN_{item.get('crno','')}",
            'corp_name':     item.get('fncoNm',''),
            'industry_name': item.get('sicNm','') or item.get('sicCd',''),
            'address':       item.get('fncoAdr',''),
            'homepage':      item.get('fncoHmpgUrl',''),
            'phone':         item.get('fncoTlno',''),
            'market_type':   '금융회사',
            'fetched_at':    now_kst()
        } for item in items if item.get('crno','')]
    except Exception as e:
        logger.error(f"금융회사기본정보 수집 오류: {type(e).__name__}")
        return []

def fetch_financial_credit() -> list:
    """금융회사요약재무제표조회 - 부채비율을 건전성 지표로 사용 (BIS비율 필드는 존재하지 않음)"""
    url = f"{BASE_URL}/GetFnCoFinaStatCredInfoService_V2/getFnCoSummFinaStat_V2"
    params = {'resultType':'json','numOfRows':50,'pageNo':1}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0): return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            debt_rto = float(item.get('fncoDebtRto',0) or 0)
            if debt_rto <= 0: continue
            crno = item.get('crno','')[:10]
            results.append({
                'indicator_code': f"FINCRED_{crno}",
                'indicator_name': f"금융회사 부채비율 ({crno})",
                'category': '금융회사건전성',
                'value': debt_rto,
                'unit': '%',
                'signal': 'green' if debt_rto<300 else 'yellow' if debt_rto<600 else 'red',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"금융회사재무신용 수집 오류: {type(e).__name__}")
        return []

def main():
    logger.info("=== 금융회사 정보 수집 시작 ===")
    if has_recent_data('corp_info', {'market_type': 'eq.금융회사'}, 'fetched_at', 6):
        logger.info("금융회사기본정보 - 이미 이번 분기 수집 완료, 스킵")
    else:
        corps = fetch_financial_corps()
        if corps:
            supabase_upsert('corp_info', corps)
            logger.info(f"✅ 금융회사기본정보 {len(corps)}건 저장")
    if has_recent_data('market_indicators', {'category': 'eq.금융회사건전성'}, 'reference_date', 6):
        logger.info("금융회사재무신용 - 이미 이번 분기 수집 완료, 스킵")
    else:
        credit = fetch_financial_credit()
        if credit:
            supabase_upsert('market_indicators', credit)
            logger.info(f"✅ 금융회사재무신용 {len(credit)}건 저장")
    logger.info("=== 금융회사 정보 수집 완료 ===")

if __name__ == '__main__': main()

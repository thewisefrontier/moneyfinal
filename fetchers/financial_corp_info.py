"""
금융회사 기본정보 / 재무신용정보 수집기
- 금융위원회_금융회사기본정보 (공공데이터포털)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service"


def fetch_financial_corps() -> list:
    url = f"{BASE_URL}/GetFinancialCompanyInfoService/getFinancialCompanyInfo"
    params = {'resultType':'json','numOfRows':100,'pageNo':1}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response',{}).get('body',{})
        if not body.get('totalCount',0): return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items, dict): items = [items]
        results = []
        for item in items:
            reg_no = item.get('fncoRegNo','')
            if not reg_no: continue
            results.append({
                'stock_code':    f"FIN_{reg_no}",
                'corp_name':     item.get('fncoNm',''),
                'industry_name': item.get('fncoClssNm',''),
                'address':       item.get('fncoAdr',''),
                'homepage':      item.get('fncoHmpgUrl',''),
                'phone':         item.get('fncoTlno',''),
                'market_type':   '금융회사',
                'fetched_at':    now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"금융회사기본정보 수집 오류: {type(e).__name__}")
        return []


def fetch_financial_credit() -> list:
    url = f"{BASE_URL}/GetFinancialCompanyCreditInfoService/getFinancialCompanyCreditInfo"
    params = {'resultType':'json','numOfRows':50,'pageNo':1}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response',{}).get('body',{})
        if not body.get('totalCount',0): return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items, dict): items = [items]
        results = []
        for item in items:
            bis = float(item.get('bisRto',0) or 0)
            reg_no = item.get('fncoRegNo','')[:10]
            results.append({
                'indicator_code': f"BIS_{reg_no}",
                'indicator_name': f"{item.get('fncoNm','')} BIS비율",
                'category':       '금융회사건전성',
                'value':          bis,
                'unit':           '%',
                'signal':         'green' if bis >= 12 else 'yellow' if bis >= 10 else 'red',
                'source':         '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at':     now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"금융회사재무신용 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 금융회사 정보 수집 시작 ===")
    corps = fetch_financial_corps()
    if corps:
        supabase_upsert('corp_info', corps)
        logger.info(f"✅ 금융회사기본정보 {len(corps)}건 저장")
    credit = fetch_financial_credit()
    if credit:
        supabase_upsert('market_indicators', credit)
        logger.info(f"✅ 금융회사재무신용 {len(credit)}건 저장")
    logger.info("=== 금융회사 정보 수집 완료 ===")

if __name__ == '__main__': main()

"""
기업 재무/기본정보 수집기
출처: 공공데이터포털
  - 재무정보: GetFinaStatInfoService_V2/getSummFinaStat_V2 (요약재무제표)
  - 기본정보: GetCorpBasicInfoService_V2/getCorpOutline_V2
주의: PER/PBR/ROE/EPS 필드는 존재하지 않음 (이전 코드의 pER/pBR/rOE/ePS는 추측된 가짜 필드).
실제 제공 필드: 매출액(enpSaleAmt), 영업이익(enpBzopPft), 순이익(enpCrtmNpf), 총자산(enpTastAmt), 부채비율(fnclDebtRto)
"""
import logging, os, sys, time
from datetime import datetime
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service"

MAJOR_STOCKS = [
    {'crno':'1301110006246','name':'삼성전자'},{'crno':'1648110006794','name':'SK하이닉스'},
    {'crno':'1301110003708','name':'현대차'},{'crno':'1101110015014','name':'NAVER'},
    {'crno':'1301110005643','name':'POSCO홀딩스'},{'crno':'1101111623419','name':'LG화학'},
    {'crno':'1301110013455','name':'삼성SDI'},{'crno':'1101110608146','name':'카카오'},
    {'crno':'1301110006246','name':'기아'},{'crno':'1101110028131','name':'KB금융'},
]


def fetch_corp_finance(stock: dict) -> dict | None:
    """요약재무제표조회 - PER/PBR 등 투자지표는 제공되지 않음, 재무제표 원시 항목만 제공"""
    url = f"{BASE_URL}/GetFinaStatInfoService_V2/getSummFinaStat_V2"
    now = datetime.now(KST)
    fiscal_year = now.year - 1 if now.month < 4 else now.year
    params = {'resultType':'json','numOfRows':1,'pageNo':1,'crno':stock['crno'],'bizYear':str(fiscal_year)}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning(f"{stock['name']}: 재무 데이터 없음")
            return None
        items = body.get('items',{}).get('item',[])
        item = items[0] if isinstance(items, list) and items else items
        if not item: return None
        return {
            'stock_code':       stock['crno'][:6],
            'corp_name':        stock['name'],
            'base_date':        f"{fiscal_year}-12-31",
            'fiscal_year':      fiscal_year,
            'fiscal_quarter':   4,
            'report_type':      '요약재무제표',
            'revenue':          int(float(item.get('enpSaleAmt',0) or 0)),
            'operating_profit': int(float(item.get('enpBzopPft',0) or 0)),
            'net_profit':       int(float(item.get('enpCrtmNpf',0) or 0)),
            'total_assets':     int(float(item.get('enpTastAmt',0) or 0)),
            'total_liabilities':int(float(item.get('enpTdbtAmt',0) or 0)),
            'total_equity':     int(float(item.get('enpTcptAmt',0) or 0)),
            'per':              0,
            'pbr':              0,
            'roe':              0,
            'eps':              0,
            'fetched_at':       now_kst()
        }
    except Exception as e:
        logger.error(f"{stock['name']} 재무정보 오류: {type(e).__name__}")
        return None


def fetch_corp_info(stock: dict) -> dict | None:
    url = f"{BASE_URL}/GetCorpBasicInfoService_V2/getCorpOutline_V2"
    params = {'resultType':'json','numOfRows':1,'pageNo':1,'crno':stock['crno']}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0): return None
        items = body.get('items',{}).get('item',[])
        item = items[0] if isinstance(items, list) and items else items
        if not item: return None
        return {
            'stock_code':    stock['crno'][:6],
            'corp_name':     item.get('corpNm', stock['name']),
            'ceo_name':      item.get('enpRprFnm',''),
            'address':       item.get('enpBsadr',''),
            'homepage':      item.get('enpHmpgUrl',''),
            'phone':         item.get('enpTlno',''),
            'industry_name': item.get('sicNm',''),
            'listing_date':  item.get('enpXchgLstgDt', None),
            'market_type':   item.get('corpRegMrktDcdNm',''),
            'fetched_at':    now_kst()
        }
    except Exception as e:
        logger.error(f"{stock['name']} 기본정보 오류: {type(e).__name__}")
        return None


def main():
    logger.info("=== 기업 재무/기본정보 수집 시작 ===")
    finance_results, corp_results = [], []
    for stock in MAJOR_STOCKS:
        f = fetch_corp_finance(stock)
        if f: finance_results.append(f); logger.info(f"✅ {stock['name']} 재무 수집")
        time.sleep(0.5)
        c = fetch_corp_info(stock)
        if c: corp_results.append(c)
        time.sleep(0.5)
    if finance_results: supabase_upsert('corp_finance', finance_results)
    if corp_results: supabase_upsert('corp_info', corp_results)
    logger.info(f"재무 {len(finance_results)}건 / 기본정보 {len(corp_results)}건 저장")
    logger.info("=== 기업 재무/기본정보 수집 완료 ===")

if __name__ == '__main__': main()

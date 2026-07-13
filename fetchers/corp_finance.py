"""
기업 재무/기본정보 수집기 + PER/PBR/ROE/EPS 계산
출처: 공공데이터포털
  - 재무정보: GetFinaStatInfoService_V2/getSummFinaStat_V2 (요약재무제표)
  - 기본정보: GetCorpBasicInfoService_V2/getCorpOutline_V2

주의: 공공데이터포털 API는 PER/PBR/ROE/EPS를 직접 제공하지 않는다.
대신 같은 종목의 stock_prices(종가, 시가총액, 상장주식수)와
재무제표(순이익, 자본총계)를 결합해 표준 재무공식으로 직접 계산한다.
(corp_finance 테이블에 계산값 여부를 표시하는 별도 컬럼은 없음 - API 원시값과
구분이 필요하면 이 주석을 참고)

EPS = 순이익 / 상장주식수
PER = 종가 / EPS
PBR = 시가총액 / 자본총계
ROE = 순이익 / 자본총계 * 100
"""
import logging, os, re, sys, time
from datetime import datetime
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, supabase_select, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service"

# crno: 법인등록번호 (API 조회용), stock_code: 실제 종목코드 (stock_prices 테이블과 매칭용)
MAJOR_STOCKS = [
    {'crno':'1301110006246','stock_code':'005930','name':'삼성전자'},
    {'crno':'1648110006794','stock_code':'000660','name':'SK하이닉스'},
    {'crno':'1301110003708','stock_code':'005380','name':'현대차'},
    {'crno':'1101110015014','stock_code':'035420','name':'NAVER'},
    {'crno':'1301110005643','stock_code':'005490','name':'POSCO홀딩스'},
    {'crno':'1101111623419','stock_code':'051910','name':'LG화학'},
    {'crno':'1301110013455','stock_code':'006400','name':'삼성SDI'},
    {'crno':'1101110608146','stock_code':'035720','name':'카카오'},
    {'crno':'1301110014488','stock_code':'000270','name':'기아'},
    {'crno':'1101110028131','stock_code':'105560','name':'KB금융'},
]


def fetch_corp_finance_raw(stock: dict) -> dict | None:
    """요약재무제표조회 - 순이익, 자본총계 등 원시 재무항목 조회"""
    url = f"{BASE_URL}/GetFinaStatInfoService_V2/getSummFinaStat_V2"
    now = datetime.now(KST)
    # 상장기업 사업보고서는 회계연도 종료 후 익년 3월경(90일 이내) 공시된다.
    # 따라서 4월 이후에는 "작년" 자료가, 4월 이전에는 아직 작년 자료가 공시되지 않았을 수 있어
    # "재작년" 자료가 최신 공시분이다. (직전 로직은 반대로 아직 존재하지 않는 연도를 요청해
    # 전 종목 조회가 실패하는 원인이었음)
    fiscal_year = now.year - 2 if now.month < 4 else now.year - 1
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
            'fiscal_year':      fiscal_year,
            'revenue':          int(float(item.get('enpSaleAmt',0) or 0)),
            'operating_profit': int(float(item.get('enpBzopPft',0) or 0)),
            'net_profit':       int(float(item.get('enpCrtmNpf',0) or 0)),
            'total_assets':     int(float(item.get('enpTastAmt',0) or 0)),
            'total_liabilities':int(float(item.get('enpTdbtAmt',0) or 0)),
            'total_equity':     int(float(item.get('enpTcptAmt',0) or 0)),
        }
    except Exception as e:
        logger.error(f"{stock['name']} 재무정보 오류: {type(e).__name__}")
        return None


def _normalize_listing_date(raw) -> str | None:
    """상장일 필드 정규화.

    data.go.kr 응답이 간헐적으로 2자리 연도(YY/MM/DD, 예: "75/06/11")로 내려와
    Postgres date 컬럼에 그대로 넣으면 "date/time field value out of range" 오류로
    upsert 배치 전체가 실패한다. YYYY-MM-DD, YYYYMMDD 형식은 그대로 통과시키고,
    YY/MM/DD는 현재 연도 기준 pivot으로 세기를 판별해 ISO 형식으로 변환한다.
    그 외 인식 불가 형식은 크래시 대신 경고 로그 후 None으로 저장한다.
    """
    if not raw:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', raw)
    if m:
        return raw

    m = re.match(r'^(\d{4})(\d{2})(\d{2})$', raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    m = re.match(r'^(\d{2})/(\d{2})/(\d{2})$', raw)
    if m:
        yy, mm, dd = int(m.group(1)), m.group(2), m.group(3)
        current_yy = datetime.now(KST).year % 100
        year = 2000 + yy if yy <= current_yy else 1900 + yy
        return f"{year:04d}-{mm}-{dd}"

    logger.warning(f"listing_date 형식 인식 불가, null 처리: {raw!r}")
    return None


def fetch_corp_info(stock: dict) -> dict | None:
    url = f"{BASE_URL}/GetCorpBasicInfoService_V2/getCorpOutline_V2"
    params = {'resultType':'json','numOfRows':1,'pageNo':1,'crno':stock['crno']}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning(f"{stock['name']}: 기본정보 없음")
            return None
        items = body.get('items',{}).get('item',[])
        item = items[0] if isinstance(items, list) and items else items
        if not item: return None
        return {
            'stock_code':    stock['stock_code'],
            'corp_name':     item.get('corpNm', stock['name']),
            'ceo_name':      item.get('enpRprFnm',''),
            'address':       item.get('enpBsadr',''),
            'homepage':      item.get('enpHmpgUrl',''),
            'phone':         item.get('enpTlno',''),
            'industry_name': item.get('sicNm',''),
            'listing_date':  _normalize_listing_date(item.get('enpXchgLstgDt', None)),
            'market_type':   item.get('corpRegMrktDcdNm',''),
            'fetched_at':    now_kst()
        }
    except Exception as e:
        logger.error(f"{stock['name']} 기본정보 오류: {type(e).__name__}")
        return None


def get_latest_price(stock_code: str) -> dict | None:
    """stock_prices 테이블에서 해당 종목의 최신 종가/시가총액/상장주식수 조회"""
    rows = supabase_select('stock_prices', {
        'select': 'close_price,market_cap,shares_out',
        'stock_code': f'eq.{stock_code}',
        'order': 'fetched_at.desc',
        'limit': '1'
    })
    return rows[0] if rows else None


def calculate_indicators(price: dict, finance: dict) -> dict:
    """EPS/PER/PBR/ROE 계산. 분모가 0이거나 데이터가 없으면 0 반환."""
    shares_out = float(price.get('shares_out', 0) or 0)
    close_price = float(price.get('close_price', 0) or 0)
    market_cap = float(price.get('market_cap', 0) or 0)
    net_profit = finance.get('net_profit', 0)
    total_equity = finance.get('total_equity', 0)

    eps = (net_profit / shares_out) if shares_out > 0 else 0
    per = (close_price / eps) if eps > 0 else 0
    pbr = (market_cap / total_equity) if total_equity > 0 else 0
    roe = (net_profit / total_equity * 100) if total_equity > 0 else 0

    return {
        'eps': round(eps, 2),
        'per': round(per, 2),
        'pbr': round(pbr, 2),
        'roe': round(roe, 2),
    }


def main():
    logger.info("=== 기업 재무/기본정보 + 투자지표 계산 시작 ===")
    finance_results, corp_results = [], []

    for stock in MAJOR_STOCKS:
        raw = fetch_corp_finance_raw(stock)
        time.sleep(0.5)
        c = fetch_corp_info(stock)
        if c:
            corp_results.append(c)
        time.sleep(0.5)

        if not raw:
            continue

        price = get_latest_price(stock['stock_code'])
        indicators = calculate_indicators(price, raw) if price else {'eps':0,'per':0,'pbr':0,'roe':0}
        if not price:
            logger.warning(f"{stock['name']}: stock_prices에 시세 데이터 없음, 지표 계산 보류 (0으로 저장)")

        finance_results.append({
            'stock_code':       stock['stock_code'],
            'corp_name':        stock['name'],
            'base_date':        f"{raw['fiscal_year']}-12-31",
            'fiscal_year':      raw['fiscal_year'],
            'fiscal_quarter':   4,
            'report_type':      '요약재무제표',
            'revenue':          raw['revenue'],
            'operating_profit': raw['operating_profit'],
            'net_profit':       raw['net_profit'],
            'total_assets':     raw['total_assets'],
            'total_liabilities':raw['total_liabilities'],
            'total_equity':     raw['total_equity'],
            'per':              indicators['per'],
            'pbr':              indicators['pbr'],
            'roe':              indicators['roe'],
            'eps':              indicators['eps'],
            'fetched_at':       now_kst()
        })
        logger.info(f"✅ {stock['name']} 재무+지표 계산 완료 (EPS {indicators['eps']}, PER {indicators['per']})")

    if finance_results: supabase_upsert('corp_finance', finance_results)
    if corp_results: supabase_upsert('corp_info', corp_results)
    logger.info(f"재무 {len(finance_results)}건 / 기본정보 {len(corp_results)}건 저장")
    logger.info("=== 기업 재무/기본정보 + 투자지표 계산 완료 ===")


if __name__ == '__main__': main()

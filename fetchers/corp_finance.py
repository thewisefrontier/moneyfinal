"""
기업 재무정보 수집기
- 금융위원회_기업재무정보 (공공데이터포털)
- 금융위원회_기업기본정보 (공공데이터포털)
출처: data.go.kr
"""
import logging
import requests
import os
import sys
from datetime import datetime
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service"

# 종목코드(srtnCd) → 종목명 매핑 (API는 종목코드로 조회)
# GetFinaStatInfoService는 crno(사업자번호) 대신 likeSrtnCd(종목코드 유사검색) 사용
MAJOR_STOCKS = [
    {'code': '005930', 'name': '삼성전자'},
    {'code': '000660', 'name': 'SK하이닉스'},
    {'code': '005380', 'name': '현대차'},
    {'code': '035420', 'name': 'NAVER'},
    {'code': '005490', 'name': 'POSCO홀딩스'},
    {'code': '051910', 'name': 'LG화학'},
    {'code': '006400', 'name': '삼성SDI'},
    {'code': '035720', 'name': '카카오'},
    {'code': '000270', 'name': '기아'},
    {'code': '105560', 'name': 'KB금융'},
    {'code': '055550', 'name': '신한지주'},
    {'code': '012330', 'name': '현대모비스'},
    {'code': '028260', 'name': '삼성물산'},
    {'code': '066570', 'name': 'LG전자'},
    {'code': '017670', 'name': 'SK텔레콤'},
    {'code': '030200', 'name': 'KT'},
    {'code': '003550', 'name': 'LG'},
    {'code': '096770', 'name': 'SK이노베이션'},
    {'code': '018260', 'name': '삼성에스디에스'},
    {'code': '009150', 'name': '삼성전기'},
]


def fetch_corp_finance(stock: dict) -> dict | None:
    """기업 재무정보 조회 — likeSrtnCd(종목코드) 파라미터 사용"""
    url = f"{BASE_URL}/GetFinaStatInfoService/getFinaStatInfo"
    now = datetime.now(KST)
    fiscal_year = now.year - 1 if now.month < 4 else now.year

    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 1,
        'pageNo': 1,
        'likeSrtnCd': stock['code'],   # fix: crno(사업자번호) → likeSrtnCd(종목코드)
        'bizYear': str(fiscal_year),
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"{stock['name']}({stock['code']}): 재무 데이터 없음")
            return None
        items = body.get('items', {}).get('item', [])
        item = items[0] if isinstance(items, list) and items else items
        if not item:
            return None

        return {
            'stock_code': stock['code'],
            'corp_name': item.get('corpNm', stock['name']),
            'base_date': f"{fiscal_year}-12-31",
            'fiscal_year': fiscal_year,
            'fiscal_quarter': 4,
            'report_type': '연간',
            'revenue': int(item.get('thstrm', 0) or 0),
            'operating_profit': int(item.get('operPrfi', 0) or 0),
            'net_profit': int(item.get('curNetPrfi', 0) or 0),
            'total_assets': int(item.get('totalAsst', 0) or 0),
            'total_liabilities': int(item.get('totalLblt', 0) or 0),
            'total_equity': int(item.get('totalCptl', 0) or 0),
            'per': float(item.get('pER', 0) or 0),
            'pbr': float(item.get('pBR', 0) or 0),
            'roe': float(item.get('rOE', 0) or 0),
            'eps': float(item.get('ePS', 0) or 0),
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"{stock['name']} 재무정보 오류: {type(e).__name__}")
        return None


def fetch_corp_info(stock: dict) -> dict | None:
    """기업 기본정보 조회 — likeSrtnCd(종목코드) 파라미터 사용"""
    url = f"{BASE_URL}/GetCorpBasicInfoService/getCorpOutline"
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 1,
        'pageNo': 1,
        'likeSrtnCd': stock['code'],   # fix: crno → likeSrtnCd
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"{stock['name']}({stock['code']}): 기본정보 없음")
            return None
        items = body.get('items', {}).get('item', [])
        item = items[0] if isinstance(items, list) and items else items
        if not item:
            return None

        return {
            'stock_code': stock['code'],
            'corp_name': item.get('corpNm', stock['name']),
            'ceo_name': item.get('enpRprFnm', ''),
            'address': item.get('enpBsadr', ''),
            'homepage': item.get('enpHmpgUrl', ''),
            'phone': item.get('enpTlno', ''),
            'industry_name': item.get('enpIndutyNm', ''),
            'listing_date': item.get('enpLstgDt', None),
            'market_type': item.get('enpMrktCtgNm', ''),
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"{stock['name']} 기본정보 오류: {type(e).__name__}")
        return None


def main():
    logger.info("=== 기업 재무/기본정보 수집 시작 ===")
    import time

    finance_results = []
    corp_results = []

    for stock in MAJOR_STOCKS:
        finance = fetch_corp_finance(stock)
        if finance:
            finance_results.append(finance)
            logger.info(f"✅ {stock['name']} 재무 수집")
        time.sleep(0.5)

        corp = fetch_corp_info(stock)
        if corp:
            corp_results.append(corp)
        time.sleep(0.5)

    if finance_results:
        supabase_upsert('corp_finance', finance_results)
        logger.info(f"재무정보 {len(finance_results)}건 저장")

    if corp_results:
        supabase_upsert('corp_info', corp_results)
        logger.info(f"기본정보 {len(corp_results)}건 저장")

    logger.info("=== 기업 재무/기본정보 수집 완료 ===")


if __name__ == '__main__':
    main()

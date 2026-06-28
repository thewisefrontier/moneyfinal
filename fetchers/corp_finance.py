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
from datetime import datetime, timedelta
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, supabase_select, now_kst, today_kst

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service"

# 시가총액 상위 주요 종목 (코스피 대형주 위주)
MAJOR_STOCKS = [
    '005930',  # 삼성전자
    '000660',  # SK하이닉스
    '005380',  # 현대차
    '035420',  # NAVER
    '005490',  # POSCO홀딩스
    '051910',  # LG화학
    '006400',  # 삼성SDI
    '035720',  # 카카오
    '000270',  # 기아
    '105560',  # KB금융
    '055550',  # 신한지주
    '012330',  # 현대모비스
    '028260',  # 삼성물산
    '066570',  # LG전자
    '017670',  # SK텔레콤
    '030200',  # KT
    '003550',  # LG
    '096770',  # SK이노베이션
    '018260',  # 삼성에스디에스
    '009150',  # 삼성전기
]


def fetch_corp_finance(stock_code: str) -> dict | None:
    """기업 재무정보 조회"""
    url = f"{BASE_URL}/GetFinaStatInfoService/getFinaStatInfo"
    now = datetime.now(KST)
    # 최근 사업연도
    fiscal_year = now.year - 1 if now.month < 4 else now.year

    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 1,
        'pageNo': 1,
        'crno': stock_code,
        'bizYear': str(fiscal_year),
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            return None
        items = body.get('items', {}).get('item', [])
        item = items[0] if isinstance(items, list) and items else items
        if not item:
            return None

        return {
            'stock_code': stock_code,
            'corp_name': item.get('corpNm', ''),
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
        logger.error(f"{stock_code} 재무정보 오류: {type(e).__name__}")
        return None


def fetch_corp_info(stock_code: str) -> dict | None:
    """기업 기본정보 조회"""
    url = f"{BASE_URL}/GetCorpBasicInfoService/getCorpOutline"
    params = {
        'serviceKey': API_KEY,
        'resultType': 'json',
        'numOfRows': 1,
        'pageNo': 1,
        'crno': stock_code,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            return None
        items = body.get('items', {}).get('item', [])
        item = items[0] if isinstance(items, list) and items else items
        if not item:
            return None

        return {
            'stock_code': stock_code,
            'corp_name': item.get('corpNm', ''),
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
        logger.error(f"{stock_code} 기본정보 오류: {type(e).__name__}")
        return None


def main():
    logger.info("=== 기업 재무/기본정보 수집 시작 ===")
    import time

    finance_results = []
    corp_results = []

    for code in MAJOR_STOCKS:
        # 재무정보
        finance = fetch_corp_finance(code)
        if finance:
            finance_results.append(finance)
            logger.info(f"✅ {code} 재무: {finance.get('corp_name','')}")
        time.sleep(0.5)  # API 부하 방지

        # 기본정보
        corp = fetch_corp_info(code)
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

"""
공통 유틸리티 - Supabase REST API 헬퍼
"""
import os
import logging
import requests
from urllib.parse import urlencode
from datetime import datetime
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

KST = pytz.timezone('Asia/Seoul')

SUPABASE_URL = os.environ['SUPABASE_URL'].rstrip('/')
SUPABASE_KEY = os.environ['SUPABASE_KEY']

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
}

# 테이블별 upsert conflict 컬럼
CONFLICT_COLUMNS = {
    'rates': 'institution,product_name,category,period',
    'market_indicators': 'indicator_code,reference_date',
    'corporate_alerts': 'company_name,alert_type,disclosure_date',
    'ipo_status': 'company_name,status,request_date',
    'financial_health': 'institution,reference_date',
    'daily_briefing': 'briefing_date',
    'stock_prices': 'stock_code,base_date,market_type',
    'stock_short': 'stock_code,base_date',
    'stock_dividends': 'stock_code,base_date,dividend_type',
    'stock_issuance': 'stock_code,issuance_date,issuance_type',
    'stocks': 'stock_code',
    'corp_info': 'stock_code',
    'corp_finance': 'stock_code,fiscal_year',
}


def data_go_kr_get(url: str, service_key: str, params: dict, timeout: int = 15) -> requests.Response:
    """
    공공데이터포털 API 전용 GET 요청.
    serviceKey는 이미 인코딩된 값이므로 requests params에 넣으면 이중 인코딩됨.
    serviceKey를 URL에 직접 붙여서 단일 인코딩을 보장한다.
    오류 시 상태코드와 응답 본문을 로그에 출력한다.
    """
    query = urlencode(params)
    full_url = f"{url}?serviceKey={service_key}&{query}"
    logging.debug(f"[API 호출] {full_url[:120]}...")
    res = requests.get(full_url, timeout=timeout)
    if res.status_code >= 400:
        logging.error(f"[API 오류] HTTP {res.status_code} | URL: {full_url[:120]}... | 응답: {res.text[:300]}")
    return res


def supabase_upsert(table: str, data: list) -> bool:
    if not data:
        return True

    conflict = CONFLICT_COLUMNS.get(table, '')
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if conflict:
        url += f"?on_conflict={conflict}"

    try:
        res = requests.post(
            url,
            headers={**HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
            json=data,
            timeout=30
        )
        if res.status_code >= 400:
            logging.error(f"[{table}] upsert 실패 ({res.status_code}): {res.text[:200]}")
            res.raise_for_status()
        logging.info(f"[{table}] {len(data)}건 upsert 완료")
        return True
    except requests.exceptions.HTTPError:
        return False
    except Exception as e:
        logging.error(f"[{table}] upsert 오류: {type(e).__name__}")
        return False


def supabase_select(table: str, params: dict = None) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        res = requests.get(
            url,
            headers=HEADERS,
            params=params or {'select': '*'},
            timeout=30
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logging.error(f"[{table}] 조회 실패: {type(e).__name__}")
        return []


def now_kst() -> str:
    return datetime.now(KST).isoformat()


def today_kst() -> str:
    return datetime.now(KST).strftime('%Y-%m-%d')

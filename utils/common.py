"""
공통 유틸리티 - Supabase REST API 헬퍼
"""
import os
import logging
import requests
from urllib.parse import urlencode, quote
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
    serviceKey를 params에 포함해 requests가 한 번만 인코딩하도록 한다.
    (requests의 params= 방식은 safe='' 기준으로 인코딩 — 공공데이터포털 키 형식과 호환)
    """
    all_params = {'serviceKey': service_key, **params}
    res = requests.get(url, params=all_params, timeout=timeout)
    if res.status_code >= 400:
        logging.error(
            f"[API 오류] HTTP {res.status_code} "
            f"| URL: {url} "
            f"| params: {list(params.items())} "
            f"| 응답: {res.text[:300]}"
        )
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

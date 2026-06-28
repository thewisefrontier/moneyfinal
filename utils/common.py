"""
공통 유틸리티 - Supabase REST API 헬퍼
"""
import os
import logging
import requests
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

# 테이블별 upsert conflict 컬럼 지정
CONFLICT_COLUMNS = {
    'rates': 'institution,product_name,category,period',
    'market_indicators': 'indicator_code,reference_date',
    'corporate_alerts': 'company_name,alert_type,disclosure_date',
    'ipo_status': 'company_name,status,request_date',
    'financial_health': 'institution,reference_date',
    'daily_briefing': 'briefing_date',
}


def supabase_upsert(table: str, data: list) -> bool:
    if not data:
        return True
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    
    # 테이블별 conflict 컬럼 지정
    conflict = CONFLICT_COLUMNS.get(table, '')
    prefer = 'resolution=merge-duplicates,return=minimal'
    if conflict:
        prefer += f',on_conflict={conflict}'

    try:
        res = requests.post(
            url,
            headers={**HEADERS, 'Prefer': prefer},
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

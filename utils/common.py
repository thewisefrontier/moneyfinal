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

# URL 마스킹 (로그용)
_URL_MASKED = SUPABASE_URL[:8] + '***' + SUPABASE_URL[-10:] if len(SUPABASE_URL) > 18 else '***'

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
}


def supabase_upsert(table: str, data: list) -> bool:
    if not data:
        return True
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        res = requests.post(
            url,
            headers={**HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
            json=data,
            timeout=30
        )
        if res.status_code >= 400:
            # URL 마스킹 후 로그
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

"""
공통 유틸리티
- Supabase REST API 헬퍼
- 로깅 설정
"""
import os
import json
import logging
import requests
from datetime import datetime
import pytz

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

KST = pytz.timezone('Asia/Seoul')

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'  # upsert 시 중복 무시
}

def supabase_upsert(table: str, data: list) -> bool:
    """Supabase 테이블에 upsert"""
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
        res.raise_for_status()
        logging.info(f"[{table}] {len(data)}건 upsert 완료")
        return True
    except Exception as e:
        logging.error(f"[{table}] upsert 실패: {e}")
        return False

def supabase_select(table: str, params: dict = None) -> list:
    """Supabase 테이블 조회"""
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
        logging.error(f"[{table}] 조회 실패: {e}")
        return []

def now_kst() -> str:
    """현재 KST 시간 ISO 포맷"""
    return datetime.now(KST).isoformat()

def today_kst() -> str:
    """오늘 날짜 KST"""
    return datetime.now(KST).strftime('%Y-%m-%d')

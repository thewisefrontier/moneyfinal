"""
DART 공시 수집기
- 불성실 공시, 임원 보수, 유상증자 등
- 출처: dart.fss.or.kr
"""
import logging
import requests
import os
import sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)

DART_API_KEY = os.environ.get('DART_API_KEY', '')
DART_BASE_URL = "https://opendart.fss.or.kr/api"
KST = pytz.timezone('Asia/Seoul')


def fetch_disclosures(bgn_de: str, end_de: str, pblntf_ty: str = 'A') -> list:
    """DART 공시 목록 수집"""
    url = f"{DART_BASE_URL}/list.json"
    params = {
        'crtfc_key': DART_API_KEY,
        'bgn_de': bgn_de,
        'end_de': end_de,
        'pblntf_ty': pblntf_ty,  # A: 정기공시, B: 주요사항보고, F: 거래소공시
        'page_count': 40
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data.get('status') != '000':
            logger.warning(f"DART API 응답 오류: {data.get('message')}")
            return []
        return data.get('list', [])
    except Exception as e:
        logger.error(f"DART 공시 수집 오류: {e}")
        return []


def fetch_insincere_disclosures() -> list:
    """불성실 공시 법인 수집"""
    url = f"{DART_BASE_URL}/list.json"
    today = datetime.now(KST)
    bgn_de = (today - timedelta(days=30)).strftime('%Y%m%d')
    end_de = today.strftime('%Y%m%d')

    params = {
        'crtfc_key': DART_API_KEY,
        'bgn_de': bgn_de,
        'end_de': end_de,
        'pblntf_detail_ty': 'F001',  # 불성실공시법인
        'page_count': 40
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        data = res.json()
        return data.get('list', [])
    except Exception as e:
        logger.error(f"불성실 공시 수집 오류: {e}")
        return []


def process_disclosures(disclosures: list) -> list:
    """공시 데이터 정제"""
    results = []
    for d in disclosures:
        results.append({
            'company_name': d.get('corp_name', ''),
            'stock_code': d.get('stock_code', ''),
            'alert_type': d.get('report_nm', ''),
            'detail_text': f"{d.get('report_nm', '')} - {d.get('corp_name', '')}",
            'dart_url': f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d.get('rcept_no', '')}",
            'disclosure_date': d.get('rcept_dt', today_kst()),
            'source': 'DART',
            'is_published': False,
            'needs_review': True,
            'fetched_at': now_kst()
        })
    return results


def main():
    logger.info("=== DART 공시 수집 시작 ===")
    today = datetime.now(KST)
    bgn_de = (today - timedelta(days=7)).strftime('%Y%m%d')
    end_de = today.strftime('%Y%m%d')

    all_disclosures = []

    # 주요사항보고 (유상증자, CB 발행 등)
    major = fetch_disclosures(bgn_de, end_de, pblntf_ty='B')
    logger.info(f"주요사항보고 {len(major)}건")
    all_disclosures.extend(major)

    # 불성실 공시
    insincere = fetch_insincere_disclosures()
    logger.info(f"불성실 공시 {len(insincere)}건")
    all_disclosures.extend(insincere)

    if all_disclosures:
        processed = process_disclosures(all_disclosures)
        supabase_upsert('corporate_alerts', processed)

    logger.info(f"=== DART 수집 완료: {len(all_disclosures)}건 ===")


if __name__ == '__main__':
    main()

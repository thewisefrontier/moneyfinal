"""
금감원 금융상품한눈에 연금저축 수집기
- annuitySavingProductsSearch -> annuity_savings (baseList만 저장, 수령액 옵션 제외)
출처: finlife.fss.or.kr (공식 명세 확인 완료)
"""
import logging
import requests
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst

logger = logging.getLogger(__name__)
FINLIFE_API_KEY = os.environ.get('FINLIFE_API_KEY', '')
FSS_BASE_URL = "https://finlife.fss.or.kr/finlifeapi"

SECTOR_MAP = {
    '020000': '은행',
    '050000': '보험',
    '060000': '금융투자',
}


def _f(v):
    try:
        return float(v) if v is not None and str(v).strip() != '' else None
    except (ValueError, TypeError):
        return None


def _i(v):
    try:
        return int(v) if v is not None and str(v).strip() != '' else None
    except (ValueError, TypeError):
        return None


def fetch_page(top_fin_grp_no: str, page_no: int):
    url = f"{FSS_BASE_URL}/annuitySavingProductsSearch.json"
    params = {'auth': FINLIFE_API_KEY, 'topFinGrpNo': top_fin_grp_no, 'pageNo': page_no}
    for attempt in range(3):
        try:
            res = requests.get(url, params=params, timeout=30)
            res.raise_for_status()
            result = res.json().get('result', {})
            if result.get('err_cd') != '000':
                logger.error(f"FSS API 오류(연금저축): {result.get('err_msg')}")
                return None
            return result
        except requests.exceptions.Timeout:
            logger.warning(f"FSS API 타임아웃 연금저축 (시도 {attempt+1}/3)")
            time.sleep(5)
        except Exception as e:
            logger.error(f"FSS API 수집 오류(연금저축): {type(e).__name__}")
            return None
    return None


def collect(grp: str) -> list:
    sector = SECTOR_MAP.get(grp, '')
    rows = []
    page_no = 1
    while True:
        result = fetch_page(grp, page_no)
        if result is None:
            break
        for p in result.get('baseList', []):
            rows.append({
                'dcls_month': p.get('dcls_month', ''),
                'fin_co_no': p.get('fin_co_no', ''),
                'kor_co_nm': p.get('kor_co_nm', ''),
                'fin_prdt_cd': p.get('fin_prdt_cd', ''),
                'fin_prdt_nm': p.get('fin_prdt_nm', ''),
                'join_way': p.get('join_way', ''),
                'pnsn_kind': str(p.get('pnsn_kind') or ''),
                'pnsn_kind_nm': p.get('pnsn_kind_nm', ''),
                'prdt_type': str(p.get('prdt_type') or ''),
                'prdt_type_nm': p.get('prdt_type_nm', ''),
                'sale_strt_day': p.get('sale_strt_day', ''),
                'mntn_cnt': _i(p.get('mntn_cnt')),
                'avg_prft_rate': _f(p.get('avg_prft_rate')),
                'dcls_rate': _f(p.get('dcls_rate')),
                'guar_rate': _f(p.get('guar_rate')),
                'btrm_prft_rate_1': _f(p.get('btrm_prft_rate_1')),
                'btrm_prft_rate_2': _f(p.get('btrm_prft_rate_2')),
                'btrm_prft_rate_3': _f(p.get('btrm_prft_rate_3')),
                'etc': p.get('etc', ''),
                'sale_co': p.get('sale_co', ''),
                'sector': sector,
                'dcls_strt_day': p.get('dcls_strt_day', ''),
                'source': '금융감독원 금융상품한눈에',
                'source_url': 'https://finlife.fss.or.kr',
                'fetched_at': now_kst(),
            })
        max_page = int(result.get('max_page_no') or 1)
        if page_no >= max_page:
            break
        page_no += 1
        time.sleep(1)
    return rows


def main():
    logger.info("=== 연금저축 수집 시작 ===")
    all_rows = []
    for grp in SECTOR_MAP:
        rows = collect(grp)
        logger.info(f"연금저축 {SECTOR_MAP[grp]} {len(rows)}건 수집")
        all_rows.extend(rows)
    seen = {}
    for r in all_rows:
        seen[(r['fin_co_no'], r['fin_prdt_cd'])] = r
    deduped = list(seen.values())
    logger.info(f"중복 제거 후 {len(deduped)}건")
    if deduped:
        supabase_upsert('annuity_savings', deduped)
    logger.info("=== 연금저축 수집 완료 ===")


if __name__ == '__main__':
    main()

"""
금감원 금융상품한눈에 금리 수집기
출처: finlife.fss.or.kr
공식 명세: /finlife/api/fdrmDpstApi/list.do?menuNo=700052 (예금)
          /finlife/api/fdrmEntyApi/list.do?menuNo=700053 (적금)
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

CATEGORY_MAP = {
    'depositProductsSearch': '예금',
    'savingProductsSearch': '적금',
}
SECTOR_MAP = {
    '020000': '은행',
    '030300': '저축은행',
}


def _to_int(v):
    try:
        return int(v) if v is not None and str(v).strip() != '' else None
    except (ValueError, TypeError):
        return None


def fetch_page(product_type: str, top_fin_grp_no: str, page_no: int):
    """단일 페이지 조회. (result dict | None) 반환"""
    url = f"{FSS_BASE_URL}/{product_type}.json"
    params = {
        'auth': FINLIFE_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': page_no
    }
    for attempt in range(3):
        try:
            res = requests.get(url, params=params, timeout=30)
            res.raise_for_status()
            data = res.json()
            result = data.get('result', {})
            if result.get('err_cd') != '000':
                logger.error(f"FSS API 오류: {result.get('err_msg')}")
                return None
            return result
        except requests.exceptions.Timeout:
            logger.warning(f"FSS API 타임아웃 (시도 {attempt+1}/3)")
            time.sleep(5)
        except Exception as e:
            logger.error(f"FSS API 수집 오류: {type(e).__name__}")
            return None
    return None


def fetch_fss_products(product_type: str, top_fin_grp_no: str = '020000') -> list:
    """max_page_no 기반 전체 페이지 수집"""
    results = []
    category = CATEGORY_MAP.get(product_type, '예금')
    sector = SECTOR_MAP.get(top_fin_grp_no, '')
    page_no = 1
    while True:
        result = fetch_page(product_type, top_fin_grp_no, page_no)
        if result is None:
            break
        base_list = result.get('baseList', [])
        option_list = result.get('optionList', [])
        for product in base_list:
            fin_prdt_cd = product.get('fin_prdt_cd')
            options = [o for o in option_list if o.get('fin_prdt_cd') == fin_prdt_cd]
            for opt in options:
                rate = float(opt.get('intr_rate', 0) or 0)
                max_rate = float(opt.get('intr_rate2', 0) or 0)
                results.append({
                    'institution': product.get('kor_co_nm', ''),
                    'product_name': product.get('fin_prdt_nm', ''),
                    'category': category,
                    'sector': sector,
                    'rate': rate,
                    'max_rate': max_rate,
                    'period': f"{opt.get('save_trm', '')}개월",
                    'join_method': product.get('join_way', ''),
                    'join_deny': _to_int(product.get('join_deny')),
                    'join_member': product.get('join_member', ''),
                    'spcl_cnd': product.get('spcl_cnd', ''),
                    'etc_note': product.get('etc_note', ''),
                    'max_limit': _to_int(product.get('max_limit')),
                    'mtrt_int': product.get('mtrt_int', ''),
                    'intr_rate_type_nm': opt.get('intr_rate_type_nm', ''),
                    'rsrv_type_nm': opt.get('rsrv_type_nm', ''),
                    'dcls_strt_day': product.get('dcls_strt_day', ''),
                    'dcls_end_day': product.get('dcls_end_day', ''),
                    'source': '금융감독원 금융상품한눈에',
                    'source_url': 'https://finlife.fss.or.kr',
                    'fetched_at': now_kst()
                })
        max_page = _to_int(result.get('max_page_no')) or 1
        if page_no >= max_page:
            break
        page_no += 1
        time.sleep(1)
    return results


def main():
    logger.info("=== 은행 금리 수집 시작 ===")
    all_rates = []
    for grp in ['020000', '030300']:
        for product_type in ['depositProductsSearch', 'savingProductsSearch']:
            rates = fetch_fss_products(product_type, grp)
            logger.info(f"{SECTOR_MAP[grp]} {CATEGORY_MAP[product_type]} {len(rates)}건 수집")
            all_rates.extend(rates)
    valid = [r for r in all_rates if r['rate'] > 0]
    seen = {}
    for r in valid:
        key = (r['institution'], r['product_name'], r['category'], r['period'])
        seen[key] = r
    deduped = list(seen.values())
    logger.info(f"중복 제거 후 {len(deduped)}건")
    if deduped:
        supabase_upsert('rates', deduped)
    logger.info("=== 은행 금리 수집 완료 ===")


if __name__ == '__main__':
    main()

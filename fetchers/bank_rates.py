"""
은행연합회/금감원 금리 수집기 (디버그 버전)
"""
import logging
import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst

logger = logging.getLogger(__name__)
FSS_API_KEY = os.environ.get('FSS_API_KEY', '')
FSS_BASE_URL = "https://finlife.fss.or.kr/finlifeapi"

CATEGORY_MAP = {
    'depositProductsSearch': '예금',
    'savingProductsSearch': '적금',
}

def fetch_fss_products(product_type: str, top_fin_grp_no: str = '020000') -> list:
    results = []
    url = f"{FSS_BASE_URL}/{product_type}.json"
    params = {
        'auth': FSS_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': 1
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        logger.info(f"FSS API 상태코드: {res.status_code}")
        logger.info(f"FSS API 응답 앞부분: {res.text[:300]}")
        res.raise_for_status()
        data = res.json()

        base_list = data.get('result', {}).get('baseList', [])
        option_list = data.get('result', {}).get('optionList', [])
        logger.info(f"baseList: {len(base_list)}건, optionList: {len(option_list)}건")

        for product in base_list:
            fin_prdt_cd = product.get('fin_prdt_cd')
            options = [o for o in option_list if o.get('fin_prdt_cd') == fin_prdt_cd]
            for opt in options:
                rate = float(opt.get('intr_rate', 0) or 0)
                max_rate = float(opt.get('intr_rate2', 0) or 0)
                results.append({
                    'institution': product.get('kor_co_nm', ''),
                    'product_name': product.get('fin_prdt_nm', ''),
                    'category': CATEGORY_MAP.get(product_type, '예금'),
                    'rate': rate,
                    'max_rate': max_rate,
                    'period': f"{opt.get('save_trm', '')}개월",
                    'join_method': product.get('join_way', ''),
                    'source': '금융감독원 금융상품한눈에',
                    'source_url': 'https://finlife.fss.or.kr',
                    'fetched_at': now_kst()
                })
    except Exception as e:
        logger.error(f"FSS API 오류: {e}")
    return results


def main():
    logger.info("=== 은행 금리 수집 시작 ===")
    logger.info(f"FSS_API_KEY 길이: {len(FSS_API_KEY)} (앞4자리: {FSS_API_KEY[:4] if FSS_API_KEY else '없음'})")
    all_rates = []

    for product_type in ['depositProductsSearch', 'savingProductsSearch']:
        rates = fetch_fss_products(product_type, '020000')
        logger.info(f"{CATEGORY_MAP.get(product_type)} {len(rates)}건 수집")
        all_rates.extend(rates)

    savings = fetch_fss_products('depositProductsSearch', '030300')
    logger.info(f"저축은행 {len(savings)}건 수집")
    all_rates.extend(savings)

    valid = [r for r in all_rates if r['rate'] > 0]
    logger.info(f"유효 금리 총 {len(valid)}건")

    if valid:
        supabase_upsert('rates', valid)

    logger.info("=== 은행 금리 수집 완료 ===")


if __name__ == '__main__':
    main()

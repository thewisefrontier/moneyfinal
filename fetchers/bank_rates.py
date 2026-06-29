"""
금감원 금융상품한눈에 금리 수집기
출처: finlife.fss.or.kr
"""
import logging
import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst

logger = logging.getLogger(__name__)
FINLIFE_API_KEY = os.environ.get('FINLIFE_API_KEY', '')
FSS_BASE_URL = "https://finlife.fss.or.kr/finlifeapi"

CATEGORY_MAP = {
    'depositProductsSearch': '예금',
    'savingProductsSearch': '적금',
}


def fetch_fss_products(product_type: str, top_fin_grp_no: str = '020000') -> list:
    results = []
    url = f"{FSS_BASE_URL}/{product_type}.json"
    params = {
        'auth': FINLIFE_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': 1
    }
    for attempt in range(3):
        try:
            res = requests.get(url, params=params, timeout=30)
            res.raise_for_status()
            break
        except requests.exceptions.Timeout:
            logger.warning(f"FSS API 타임아웃 (시도 {attempt+1}/3)")
            if attempt == 2:
                logger.error("FSS API 최대 재시도 초과")
                return results
            import time; time.sleep(5)
        except Exception as e:
            logger.error(f"FSS API 수집 오류: {type(e).__name__}")
            return results
    try:
        data = res.json()
        result = data.get('result', {})
        if result.get('err_cd') != '000':
            logger.error(f"FSS API 오류: {result.get('err_msg')}")
            return []
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
        logger.error(f"FSS API 데이터 파싱 오류: {type(e).__name__}")
    return results


def main():
    logger.info("=== 은행 금리 수집 시작 ===")
    all_rates = []
    for product_type in ['depositProductsSearch', 'savingProductsSearch']:
        rates = fetch_fss_products(product_type, '020000')
        logger.info(f"{CATEGORY_MAP.get(product_type)} {len(rates)}건 수집")
        all_rates.extend(rates)
    for product_type in ['depositProductsSearch', 'savingProductsSearch']:
        rates = fetch_fss_products(product_type, '030300')
        logger.info(f"저축은행 {CATEGORY_MAP.get(product_type)} {len(rates)}건 수집")
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

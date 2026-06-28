"""
은행연합회 소비자포털 금리 수집기
- 적금/예금/파킹 금리 수집
- 출처: https://consumer.fss.or.kr
"""
import logging
import requests
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst

logger = logging.getLogger(__name__)

# 금융감독원 금융상품 한눈에 API (공공데이터)
FSS_BASE_URL = "https://finlife.fss.or.kr/finlifeapi"

# 금감원 금융상품통합비교공시 API 키 (공공데이터포털에서 발급)
FSS_API_KEY = os.environ.get('FSS_API_KEY', '')

CATEGORY_MAP = {
    'depositProductsSearch': '예금',
    'savingProductsSearch': '적금',
}

def fetch_fss_products(product_type: str) -> list:
    """금감원 API로 예금/적금 상품 수집"""
    results = []
    page = 1

    while True:
        url = f"{FSS_BASE_URL}/{product_type}.json"
        params = {
            'auth': FSS_API_KEY,
            'topFinGrpNo': '020000',  # 은행
            'pageNo': page
        }
        try:
            res = requests.get(url, params=params, timeout=15)
            res.raise_for_status()
            data = res.json()

            base_list = data.get('result', {}).get('baseList', [])
            option_list = data.get('result', {}).get('optionList', [])

            if not base_list:
                break

            # 기본 상품 정보 + 금리 옵션 매핑
            for product in base_list:
                fin_prdt_cd = product.get('fin_prdt_cd')
                options = [o for o in option_list if o.get('fin_prdt_cd') == fin_prdt_cd]

                for opt in options:
                    results.append({
                        'institution': product.get('kor_co_nm', ''),
                        'product_name': product.get('fin_prdt_nm', ''),
                        'category': CATEGORY_MAP.get(product_type, '예금'),
                        'rate': float(opt.get('intr_rate', 0) or 0),
                        'max_rate': float(opt.get('intr_rate2', 0) or 0),
                        'period': f"{opt.get('save_trm', '')}개월",
                        'join_method': product.get('join_way', ''),
                        'source': '금융감독원 금융상품한눈에',
                        'source_url': 'https://finlife.fss.or.kr',
                        'fetched_at': now_kst()
                    })

            total_count = data.get('result', {}).get('total_count', 0)
            if page * 20 >= total_count:
                break
            page += 1

        except Exception as e:
            logger.error(f"FSS API 오류 (page {page}): {e}")
            break

    return results


def fetch_savings_bank_rates() -> list:
    """저축은행 금리 (금감원 API)"""
    results = []
    for product_type in ['depositProductsSearch', 'savingProductsSearch']:
        params = {
            'auth': FSS_API_KEY,
            'topFinGrpNo': '030300',  # 저축은행
            'pageNo': 1
        }
        url = f"{FSS_BASE_URL}/{product_type}.json"
        try:
            res = requests.get(url, params=params, timeout=15)
            data = res.json()
            base_list = data.get('result', {}).get('baseList', [])
            option_list = data.get('result', {}).get('optionList', [])

            for product in base_list:
                fin_prdt_cd = product.get('fin_prdt_cd')
                options = [o for o in option_list if o.get('fin_prdt_cd') == fin_prdt_cd]
                for opt in options:
                    results.append({
                        'institution': product.get('kor_co_nm', ''),
                        'product_name': product.get('fin_prdt_nm', ''),
                        'category': CATEGORY_MAP.get(product_type, '예금'),
                        'rate': float(opt.get('intr_rate', 0) or 0),
                        'max_rate': float(opt.get('intr_rate2', 0) or 0),
                        'period': f"{opt.get('save_trm', '')}개월",
                        'join_method': product.get('join_way', ''),
                        'source': '금융감독원 금융상품한눈에',
                        'source_url': 'https://finlife.fss.or.kr',
                        'fetched_at': now_kst()
                    })
        except Exception as e:
            logger.error(f"저축은행 금리 수집 오류: {e}")

    return results


def main():
    logger.info("=== 은행 금리 수집 시작 ===")
    all_rates = []

    # 은행 예금/적금
    for product_type in ['depositProductsSearch', 'savingProductsSearch']:
        rates = fetch_fss_products(product_type)
        logger.info(f"{CATEGORY_MAP.get(product_type)} {len(rates)}건 수집")
        all_rates.extend(rates)

    # 저축은행
    savings_rates = fetch_savings_bank_rates()
    logger.info(f"저축은행 {len(savings_rates)}건 수집")
    all_rates.extend(savings_rates)

    # 유효한 금리만 필터 (0% 제외)
    valid_rates = [r for r in all_rates if r['rate'] > 0]
    logger.info(f"유효 금리 총 {len(valid_rates)}건")

    # Supabase upsert
    if valid_rates:
        supabase_upsert('rates', valid_rates)

    logger.info("=== 은행 금리 수집 완료 ===")


if __name__ == '__main__':
    main()

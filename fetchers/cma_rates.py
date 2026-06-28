"""
CMA / 파킹통장 금리 수집기
- 금감원 금융상품한눈에 API (finlife.fss.or.kr)
- 입출금 / CMA 상품 수집
"""
import logging, requests, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst

logger = logging.getLogger(__name__)
FSS_API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://finlife.fss.or.kr/finlifeapi"

# 금융권역코드
# 020000: 은행, 030300: 저축은행, 050000: 증권사
GROUPS = [
    ('020000', '파킹통장'),
    ('050000', 'CMA'),
]


def fetch_demand_products(top_fin_grp_no: str, category: str) -> list:
    """입출금/CMA 상품 수집"""
    url = f"{BASE_URL}/demandDepositProductsSearch.json"
    params = {
        'auth': FSS_API_KEY,
        'topFinGrpNo': top_fin_grp_no,
        'pageNo': 1
    }
    results = []
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        result = data.get('result', {})
        if result.get('err_cd') != '000':
            logger.warning(f"{category} 오류: {result.get('err_msg')}")
            return []
        base_list = result.get('baseList', [])
        option_list = result.get('optionList', [])
        for product in base_list:
            fin_prdt_cd = product.get('fin_prdt_cd')
            options = [o for o in option_list if o.get('fin_prdt_cd') == fin_prdt_cd]
            for opt in options:
                rate = float(opt.get('intr_rate', 0) or 0)
                if rate <= 0:
                    continue
                results.append({
                    'institution': product.get('kor_co_nm', ''),
                    'product_name': product.get('fin_prdt_nm', ''),
                    'category': category,
                    'rate': rate,
                    'max_rate': float(opt.get('intr_rate2', rate) or rate),
                    'period': '수시',
                    'join_method': product.get('join_way', ''),
                    'source': '금융감독원 금융상품한눈에',
                    'source_url': 'https://finlife.fss.or.kr',
                    'fetched_at': now_kst()
                })
    except Exception as e:
        logger.error(f"{category} 수집 오류: {type(e).__name__}")
    return results


def main():
    logger.info("=== CMA/파킹통장 금리 수집 시작 ===")
    all_rates = []
    for grp, category in GROUPS:
        rates = fetch_demand_products(grp, category)
        logger.info(f"{category}: {len(rates)}건")
        all_rates.extend(rates)
    if all_rates:
        supabase_upsert('rates', all_rates)
    logger.info(f"=== CMA/파킹통장 수집 완료: {len(all_rates)}건 ===")


if __name__ == '__main__':
    main()

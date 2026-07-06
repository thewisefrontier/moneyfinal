"""
금감원 금융상품한눈에 대출상품 수집기
- 주택담보대출: mortgageLoanProductsSearch -> mortgage_loans
- 전세자금대출: rentHouseLoanProductsSearch -> rent_loans
- 개인신용대출: creditLoanProductsSearch -> credit_loans
- 개인사업자대출: busiLoanProductsSearch -> business_loans
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
    '030300': '저축은행',
}
SOURCE_FIELDS = {
    'source': '금융감독원 금융상품한눈에',
    'source_url': 'https://finlife.fss.or.kr',
}


def _f(v):
    """빈문자열/None 안전 float 변환"""
    try:
        return float(v) if v is not None and str(v).strip() != '' else None
    except (ValueError, TypeError):
        return None


def fetch_page(service: str, top_fin_grp_no: str, page_no: int):
    url = f"{FSS_BASE_URL}/{service}.json"
    params = {'auth': FINLIFE_API_KEY, 'topFinGrpNo': top_fin_grp_no, 'pageNo': page_no}
    for attempt in range(3):
        try:
            res = requests.get(url, params=params, timeout=30)
            res.raise_for_status()
            result = res.json().get('result', {})
            if result.get('err_cd') != '000':
                logger.error(f"FSS API 오류({service}): {result.get('err_msg')}")
                return None
            return result
        except requests.exceptions.Timeout:
            logger.warning(f"FSS API 타임아웃 {service} (시도 {attempt+1}/3)")
            time.sleep(5)
        except Exception as e:
            logger.error(f"FSS API 수집 오류({service}): {type(e).__name__}")
            return None
    return None


def fetch_all_pages(service: str, top_fin_grp_no: str):
    """전체 페이지의 (baseList, optionList) 병합 반환"""
    base_all, opt_all = [], []
    page_no = 1
    while True:
        result = fetch_page(service, top_fin_grp_no, page_no)
        if result is None:
            break
        base_all.extend(result.get('baseList', []))
        opt_all.extend(result.get('optionList', []))
        max_page = int(result.get('max_page_no') or 1)
        if page_no >= max_page:
            break
        page_no += 1
        time.sleep(1)
    return base_all, opt_all


def _base_common(p: dict, sector: str) -> dict:
    return {
        'dcls_month': p.get('dcls_month', ''),
        'fin_co_no': p.get('fin_co_no', ''),
        'kor_co_nm': p.get('kor_co_nm', ''),
        'fin_prdt_cd': p.get('fin_prdt_cd', ''),
        'fin_prdt_nm': p.get('fin_prdt_nm', ''),
        'join_way': p.get('join_way', ''),
        'sector': sector,
        'dcls_strt_day': p.get('dcls_strt_day', ''),
        'fetched_at': now_kst(),
        **SOURCE_FIELDS,
    }


def collect_mortgage(grp: str) -> list:
    base_list, opt_list = fetch_all_pages('mortgageLoanProductsSearch', grp)
    sector = SECTOR_MAP.get(grp, '')
    rows = []
    base_map = {p.get('fin_prdt_cd'): p for p in base_list}
    for o in opt_list:
        p = base_map.get(o.get('fin_prdt_cd'))
        if not p:
            continue
        rows.append({
            **_base_common(p, sector),
            'loan_inci_expn': p.get('loan_inci_expn', ''),
            'erly_rpay_fee': p.get('erly_rpay_fee', ''),
            'dly_rate': p.get('dly_rate', ''),
            'loan_lmt': p.get('loan_lmt', ''),
            'mrtg_type': o.get('mrtg_type') or '',
            'mrtg_type_nm': o.get('mrtg_type_nm', ''),
            'rpay_type': o.get('rpay_type') or '',
            'rpay_type_nm': o.get('rpay_type_nm', ''),
            'lend_rate_type': o.get('lend_rate_type') or '',
            'lend_rate_type_nm': o.get('lend_rate_type_nm', ''),
            'lend_rate_min': _f(o.get('lend_rate_min')),
            'lend_rate_max': _f(o.get('lend_rate_max')),
            'lend_rate_avg': _f(o.get('lend_rate_avg')),
        })
    return rows


def collect_rent(grp: str) -> list:
    base_list, opt_list = fetch_all_pages('rentHouseLoanProductsSearch', grp)
    sector = SECTOR_MAP.get(grp, '')
    rows = []
    base_map = {p.get('fin_prdt_cd'): p for p in base_list}
    for o in opt_list:
        p = base_map.get(o.get('fin_prdt_cd'))
        if not p:
            continue
        rows.append({
            **_base_common(p, sector),
            'loan_inci_expn': p.get('loan_inci_expn', ''),
            'erly_rpay_fee': p.get('erly_rpay_fee', ''),
            'dly_rate': p.get('dly_rate', ''),
            'loan_lmt': p.get('loan_lmt', ''),
            'rpay_type': o.get('rpay_type') or '',
            'rpay_type_nm': o.get('rpay_type_nm', ''),
            'lend_rate_type': o.get('lend_rate_type') or '',
            'lend_rate_type_nm': o.get('lend_rate_type_nm', ''),
            'lend_rate_min': _f(o.get('lend_rate_min')),
            'lend_rate_max': _f(o.get('lend_rate_max')),
            'lend_rate_avg': _f(o.get('lend_rate_avg')),
        })
    return rows


CRDT_GRADS = ['1', '4', '5', '6', '10', '11', '12', '13', 'avg']


def collect_credit(grp: str) -> list:
    base_list, opt_list = fetch_all_pages('creditLoanProductsSearch', grp)
    sector = SECTOR_MAP.get(grp, '')
    rows = []
    # base와 option은 fin_prdt_cd + crdt_prdt_type 조합으로 연결
    base_map = {(p.get('fin_prdt_cd'), str(p.get('crdt_prdt_type'))): p for p in base_list}
    for o in opt_list:
        p = base_map.get((o.get('fin_prdt_cd'), str(o.get('crdt_prdt_type'))))
        if not p:
            continue
        row = {
            **_base_common(p, sector),
            'cb_name': p.get('cb_name', ''),
            'crdt_prdt_type': str(p.get('crdt_prdt_type') or ''),
            'crdt_prdt_type_nm': p.get('crdt_prdt_type_nm', ''),
            'crdt_lend_rate_type': o.get('crdt_lend_rate_type') or '',
            'crdt_lend_rate_type_nm': o.get('crdt_lend_rate_type_nm', ''),
        }
        for g in CRDT_GRADS:
            row[f'crdt_grad_{g}'] = _f(o.get(f'crdt_grad_{g}'))
        rows.append(row)
    return rows


def collect_business(grp: str) -> list:
    base_list, opt_list = fetch_all_pages('busiLoanProductsSearch', grp)
    sector = SECTOR_MAP.get(grp, '')
    rows = []
    opt_map = {o.get('fin_prdt_cd'): o for o in opt_list}
    for p in base_list:
        o = opt_map.get(p.get('fin_prdt_cd'), {})
        row = {
            **_base_common(p, sector),
            'fin_prdt_type': str(p.get('fin_prdt_type') or ''),
            'fin_prdt_type_nm': p.get('fin_prdt_type_nm', ''),
            'loan_type': p.get('loan_type', ''),
            'rpay_type': p.get('rpay_type', ''),
            'lend_rate_type': p.get('lend_rate_type', ''),
            'use_way': p.get('use_way', ''),
            'loan_limit': p.get('loan_limit', ''),
            'loan_limit_detl': p.get('loan_limit_detl', ''),
            'join_deny': p.get('join_deny', ''),
            'join_deny_detl': p.get('join_deny_detl', ''),
            'spcl_rate': p.get('spcl_rate', ''),
            'loan_term': p.get('loan_term', ''),
            'erly_rpay_fee': p.get('erly_rpay_fee', ''),
            'loan_inci_expn': p.get('loan_inci_expn', ''),
            'dly_rate': p.get('dly_rate', ''),
            'cb_name': p.get('cb_name', ''),
            'lend_rate_min': _f(o.get('lend_rate_min')),
            'lend_rate_max': _f(o.get('lend_rate_max')),
            'lend_rate_avg': _f(o.get('lend_rate_avg')),
        }
        for v in ('val1', 'val2', 'val3'):
            for g in ('1', '2', '3', '4', '5', '6', '7', '8', 'avg'):
                row[f'{v}_grad_{g}'] = _f(o.get(f'{v}_grad_{g}'))
        rows.append(row)
    return rows


def _dedupe(rows: list, key_fields: tuple) -> list:
    seen = {}
    for r in rows:
        seen[tuple(r.get(k) for k in key_fields)] = r
    return list(seen.values())


TARGETS = [
    ('mortgage_loans', collect_mortgage,
     ('fin_co_no', 'fin_prdt_cd', 'mrtg_type', 'rpay_type', 'lend_rate_type')),
    ('rent_loans', collect_rent,
     ('fin_co_no', 'fin_prdt_cd', 'rpay_type', 'lend_rate_type')),
    ('credit_loans', collect_credit,
     ('fin_co_no', 'fin_prdt_cd', 'crdt_prdt_type', 'crdt_lend_rate_type')),
    ('business_loans', collect_business,
     ('fin_co_no', 'fin_prdt_cd')),
]


def main():
    logger.info("=== 대출상품 수집 시작 ===")
    for table, collector, key_fields in TARGETS:
        all_rows = []
        for grp in SECTOR_MAP:
            rows = collector(grp)
            logger.info(f"[{table}] {SECTOR_MAP[grp]} {len(rows)}건 수집")
            all_rows.extend(rows)
        deduped = _dedupe(all_rows, key_fields)
        logger.info(f"[{table}] 중복 제거 후 {len(deduped)}건")
        if deduped:
            supabase_upsert(table, deduped)
    logger.info("=== 대출상품 수집 완료 ===")


if __name__ == '__main__':
    main()

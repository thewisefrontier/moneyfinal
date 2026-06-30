"""
금융투자협회 종합통계정보 수집기
- 금융위원회_금융투자협회종합통계정보 (공공데이터포털)
- 서비스: GetKofiaStatisticsInfoService
- 8개 오퍼레이션: 신탁규모/펀드순자산/CMA현황/신용공여/증시자금/DLS·DLB/ELS·ELB/해외파생거래
출처: 오픈API 활용자가이드_금융위원회_금융투자협회종합통계정보.docx
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetKofiaStatisticsInfoService"


def get_recent_yyyymm(months_back: int = 1) -> str:
    """최근 N개월 전 기준년월 (YYYYMM) - 월간 통계용"""
    now = datetime.now(KST)
    target = now.replace(day=1) - timedelta(days=30 * months_back)
    return target.strftime('%Y%m')


def get_recent_date(days_back: int = 7) -> str:
    """최근 N일 전 날짜 (YYYYMMDD) - 일간 통계용"""
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')


def fetch_operation(operation: str, params: dict) -> list:
    """공통 오퍼레이션 호출 헬퍼"""
    url = f"{BASE_URL}/{operation}"
    base_params = {'resultType': 'json', 'numOfRows': 50, 'pageNo': 1}
    base_params.update(params)
    try:
        res = data_go_kr_get(url, API_KEY, base_params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"{operation}: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        return items
    except Exception as e:
        logger.error(f"{operation} 수집 오류: {type(e).__name__} - {e}")
        return []


def collect_trust_scale() -> list:
    """① 업권별신탁규모 (getTrustScaleInfo) - basYm 기준년월"""
    items = fetch_operation('getTrustScaleInfo', {'basYm': get_recent_yyyymm(2)})
    results = []
    for item in items:
        val = float(item.get('val', 0) or 0)
        if val <= 0:
            continue
        results.append({
            'indicator_code': f"KOFIA_TRUST_{item.get('bzds','')}_{item.get('iqBs','')}"[:50],
            'indicator_name': f"{item.get('bzds','')} {item.get('tstCtg','')} {item.get('iqBs','')}",
            'category': '금융투자',
            'value': val,
            'unit': '건' if item.get('iqBs') in ('고객수', '계약수') else '백만원',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        })
    return results


def collect_fund_net_asset() -> list:
    """② 펀드순자산총액 (getFundTotalNetEssetInfo) - basDt 기준일자"""
    items = fetch_operation('getFundTotalNetEssetInfo', {'basDt': get_recent_date(3)})
    results = []
    for item in items:
        amt = float(item.get('nPptTotAmt', 0) or 0)
        if amt <= 0:
            continue
        results.append({
            'indicator_code': f"KOFIA_FUND_{item.get('ctg','')}_{item.get('tstMthdCtg','')}"[:50],
            'indicator_name': f"펀드 {item.get('ctg','')} ({item.get('tstMthdCtg','')})",
            'category': '금융투자',
            'value': amt,
            'unit': '원',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        })
    return results


def collect_cma_status() -> list:
    """③ 일자별CMA현황 (getCMAStatus) - basDt 기준일자"""
    items = fetch_operation('getCMAStatus', {'basDt': get_recent_date(5)})
    results = []
    for item in items:
        bal = float(item.get('actBal', 0) or 0)
        if bal <= 0:
            continue
        results.append({
            'indicator_code': f"KOFIA_CMA_{item.get('mngInvTgt','')}_{item.get('invrCtg','')}"[:50],
            'indicator_name': f"CMA {item.get('mngInvTgt','')} ({item.get('invrCtg','')})",
            'category': 'CMA',
            'value': bal,
            'unit': '원',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'summary_text': f"계좌수 {item.get('actCnt','')}건, 증권사 {item.get('scrtCmpyCnt','')}개",
            'fetched_at': now_kst()
        })
    return results


def collect_credit_balance() -> list:
    """④ 신용공여잔고추이 (getGrantingOfCreditBalanceInfo) - basDt 기준일자"""
    items = fetch_operation('getGrantingOfCreditBalanceInfo', {'basDt': get_recent_date(5)})
    results = []
    for item in items:
        whl = float(item.get('crdTrFingWhl', 0) or 0)
        if whl <= 0:
            continue
        results.append({
            'indicator_code': 'KOFIA_CREDIT_BALANCE',
            'indicator_name': '신용공여잔고 (신용거래융자 전체)',
            'category': '금융투자',
            'value': whl,
            'unit': '백만원',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        })
    return results


def collect_market_capital() -> list:
    """⑤ 증시자금추이 (GetSecuritiesMarketTotalCapitalInfo) - basDt 기준일자"""
    items = fetch_operation('GetSecuritiesMarketTotalCapitalInfo', {'basDt': get_recent_date(5)})
    results = []
    for item in items:
        amt = float(item.get('invrDpsgAmt', 0) or 0)
        if amt <= 0:
            continue
        results.append({
            'indicator_code': 'KOFIA_INVESTOR_DEPOSIT',
            'indicator_name': '투자자예탁금',
            'category': '금융투자',
            'value': amt,
            'unit': '원',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        })
    return results


def collect_dls_dlb() -> list:
    """⑥ DLS/DLB발행동향 (getDLSAndDLBInfo) - basDt 기준년월(YYYYMM)"""
    items = fetch_operation('getDLSAndDLBInfo', {'basDt': get_recent_yyyymm(2)})
    results = []
    for item in items:
        amt = float(item.get('amt', 0) or 0)
        if amt <= 0:
            continue
        results.append({
            'indicator_code': f"KOFIA_DLS_{item.get('ctgDlbDls','')}_{item.get('presCtg','')}"[:50],
            'indicator_name': f"DLS/DLB {item.get('ctgDlbDls','')} {item.get('presCtg','')}",
            'category': '파생결합증권',
            'value': amt,
            'unit': '원',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        })
    return results


def collect_els_elb() -> list:
    """⑦ ELS/ELB발행동향 (getELSAndELBInfo) - basDt 기준년월(YYYYMM)"""
    items = fetch_operation('getELSAndELBInfo', {'basDt': get_recent_yyyymm(2)})
    results = []
    for item in items:
        amt = float(item.get('amt', 0) or 0)
        if amt <= 0:
            continue
        results.append({
            'indicator_code': f"KOFIA_ELS_{item.get('ctgElbEls','')}_{item.get('presCtg','')}"[:50],
            'indicator_name': f"ELS/ELB {item.get('ctgElbEls','')} {item.get('presCtg','')}",
            'category': '파생결합증권',
            'value': amt,
            'unit': '원',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        })
    return results


def collect_foreign_derivatives() -> list:
    """⑧ 국내투자자 해외파생상품거래동향 (getDerivationProductTradingInfo) - basDt 기준년월(YYYYMM)"""
    items = fetch_operation('getDerivationProductTradingInfo', {'basDt': get_recent_yyyymm(2), 'numOfRows': 20})
    results = []
    for item in items:
        amt = float(item.get('trPrcUsd', 0) or 0)
        if amt <= 0:
            continue
        results.append({
            'indicator_code': f"KOFIA_FRNDRV_{item.get('prdNm','')[:20]}",
            'indicator_name': f"해외파생 {item.get('prdNm','')} ({item.get('byNtnl','')})",
            'category': '해외파생거래',
            'value': amt,
            'unit': 'USD',
            'signal': 'green',
            'source': '금융투자협회 (공공데이터포털)',
            'reference_date': today_kst(),
            'fetched_at': now_kst()
        })
    return results


def main():
    logger.info("=== 금융투자협회 종합통계 수집 시작 ===")
    all_results = []

    collectors = [
        ('업권별신탁규모', collect_trust_scale),
        ('펀드순자산총액', collect_fund_net_asset),
        ('일자별CMA현황', collect_cma_status),
        ('신용공여잔고추이', collect_credit_balance),
        ('증시자금추이', collect_market_capital),
        ('DLS/DLB발행동향', collect_dls_dlb),
        ('ELS/ELB발행동향', collect_els_elb),
        ('해외파생거래동향', collect_foreign_derivatives),
    ]

    for name, fn in collectors:
        try:
            results = fn()
            all_results.extend(results)
            logger.info(f"✅ {name}: {len(results)}건")
        except Exception as e:
            logger.error(f"❌ {name} 처리 오류: {type(e).__name__} - {e}")

    if all_results:
        supabase_upsert('market_indicators', all_results)

    logger.info(f"=== 금융투자협회 종합통계 수집 완료: 총 {len(all_results)}건 ===")


if __name__ == '__main__':
    main()

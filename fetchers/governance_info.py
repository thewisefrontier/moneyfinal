"""
금융회사 지배구조정보 수집기 (대표이사 정보, 임원보수현황)
출처: 공공데이터포털 금융위원회_금융회사지배구조정보 (GetFnCoGoveInfoService)
주의: 이 서비스는 대한민국 원화/원/달러 단위가 아니라 단위명이 없는 필드(xb1원단위)가 있으므로
문서의 샘플데이터 단위를 그대로 따른다 (보수 금액 샘플: 388, 30 등 → 백만원 단위로 추정되지만 문서에 명시되어 있지 않아 원시값 그대로 저장
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetFnCoGoveInfoService"


def fetch_operation(operation: str, num_rows: int = 50) -> list:
    url = f"{BASE_URL}/{operation}"
    params = {'resultType': 'json', 'numOfRows': num_rows, 'pageNo': 1}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        return items
    except Exception as e:
        logger.error(f"{operation} 수집 오류: {type(e).__name__} - {e}")
        return []


def collect_ceo_info() -> list:
    """금융회사대표이사정보조회 (getFnCoReprDireInfo)"""
    items = fetch_operation('getFnCoReprDireInfo')
    results = []
    for item in items:
        ceo = item.get('ceoFnm', '')
        if not ceo:
            continue
        results.append({
            'indicator_code': f"GOVE_CEO_{item.get('crno','')[:10]}",
            'indicator_name': f"{item.get('fncoNm','')} 대표이사",
            'category': '금융회사지배구조',
            'value': 0,
            'unit': '',
            'signal': 'green',
            'source': '금융위원회 지배구조정보 (공공데이터포털)',
            'reference_date': today_kst(),
            'summary_text': f"{ceo} ({item.get('ceoJbttNm','')}) 재직기간 {item.get('ceoHdfTermCtt','')}",
            'fetched_at': now_kst()
        })
    return results


def collect_exec_remuneration() -> list:
    """금융회사임원보수현황조회 (getFnCoExecRemuStat) - 단위 문서에 명시 없음, 원시값 그대로 저장"""
    items = fetch_operation('getFnCoExecRemuStat')
    results = []
    for item in items:
        amt = float(item.get('rgstDrtrTrmrAmt', 0) or 0)
        if amt <= 0:
            continue
        results.append({
            'indicator_code': f"GOVE_REMU_{item.get('crno','')[:10]}",
            'indicator_name': f"등기이사 총보수 ({item.get('crno','')})",
            'category': '금융회사지배구조',
            'value': amt,
            'unit': '원시값(단위문서미명시)',
            'signal': 'green',
            'source': '금융위원회 지배구조정보 (공공데이터포털)',
            'reference_date': today_kst(),
            'summary_text': f"등기이사 {item.get('rgstDrtrCnt','')}명, 사외이사 {item.get('otdrCnt','')}명",
            'fetched_at': now_kst()
        })
    return results


def main():
    logger.info("=== 금융회사 지배구조정보 수집 시작 ===")
    ceo_results = collect_ceo_info()
    remu_results = collect_exec_remuneration()

    all_results = ceo_results + remu_results
    if all_results:
        supabase_upsert('market_indicators', all_results)

    logger.info(f"✅ 대표이사정보 {len(ceo_results)}건, 임원보수현황 {len(remu_results)}건 저장")
    logger.info("=== 금융회사 지배구조정보 수집 완료 ===")


if __name__ == '__main__':
    main()

"""
기업 주요 공시 알림 수집기 (부도/영업정지/회생절차/해산사유/유상증자/무상증자)
출처: 공공데이터포털 공시정보조회서비스 (GetDiscInfoService_V2)
이 API는 조회시 반드시 basDt 또는 crno를 지정해야 한다(전체조회 시 timeout 가능성).
우선 주요 종목 일부에 대해 최근 기준일자로 조회한다.
이 API는 공공누리 라이선스 제한이 없음 (유의사항 섹션 없음, 한국예탁결제원 KSD가 아니라 금융위원회 자체 제공).
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetDiscInfoService_V2"


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_operation(operation: str, base_date: str, num_rows: int = 30) -> list:
    url = f"{BASE_URL}/{operation}"
    params = {'resultType': 'json', 'numOfRows': num_rows, 'pageNo': 1, 'basDt': base_date}
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


def collect_dishonor(base_date: str) -> list:
    """부도발생공시 (getDishDiscInfo_V2)"""
    items = fetch_operation('getDishDiscInfo_V2', base_date)
    results = []
    for item in items:
        results.append({
            'company_name': item.get('crno', ''),  # 기업명 필드가 없어 법인등록번호로 대체
            'alert_type': '부도발생',
            'detail_text': f"{item.get('dshCtt','')} ({item.get('dshOccrBnkNm','')}) {item.get('dshAmt','')}원",
            'dart_url': '',
            'disclosure_date': f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
            'source': '금융위원회 공시정보조회서비스 (공공데이터포털)',
            'is_published': True,
            'needs_review': False,
            'fetched_at': now_kst()
        })
    return results


def collect_business_suspension(base_date: str) -> list:
    """영업정지공시 (getBusiSuspDiscInfo_V2)"""
    items = fetch_operation('getBusiSuspDiscInfo_V2', base_date)
    results = []
    for item in items:
        results.append({
            'company_name': item.get('crno', ''),
            'alert_type': '영업정지',
            'detail_text': f"{item.get('bzopStopFildNm','')} - {item.get('bzopStopRsnCtt','')}",
            'dart_url': '',
            'disclosure_date': f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
            'source': '금융위원회 공시정보조회서비스 (공공데이터포털)',
            'is_published': True,
            'needs_review': False,
            'fetched_at': now_kst()
        })
    return results


def collect_rehabilitation(base_date: str) -> list:
    """회생절차개시신청공시 (getReviProcDiscInfo_V2)"""
    items = fetch_operation('getReviProcDiscInfo_V2', base_date)
    results = []
    for item in items:
        results.append({
            'company_name': item.get('corvAplpnFnm', '') or item.get('crno', ''),
            'alert_type': '회생절차개시신청',
            'detail_text': f"{item.get('corvJurdCurtNm','')} - {item.get('corvPropRsnCtt','')}",
            'dart_url': '',
            'disclosure_date': f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
            'source': '금융위원회 공시정보조회서비스 (공공데이터포털)',
            'is_published': True,
            'needs_review': False,
            'fetched_at': now_kst()
        })
    return results


def collect_dissolution(base_date: str) -> list:
    """해산사유발생공시 (getDissReasDiscInfo_V2)"""
    items = fetch_operation('getDissReasDiscInfo_V2', base_date)
    results = []
    for item in items:
        results.append({
            'company_name': item.get('crno', ''),
            'alert_type': '해산사유발생',
            'detail_text': f"{item.get('corpDsonCtt','')} ({item.get('corpDsonRsnCtt','')})",
            'dart_url': '',
            'disclosure_date': f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
            'source': '금융위원회 공시정보조회서비스 (공공데이터포털)',
            'is_published': True,
            'needs_review': False,
            'fetched_at': now_kst()
        })
    return results


def collect_capital_increase_paid(base_date: str) -> list:
    """유상증자결정공시 (getCapiIncrWithConsDiscInfo_V2)"""
    items = fetch_operation('getCapiIncrWithConsDiscInfo_V2', base_date)
    results = []
    for item in items:
        ns = item.get('onskNstCnt', '0')
        results.append({
            'company_name': item.get('crno', ''),
            'alert_type': '유상증자결정',
            'detail_text': f"보통주 신주 {ns}주, 증자방식: {item.get('capiMthoNm','')}",
            'dart_url': '',
            'disclosure_date': f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
            'source': '금융위원회 공시정보조회서비스 (공공데이터포털)',
            'is_published': True,
            'needs_review': False,
            'fetched_at': now_kst()
        })
    return results


def collect_capital_increase_free(base_date: str) -> list:
    """무상증자결정공시 (getBonuIssuDiscInfo_V2)"""
    items = fetch_operation('getBonuIssuDiscInfo_V2', base_date)
    results = []
    for item in items:
        ns = item.get('onskNstCnt', '0')
        results.append({
            'company_name': item.get('crno', ''),
            'alert_type': '무상증자결정',
            'detail_text': f"보통주 신주 {ns}주",
            'dart_url': '',
            'disclosure_date': f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
            'source': '금융위원회 공시정보조회서비스 (공공데이터포털)',
            'is_published': True,
            'needs_review': False,
            'fetched_at': now_kst()
        })
    return results


def main():
    logger.info("=== 기업 주요 공시 알림 수집 시작 ===")
    base_date = get_base_date()
    logger.info(f"기준일: {base_date}")

    collectors = [
        ('부도발생', collect_dishonor),
        ('영업정지', collect_business_suspension),
        ('회생절차개시신청', collect_rehabilitation),
        ('해산사유발생', collect_dissolution),
        ('유상증자결정', collect_capital_increase_paid),
        ('무상증자결정', collect_capital_increase_free),
    ]

    all_results = []
    for name, fn in collectors:
        try:
            results = fn(base_date)
            all_results.extend(results)
            logger.info(f"✅ {name}: {len(results)}건")
        except Exception as e:
            logger.error(f"❌ {name} 처리 오류: {type(e).__name__}")

    if all_results:
        supabase_upsert('corporate_alerts', all_results)

    logger.info(f"=== 기업 주요 공시 알림 수집 완료: 총 {len(all_results)}건 ===")


if __name__ == '__main__':
    main()

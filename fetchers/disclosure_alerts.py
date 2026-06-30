"""
기업 중요공시 알림 수집기 (부도/영업정지/회생절차/해산/유상증자/무상증자)
출처: 공공데이터포털 금융위원회_공시정보_V2 (GetDiscInfoService_V2)
주의: 각 오퍼레이션 응답에는 회사명(필드) 없이 crno(법인등록번호)만 있음.
회사명은 추측하지 않고 GetCorpBasicInfoService_V2/getCorpOutline_V2 (기업기본정보 가이드에서 검증된 API)로 crno→corpNm을 실제 조회해서 채운다.
단일 basDt(하루)만 조회 가능하며, 해당일 해당 유형 공시가 없으면 0건이 정상이다(불규칙 이벤트성 공시라 매일 발생하지 않음).
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
DISC_BASE = "https://apis.data.go.kr/1160100/service/GetDiscInfoService_V2"
CORP_BASE = "https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/getCorpOutline_V2"

_name_cache = {}


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def resolve_corp_name(crno: str) -> str:
    """crno -> 회사명 조회 (실행 내 캐시). 실패시 crno 그대로 반환(추측 금지, 회사명 없으면 식별자로만 표시)."""
    if crno in _name_cache:
        return _name_cache[crno]
    try:
        res = data_go_kr_get(CORP_BASE, API_KEY, {'resultType':'json','numOfRows':1,'pageNo':1,'crno':crno})
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        items = body.get('items',{}).get('item',[])
        item = items[0] if isinstance(items,list) and items else items
        name = item.get('corpNm','') if item else ''
        _name_cache[crno] = name if name else crno
    except Exception:
        _name_cache[crno] = crno
    return _name_cache[crno]


def fetch_disc_operation(operation: str, base_date: str, num_rows: int = 30) -> list:
    url = f"{DISC_BASE}/{operation}"
    params = {'resultType':'json','numOfRows':num_rows,'pageNo':1,'basDt':base_date}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        return items
    except Exception as e:
        logger.error(f"{operation} 수집 오류: {type(e).__name__} - {e}")
        return []


def build_alert(item: dict, alert_type: str, detail: str, disc_date_field: str = 'basDt') -> dict | None:
    crno = item.get('crno','')
    if not crno:
        return None
    name = resolve_corp_name(crno)
    base_dt = item.get(disc_date_field, item.get('basDt',''))
    return {
        'company_name': name,
        'alert_type': alert_type,
        'detail_text': detail[:1000] if detail else '',
        'dart_url': '',
        'disclosure_date': f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:8]}" if len(str(base_dt))==8 else today_kst(),
        'source': '금융위원회 공시정보 (공공데이터포털)',
        'is_published': True,
        'needs_review': False,
        'fetched_at': now_kst()
    }


def collect_default(base_date: str) -> list:
    """부도발생공시정보조회 (getDishDiscInfo_V2)"""
    items = fetch_disc_operation('getDishDiscInfo_V2', base_date)
    results = []
    for item in items:
        detail = f"부도금액 {item.get('dshAmt','')}원 / {item.get('dshCtt','')} / {item.get('dshOccrBnkNm','')}"
        alert = build_alert(item, '부도발생', detail)
        if alert: results.append(alert)
    return results


def collect_business_suspension(base_date: str) -> list:
    """영업정지공시정보조회 (getBusiSuspDiscInfo_V2)"""
    items = fetch_disc_operation('getBusiSuspDiscInfo_V2', base_date)
    results = []
    for item in items:
        detail = f"{item.get('bzopStopFildNm','')} 영업정지 / 사유: {item.get('bzopStopRsnCtt','')}"
        alert = build_alert(item, '영업정지', detail)
        if alert: results.append(alert)
    return results


def collect_rehabilitation(base_date: str) -> list:
    """회생절차개시신청공시정보조회 (getReviProcDiscInfo_V2)"""
    items = fetch_disc_operation('getReviProcDiscInfo_V2', base_date)
    results = []
    for item in items:
        detail = f"회생절차 신청 / 관할법원: {item.get('corvJurdCurtNm','')} / 사유: {item.get('corvPropRsnCtt','')}"
        alert = build_alert(item, '회생절차개시신청', detail)
        if alert: results.append(alert)
    return results


def collect_dissolution(base_date: str) -> list:
    """해산사유발생공시정보조회 (getDissReasDiscInfo_V2)"""
    items = fetch_disc_operation('getDissReasDiscInfo_V2', base_date)
    results = []
    for item in items:
        detail = f"{item.get('corpDsonCtt','')} / 사유: {item.get('corpDsonRsnCtt','')}"
        alert = build_alert(item, '해산사유발생', detail)
        if alert: results.append(alert)
    return results


def collect_capital_increase_paid(base_date: str) -> list:
    """유상증자결정공시정보조회 (getCapiIncrWithConsDiscInfo_V2)"""
    items = fetch_disc_operation('getCapiIncrWithConsDiscInfo_V2', base_date)
    results = []
    for item in items:
        detail = f"보통주신주수 {item.get('onskNstCnt','')}주 / 발행가 {item.get('onskIssuFrmPric','')}원"
        alert = build_alert(item, '유상증자결정', detail)
        if alert: results.append(alert)
    return results


def collect_capital_increase_free(base_date: str) -> list:
    """무상증자결정공시정보조회 (getBonuIssuDiscInfo_V2)"""
    items = fetch_disc_operation('getBonuIssuDiscInfo_V2', base_date)
    results = []
    for item in items:
        detail = f"보통주신주수 {item.get('onskNstCnt','')}주 무상증자"
        alert = build_alert(item, '무상증자결정', detail)
        if alert: results.append(alert)
    return results


def main():
    logger.info("=== 기업 중요공시 알림 수집 시작 ===")
    base_date = get_base_date()
    logger.info(f"기준일: {base_date}")

    collectors = [
        ('부도발생', collect_default),
        ('영업정지', collect_business_suspension),
        ('회생절차개시신청', collect_rehabilitation),
        ('해산사유발생', collect_dissolution),
        ('유상증자결정', collect_capital_increase_paid),
        ('무상증자결정', collect_capital_increase_free),
    ]

    all_alerts = []
    for name, fn in collectors:
        try:
            results = fn(base_date)
            all_alerts.extend(results)
            logger.info(f"✅ {name}: {len(results)}건 (해당일 공시 없으면 0건이 정상)")
        except Exception as e:
            logger.error(f"❌ {name} 처리 오류: {type(e).__name__} - {e}")

    if all_alerts:
        supabase_upsert('corporate_alerts', all_alerts)

    logger.info(f"=== 기업 중요공시 알림 수집 완료: 총 {len(all_alerts)}건 ===")


if __name__ == '__main__': main()

"""
금융회사 기본정보 / 재무신용정보 수집기
출처: 공공데이터포털
  - 기본정보: GetFnCoBasiInfoService/getFnCoOutl
  - 재무정보: GetFnCoFinaStatCredInfoService_V2/getFnCoSummFinaStat_V2
정확한 서비스명: 이전 코드는 GetFinancialCompanyInfoService 등으로 잘못 추측됨.
bisRto(BIS비율) 필드는 존재하지 않으며, fncoDebtRto(부채비율)가 정확한 필드임

주의 (2026-09-02 수정):
- basDt(기준일자) 없이 조회하면 응답이 날짜별 스냅샷이 전부 누적된 상태로
  나와 totalCount가 200만건대로 부풀고, page 1의 100건은 그중 임의의 옛날
  스냅샷 일부에 불과했음(basDt 지정 시 totalCount 1,103건으로 정상화 확인).
  최근 10일 범위조회로 변경.
- 재무신용(부채비율) 쪽도 totalCount 904건인데 numOfRows=50/1page만 받고
  있어서 대부분 누락되고 있었음 - 페이징 추가.
- 재무신용 응답에는 회사명이 없고 crno(사업자등록번호 아님, 법인등록번호)만
  있어 화면에 "금융회사 부채비율 (1101110002)"처럼 못 알아보는 형태로
  나가고 있었음 - 기본정보에서 수집한 crno→회사명 매핑으로 보강.
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, supabase_select_all, now_kst, today_kst, data_go_kr_get, has_recent_data

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service"
KST = pytz.timezone('Asia/Seoul')


def fetch_all_pages(url: str, base_params: dict, page_size: int = 500, max_pages: int = 10) -> list:
    all_items = []
    for page in range(1, max_pages + 1):
        params = {**base_params, 'numOfRows': page_size, 'pageNo': page}
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        total = body.get('totalCount', 0)
        if not total:
            break
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict): items = [items]
        all_items.extend(items)
        if not items or page * page_size >= total:
            break
    return all_items


def fetch_financial_corps() -> list:
    """최근 10일 범위의 최신 스냅샷만 조회 (basDt 없이 조회하면 날짜별 스냅샷이
    전부 누적된 상태로 나와 사실상 무작위 옛날 데이터를 긁게 됨)"""
    begin = (datetime.now(KST) - timedelta(days=10)).strftime('%Y%m%d')
    url = f"{BASE_URL}/GetFnCoBasiInfoService/getFnCoOutl"
    try:
        items = fetch_all_pages(url, {'resultType': 'json', 'beginBasDt': begin})
        # 같은 crno가 날짜별로 여러 번 나올 수 있어 최신 basDt만 유지
        latest = {}
        for item in items:
            crno = item.get('crno', '')
            if not crno: continue
            if crno not in latest or item.get('basDt', '') > latest[crno].get('basDt', ''):
                latest[crno] = item
        return [{
            'stock_code':    f"FIN_{crno}",
            'corp_name':     item.get('fncoNm',''),
            'industry_name': item.get('sicNm','') or item.get('sicCd',''),
            'address':       item.get('fncoAdr',''),
            'homepage':      item.get('fncoHmpgUrl',''),
            'phone':         item.get('fncoTlno',''),
            'market_type':   '금융회사',
            'fetched_at':    now_kst()
        } for crno, item in latest.items()]
    except Exception as e:
        logger.error(f"금융회사기본정보 수집 오류: {type(e).__name__}")
        return []


def fetch_financial_credit(name_by_crno: dict) -> list:
    """금융회사요약재무제표조회 - 부채비율을 건전성 지표로 사용 (BIS비율 필드는 존재하지 않음)
    name_by_crno: fetch_financial_corps() 결과로 만든 crno→회사명 매핑 (없으면 crno로 표기)"""
    url = f"{BASE_URL}/GetFnCoFinaStatCredInfoService_V2/getFnCoSummFinaStat_V2"
    try:
        items = fetch_all_pages(url, {'resultType': 'json'})
        # 같은 회사가 연결/별도 재무제표, 여러 회계연도로 중복 등장 -> 최신
        # bizYear 1건만 남긴다 (동순위면 먼저 나온 것 유지)
        latest_by_crno = {}
        for item in items:
            crno = item.get('crno', '')
            if not crno: continue
            biz_year = item.get('bizYear', '')
            if crno not in latest_by_crno or biz_year > latest_by_crno[crno].get('bizYear', ''):
                latest_by_crno[crno] = item

        results = []
        for crno, item in latest_by_crno.items():
            debt_rto = float(item.get('fncoDebtRto',0) or 0)
            if debt_rto <= 0: continue
            name = name_by_crno.get(crno, crno)
            results.append({
                'indicator_code': f"FINCRED_{crno}",
                'indicator_name': f"{name} 부채비율",
                'category': '금융회사건전성',
                'value': debt_rto,
                'unit': '%',
                'signal': 'green' if debt_rto<300 else 'yellow' if debt_rto<600 else 'red',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{item.get('bizYear','')}년 결산 기준" if item.get('bizYear') else None,
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"금융회사재무신용 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 금융회사 정보 수집 시작 ===")
    corps = []
    if has_recent_data('corp_info', {'market_type': 'eq.금융회사'}, 'fetched_at', 6):
        logger.info("금융회사기본정보 - 이미 이번 분기 수집 완료, 스킵")
    else:
        corps = fetch_financial_corps()
        if corps:
            supabase_upsert('corp_info', corps)
            logger.info(f"✅ 금융회사기본정보 {len(corps)}건 저장")
    if has_recent_data('market_indicators', {'category': 'eq.금융회사건전성'}, 'reference_date', 6):
        logger.info("금융회사재무신용 - 이미 이번 분기 수집 완료, 스킵")
    else:
        if not corps:
            # 이번 실행에서 기본정보를 새로 안 받았으면(위 스킵) DB에 있는
            # 기존 기본정보로 이름 매핑을 만든다 (없으면 crno로 표기됨)
            corps = supabase_select_all('corp_info', {'select': 'stock_code,corp_name', 'market_type': 'eq.금융회사'})
        name_by_crno = {c['stock_code'].removeprefix('FIN_'): c['corp_name'] for c in corps}
        credit = fetch_financial_credit(name_by_crno)
        if credit:
            supabase_upsert('market_indicators', credit)
            logger.info(f"✅ 금융회사재무신용 {len(credit)}건 저장")
    logger.info("=== 금융회사 정보 수집 완료 ===")

if __name__ == '__main__': main()

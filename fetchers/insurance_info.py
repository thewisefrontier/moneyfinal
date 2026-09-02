"""
실손보험정보 수집기
출처: 공공데이터포털 금융위원회_실손보험정보 (GetMedicalReimbursementInsuranceInfoService/getInsuranceInfo)
정확한 서비스명: 이전 코드는 GetRealLossInsuranceInfoService로 잘못 추측됨

주의 (2026-09-02 수정):
- age(나이) 파라미터 없이 조회하면 0~70세 전 연령이 개별 행으로 다 나와
  totalCount가 36만건대로 부풀고, numOfRows=50/1페이지만 받던 기존 코드는
  그중 임의의 18건만 잡고 있었음 -> 비교 기준으로 대표 연령 1개(40세)만 조회.
- basDt(공시 시작일)도 없이 조회하면 2021~2026년 모든 개정판이 다 섞여
  나옴 -> beginBasDt 최근 2년 범위로 좁히고 (회사,상품,mog)별 최신 basDt만 채택.
- mog(보장항목)에 기본형/노후/유병력자/특약1/특약2가 섞여 나오는데, 특약류는
  0원(미가입)인 행이 대부분이라 비교 의미가 있는 "(기본형)질병급여/상해급여"
  2개 항목만 사용 (공백 유무가 섞여 있어 정규화 후 매칭).
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get, has_recent_data

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetMedicalReimbursementInsuranceInfoService/getInsuranceInfo"
KST = pytz.timezone('Asia/Seoul')

REPRESENTATIVE_AGE = '40'
PAGE_SIZE = 500
MAX_PAGES = 20


def norm_mog(mog: str) -> str:
    return (mog or '').replace(' ', '')


def fetch_all() -> list:
    begin = (datetime.now(KST) - timedelta(days=730)).strftime('%Y%m%d')
    all_items, page = [], 1
    while page <= MAX_PAGES:
        params = {
            'resultType': 'json', 'numOfRows': PAGE_SIZE, 'pageNo': page,
            'age': REPRESENTATIVE_AGE, 'beginBasDt': begin
        }
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response', {}).get('body', {})
        total = body.get('totalCount', 0)
        if not total:
            break
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        all_items.extend(items)
        if not items or page * PAGE_SIZE >= total:
            break
        page += 1
    return all_items


def main():
    logger.info("=== 실손보험 정보 수집 시작 ===")
    if has_recent_data('rates', {'category': 'eq.실손보험'}, 'fetched_at', 6):
        logger.info("이미 이번 달 수집 완료 - 스킵 (재시도 크론 중복 방지)")
        return
    try:
        items = fetch_all()
        if not items:
            logger.warning("실손보험: 데이터 없음")
            return

        # (회사,상품,mog)별 최신 basDt 1건만 채택
        latest = {}
        for item in items:
            if norm_mog(item.get('mog')) not in ('(기본형)질병급여', '(기본형)상해급여'):
                continue
            key = (item.get('cmpyNm', ''), item.get('prdNm', ''), norm_mog(item.get('mog')))
            if key not in latest or item.get('basDt', '') > latest[key].get('basDt', ''):
                latest[key] = item

        results = []
        for (cmpy, prd, mog), item in latest.items():
            ml = float(item.get('mlInsRt', 0) or 0)
            fml = float(item.get('fmlInsRt', 0) or 0)
            avg = (ml + fml) / 2 if (ml > 0 or fml > 0) else 0
            if avg <= 0:
                continue
            results.append({
                'institution': cmpy,
                'product_name': prd,
                'category': '실손보험',
                'rate': avg,
                'max_rate': max(ml, fml),
                'period': '질병급여' if '질병' in mog else '상해급여',
                'join_method': item.get('ptrn', ''),
                'etc_note': f"{REPRESENTATIVE_AGE}세 기준 (남 {ml:,.0f}원 / 여 {fml:,.0f}원), 공시일 {item.get('basDt','')}",
                'source': '손해보험협회/생명보험협회 (공공데이터포털)',
                'source_url': 'https://data.go.kr',
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('rates', results)
            logger.info(f"✅ 실손보험 {len(results)}건 저장 (원본 {len(items)}건 중 기본형 최신판만 채택)")
    except Exception as e:
        logger.error(f"실손보험 수집 오류: {type(e).__name__}")
    logger.info("=== 실손보험 정보 수집 완료 ===")

if __name__ == '__main__': main()

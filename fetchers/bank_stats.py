"""
국내은행 통계 수집기
출처: 공공데이터포털 금융위원회_금융통계국내은행정보 (GetDomeBankInfoService)
정확한 서비스명: 이전 코드는 GetDomBankStatsInfoService로 잘못 추측됨
title 파라미터로 데이터세트를 지정해야 함 (정확한 타이틀 문자열 필요)
- 이 통계는 발표 지연이 5개월 이상이라(실측: 2026-08 기준 최신 공시가 2026-03),
  고정 3개월 전만 조회하면 항상 0건이 됨 -> 최신 기준월부터 역순으로 탐색
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get, has_recent_data

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetDomeBankInfoService"

def yyyymm_back(months_back: int) -> str:
    now = datetime.now(KST)
    target = now.replace(day=1) - timedelta(days=30*months_back)
    return target.strftime('%Y%m')

def fetch_for_month(bas_ym: str) -> list:
    """전 은행 커버를 위한 페이징 조회.
    한 달치 응답이 은행 수 × 14개 항목(cpaqItemDcd)으로 totalCount가 수백 건에
    달해 numOfRows=50 한 페이지만 받으면 은행 4곳 정도만 잡히는 문제가 있었음."""
    url = f"{BASE_URL}/getDomeBankKeyManaIndi"
    page_size = 100
    all_items, page = [], 1
    while True:
        params = {'resultType':'json','numOfRows':page_size,'pageNo':page,'title':'은행_주요경영지표_자본적정성','basYm':bas_ym}
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        tables = body.get('tableList', [])
        total = tables[0].get('totalCount', 0) if tables else 0
        if not total:
            break
        items = tables[0].get('items', {}).get('item', [])
        if isinstance(items, dict): items = [items]
        all_items.extend(items)
        if not items or page * page_size >= total:
            break
        page += 1
    return all_items

# 자본적정성 타이틀 응답에는 비율(%) 항목(A/A1/A2)과 절대금액(원) 항목(B*, C*)이
# cpaqItemClsfVal 하나에 섞여 온다. 절대금액 항목까지 그대로 넣으면 "자기자본합계
# 33,284,861,000,000%" 같은 값이 나오므로, 실제 비율 항목만 골라서 사용한다.
RATIO_CODES = {'A', 'A1', 'A2'}  # BIS기준 자기자본비율 / 기본자본비율 / 보통주자본비율


def collect_key_indicators() -> list:
    """국내은행주요경영지표조회 (getDomeBankKeyManaIndi) - 자본적정성 타이틀 지정
    분기 발표 + 지연이 길어 최신 기준월부터 최대 15개월 역순 탐색"""
    items, used_ym = [], None
    try:
        for months_back in range(0, 16):
            bas_ym = yyyymm_back(months_back)
            items = fetch_for_month(bas_ym)
            if items:
                used_ym = bas_ym
                break
        if not items:
            logger.warning("은행경영지표: 최근 15개월 내 데이터 없음")
            return []
        logger.info(f"은행경영지표: {used_ym} 기준 {len(items)}건 발견")
        results = []
        for item in items:
            if item.get('cpaqItemDcd') not in RATIO_CODES:
                continue
            val = float(item.get('cpaqItemClsfVal',0) or 0)
            if val <= 0: continue
            results.append({
                'indicator_code': f"BANK_{item.get('fncoNm','')}_{item.get('cpaqItemDcdNm','')}"[:50],
                'indicator_name': f"{item.get('fncoNm','')} {item.get('cpaqItemDcdNm','')}",
                'category': '은행통계',
                'value': val,
                'unit': '%',
                'signal': 'green' if val>=10 else 'yellow' if val>=8 else 'red',
                'source': '금융위원회 국내은행통계 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{used_ym} 기준",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"은행경영지표 수집 오류: {type(e).__name__}")
        return []

def main():
    logger.info("=== 국내은행 통계 수집 시작 ===")
    if has_recent_data('market_indicators', {'category': 'eq.은행통계'}, 'reference_date', 6):
        logger.info("이미 이번 분기 수집 완료 - 스킵 (재시도 크론 중복 방지)")
        return
    results = collect_key_indicators()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 국내은행통계 {len(results)}건 저장")
    logger.info("=== 국내은행 통계 수집 완료 ===")

if __name__ == '__main__': main()

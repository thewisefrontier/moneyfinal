"""
국내은행 통계 수집기
출처: 공공데이터포털 금융위원회_금융통계국내은행정보 (GetDomeBankInfoService)
정확한 서비스명: 이전 코드는 GetDomBankStatsInfoService로 잘못 추측됨
title 파라미터로 데이터세트를 지정해야 함 (정확한 타이틀 문자열 필요)
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

def get_recent_yyyymm(months_back: int = 3) -> str:
    now = datetime.now(KST)
    target = now.replace(day=1) - timedelta(days=30*months_back)
    return target.strftime('%Y%m')

def collect_key_indicators() -> list:
    """국내은행주요경영지표조회 (getDomeBankKeyManaIndi) - 자본적정성 타이틀 지정"""
    url = f"{BASE_URL}/getDomeBankKeyManaIndi"
    params = {'resultType':'json','numOfRows':50,'pageNo':1,'title':'은행_주요경영지표_자본적정성','basYm':get_recent_yyyymm(3)}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("은행경영지표: 데이터 없음")
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
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

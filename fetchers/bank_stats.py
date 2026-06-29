"""
국내은행 통계 수집기
- 금융위원회_국내은행통계 (공공데이터포털)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetDomBankStatsInfoService/getDomBankStatsInfo"


def fetch_bank_stats() -> list:
    params = {'resultType':'json','numOfRows':50,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("국내은행통계: 데이터 없음")
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items, dict): items = [items]
        results = []
        for item in items:
            nm = item.get('sttsItemNm','')
            results.append({
                'indicator_code': f"BANK_{nm[:20]}",
                'indicator_name': nm,
                'category':       '은행통계',
                'value':          float(item.get('sttsVal',0) or 0),
                'unit':           item.get('sttsValUnit',''),
                'signal':         'green',
                'source':         '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at':     now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"국내은행통계 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 국내은행 통계 수집 시작 ===")
    results = fetch_bank_stats()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 국내은행통계 {len(results)}건 저장")
    logger.info("=== 국내은행 통계 수집 완료 ===")

if __name__ == '__main__': main()

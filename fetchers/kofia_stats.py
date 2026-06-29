"""
금융투자협회 통계 수집기
- 금융위원회_금융투자협회통계 (공공데이터포털)
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetKofiaStatsInfoService/getKofiaStatsInfo"


def fetch_kofia_stats() -> list:
    params = {'resultType':'json','numOfRows':50,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("KOFIA 통계: 데이터 없음")
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items, dict): items = [items]
        results = []
        for item in items:
            nm = item.get('sttsItemNm','')
            results.append({
                'indicator_code': f"KOFIA_{nm[:20]}",
                'indicator_name': nm,
                'category':       '금융투자',
                'value':          float(item.get('sttsVal',0) or 0),
                'unit':           item.get('sttsValUnit',''),
                'signal':         'green',
                'source':         '금융투자협회 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at':     now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"KOFIA 통계 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== KOFIA 통계 수집 시작 ===")
    results = fetch_kofia_stats()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ KOFIA 통계 {len(results)}건 저장")
    logger.info("=== KOFIA 통계 수집 완료 ===")

if __name__ == '__main__': main()

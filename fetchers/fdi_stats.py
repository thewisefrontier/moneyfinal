"""
FDI 외국인직접투자 수집기
출처: 공공데이터포털 KOTRA
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/B553718/FdiService/getFdiList"

def main():
    logger.info("=== FDI 외국인투자 수집 시작 ===")
    params = {'resultType':'json','numOfRows':20,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("FDI: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = [{'indicator_code':f"FDI_{item.get('indutyNm','')[:20]}", 'indicator_name':f"FDI {item.get('indutyNm','')}", 'category':'외국인직접투자', 'value':float(item.get('fdiAmt',0) or 0), 'unit':'백만달러', 'signal':'green', 'source':'KOTRA (공공데이터포털)', 'reference_date':today_kst(), 'fetched_at':now_kst()} for item in items]
        if results: supabase_upsert('market_indicators', results)
        logger.info(f"✅ FDI {len(results)}건 저장")
    except Exception as e:
        logger.error(f"FDI 수집 오류: {type(e).__name__}")
    logger.info("=== FDI 외국인투자 수집 완료 ===")

if __name__ == '__main__': main()

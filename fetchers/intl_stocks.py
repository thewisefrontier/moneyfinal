"""
국제거래 종목 수집기
출처: 공공데이터포털 금융위원회
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetIntlTradingItemInfoService/getIntlTradingItemInfo"

def main():
    logger.info("=== 국제거래 종목 수집 시작 ===")
    params = {'resultType':'json','numOfRows':100,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("국제거래종목: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = [{'stock_code':item.get('isinCd',''),'stock_name':item.get('itmsNm',''),'market_type':'해외','corp_name':f"{item.get('itmsNm','')} ({item.get('natnNm','')})", 'fetched_at':now_kst()} for item in items if item.get('isinCd','')]
        if results: supabase_upsert('stocks', results)
        logger.info(f"✅ 국제거래종목 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"국제거래종목 수집 오류: {type(e).__name__}")
    logger.info("=== 국제거래 종목 수집 완료 ===")

if __name__ == '__main__': main()

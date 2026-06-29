"""
ISA 다모아 수집기
출처: 공공데이터포털 금융위원회
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetIsaProductInfoService/getIsaProductInfo"

def main():
    logger.info("=== ISA 정보 수집 시작 ===")
    params = {'resultType':'json','numOfRows':100,'pageNo':1}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("ISA 상품: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = [{'indicator_code':f"ISA_{item.get('prdtNm','').replace(' ','_')[:20]}", 'indicator_name':f"ISA {item.get('prdtNm','')}", 'category':'ISA', 'value':float(item.get('erngRt',0) or 0), 'unit':'%', 'signal':'green', 'source':'금융위원회 ISA다모아 (공공데이터포털)', 'reference_date':today_kst(), 'summary_text':f"{item.get('fncoNm','')} {item.get('prdtNm','')}", 'fetched_at':now_kst()} for item in items]
        if results: supabase_upsert('market_indicators', results)
        logger.info(f"✅ ISA 상품 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"ISA 수집 오류: {type(e).__name__}")
    logger.info("=== ISA 정보 수집 완료 ===")

if __name__ == '__main__': main()

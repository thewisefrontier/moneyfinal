"""
주식 발행 정보 수집기
출처: 공공데이터포털 금융위원회
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockIssuanceInfo"

def main():
    logger.info("=== 주식발행 정보 수집 시작 ===")
    now = datetime.now(KST)
    begin = (now-timedelta(days=90)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    params = {'resultType':'json','numOfRows':100,'pageNo':1,'beginBasDt':begin,'endBasDt':end}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("주식발행: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            base_dt = item.get('basDt','')
            results.append({'stock_code':item.get('srtnCd',''),'stock_name':item.get('itmsNm',''),'issuance_date':f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:8]}" if len(base_dt)==8 else today_kst(),'issuance_type':item.get('issuKindNm',''),'issue_price':float(item.get('issuPrc',0) or 0),'issue_amount':int(item.get('issuAmt',0) or 0),'fetched_at':now_kst()})
        if results: supabase_upsert('stock_issuance', results)
        logger.info(f"✅ 주식발행 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"주식발행 수집 오류: {type(e).__name__}")
    logger.info("=== 주식발행 정보 수집 완료 ===")

if __name__ == '__main__': main()

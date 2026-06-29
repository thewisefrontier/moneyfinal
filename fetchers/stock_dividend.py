"""
주식 배당 수집기
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
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockDividendInfoService/getStockDividendInfo"

def main():
    logger.info("=== 주식 배당정보 수집 시작 ===")
    now = datetime.now(KST)
    begin = (now-timedelta(days=365)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    params = {'resultType':'json','numOfRows':200,'pageNo':1,'beginBasDt':begin,'endBasDt':end}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("배당정보: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            dps = float(item.get('dps',0) or 0)
            if dps<=0: continue
            base_dt = item.get('basDt','')
            results.append({'stock_code':item.get('srtnCd',''),'stock_name':item.get('itmsNm',''),'base_date':f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:8]}" if len(base_dt)==8 else today_kst(),'dps':dps,'dividend_type':item.get('dvdnKindNm','현금'),'fiscal_year':int(item.get('bizYear',0) or 0),'fetched_at':now_kst()})
        if results: supabase_upsert('stock_dividends', results)
        logger.info(f"✅ 배당정보 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"배당정보 수집 오류: {type(e).__name__}")
    logger.info("=== 주식 배당정보 수집 완료 ===")

if __name__ == '__main__': main()

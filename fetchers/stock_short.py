"""
주식 대차/공매도 수집기
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
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockMarginInfo"

def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')

def main():
    logger.info("=== 주식 대차정보 수집 시작 ===")
    base_date = get_base_date()
    params = {'resultType':'json','numOfRows':100,'pageNo':1,'basDt':base_date}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning(f"대차정보 {base_date}: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = [{'stock_code':item.get('srtnCd',''), 'stock_name':item.get('itmsNm',''), 'base_date':f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}", 'short_volume':int(item.get('ststByMrktClssScrsItmsEtfYn',0) or 0), 'short_amount':int(item.get('shrtsItmsTotLoanMny',0) or 0), 'short_ratio':float(item.get('shrtsItmsShtslRt',0) or 0), 'market_type':item.get('mrktCls',''), 'fetched_at':now_kst()} for item in items]
        if results: supabase_upsert('stock_short', results)
        logger.info(f"✅ 대차정보 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"대차정보 수집 오류: {type(e).__name__}")
    logger.info("=== 주식 대차정보 수집 완료 ===")

if __name__ == '__main__': main()

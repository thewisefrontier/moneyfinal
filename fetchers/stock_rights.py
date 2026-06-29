"""
주식 권리일정 수집기
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
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockRightsInfo"

def main():
    logger.info("=== 권리일정 수집 시작 ===")
    now = datetime.now(KST)
    begin = now.strftime('%Y%m%d')
    end = (now+timedelta(days=60)).strftime('%Y%m%d')
    params = {'resultType':'json','numOfRows':100,'pageNo':1,'beginBasDt':begin,'endBasDt':end}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("권리일정: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            base_dt = item.get('basDt','')
            results.append({'company_name':item.get('itmsNm',''),'stock_code':item.get('srtnCd',''),'alert_type':f"[권리일정] {item.get('rightClsNm','')}", 'detail_text':f"{item.get('itmsNm','')} {item.get('rightClsNm','')} 권리일정",'dart_url':'','disclosure_date':f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:8]}" if len(base_dt)==8 else today_kst(),'source':'공공데이터포털','is_published':True,'needs_review':False,'fetched_at':now_kst()})
        if results: supabase_upsert('corporate_alerts', results)
        logger.info(f"✅ 권리일정 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"권리일정 수집 오류: {type(e).__name__}")
    logger.info("=== 권리일정 수집 완료 ===")

if __name__ == '__main__': main()

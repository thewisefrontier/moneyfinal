"""
채권 발행 정보 수집기
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
BASE_URL = "https://apis.data.go.kr/1160100/service/GetBondSecuritiesInfoService/getBondIssuanceInfo"

def main():
    logger.info("=== 채권발행 정보 수집 시작 ===")
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    begin = (now-timedelta(days=30)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    params = {'resultType':'json','numOfRows':50,'pageNo':1,'beginBasDt':begin,'endBasDt':end}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("채권발행: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = [{'indicator_code':f"BOND_ISS_{item.get('isinCd','')[:12]}", 'indicator_name':f"{item.get('bondIsurNm','')} {item.get('bondNm','')}", 'category':'채권발행', 'value':float(item.get('issuAmt',0) or 0), 'unit':'억원', 'signal':'green', 'source':'금융위원회 (공공데이터포털)', 'reference_date':today_kst(), 'fetched_at':now_kst()} for item in items]
        if results: supabase_upsert('market_indicators', results)
        logger.info(f"✅ 채권발행 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"채권발행 수집 오류: {type(e).__name__}")
    logger.info("=== 채권발행 정보 수집 완료 ===")

if __name__ == '__main__': main()

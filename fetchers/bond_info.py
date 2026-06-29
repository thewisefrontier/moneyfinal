"""
채권 시세 수집기
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
BASE_URL = "https://apis.data.go.kr/1160100/service/GetBondSecuritiesInfoService/getBondPriceInfo"

def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')

def main():
    logger.info("=== 채권 시세 수집 시작 ===")
    base_date = get_base_date()
    params = {'resultType':'json','numOfRows':50,'pageNo':1,'basDt':base_date}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning(f"채권시세 {base_date}: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        results = []
        for item in items:
            ytm = float(item.get('mktYtm',0) or 0)
            results.append({'indicator_code':f"BOND_{item.get('isinCd','')[:10]}", 'indicator_name':item.get('bondIsurNm','')+' '+item.get('bondNm',''), 'category':'채권금리', 'value':ytm, 'unit':'%', 'signal':'green' if ytm<4 else 'yellow' if ytm<5 else 'red', 'source':'금융위원회 (공공데이터포털)', 'reference_date':today_kst(), 'fetched_at':now_kst()})
        if results: supabase_upsert('market_indicators', results)
        logger.info(f"✅ 채권시세 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"채권시세 수집 오류: {type(e).__name__}")
    logger.info("=== 채권 시세 수집 완료 ===")

if __name__ == '__main__': main()

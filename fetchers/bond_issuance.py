"""
채권 발행 정보 수집기
- 금융위원회_채권발행정보 (공공데이터포털)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetBondSecuritiesInfoService/getBondIssuanceInfo"


def fetch_bond_issuance() -> list:
    now = datetime.now(KST)
    begin = (now - timedelta(days=30)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    params = {'resultType':'json','numOfRows':50,'pageNo':1,'beginBasDt':begin,'endBasDt':end}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        data = res.json()
        body = data.get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning("채권발행: 데이터 없음")
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items, dict): items = [items]
        results = []
        for item in items:
            results.append({
                'indicator_code': f"BOND_ISS_{item.get('isinCd','')[:12]}",
                'indicator_name': f"{item.get('bondIsurNm','')} {item.get('bondNm','')}",
                'category':       '채권발행',
                'value':          float(item.get('issuAmt',0) or 0),
                'unit':           '억원',
                'signal':         'green',
                'source':         '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'fetched_at':     now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"채권발행 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 채권발행 정보 수집 시작 ===")
    results = fetch_bond_issuance()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 채권발행 {len(results)}건 저장")
    logger.info("=== 채권발행 정보 수집 완료 ===")

if __name__ == '__main__': main()

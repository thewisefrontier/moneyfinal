"""
채권 시세 수집기
출처: 공공데이터포털 금융위원회_채권시세정보 (GetBondSecuritiesInfoService/getBondPriceInfo)
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 종목별 최신 basDt 값만 채택 (krx_index.py와 동일 패턴,
  실측 확인: category='채권금리' 데이터가 한 번도 DB에 저장된 적 없었음)
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

def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')

def main():
    logger.info("=== 채권 시세 수집 시작 ===")
    begin_date = get_recent_date(10)
    params = {'resultType':'json','numOfRows':500,'pageNo':1,'beginBasDt':begin_date}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning(f"채권시세 {begin_date}~: 데이터 없음")
            return
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        # 종목(isinCd)별로 basDt가 가장 최신인 항목만 채택
        latest_by_code = {}
        for item in items:
            code = item.get('isinCd','')
            cur = latest_by_code.get(code)
            if cur is None or item.get('basDt','') > cur.get('basDt',''):
                latest_by_code[code] = item
        results = []
        for item in latest_by_code.values():
            # 수정: clprBnfRt(종가_수익률)가 정확한 필드명. mktYtm은 존재하지 않음
            ytm = float(item.get('clprBnfRt',0) or 0)
            results.append({
                'indicator_code': f"BOND_{item.get('isinCd','')[:10]}",
                'indicator_name': item.get('itmsNm',''),
                'category': '채권금리',
                'value': ytm,
                'unit': '%',
                'signal': 'green' if ytm<4 else 'yellow' if ytm<5 else 'red',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{item.get('mrktCtg','')} 종가 {item.get('clprPrc','')}",
                'fetched_at': now_kst()
            })
        if results:
            supabase_upsert('market_indicators', results)
            logger.info(f"✅ 채권시세 {len(results)}건 저장")
    except Exception as e:
        logger.error(f"채권시세 수집 오류: {type(e).__name__}")
    logger.info("=== 채권 시세 수집 완료 ===")

if __name__ == '__main__': main()

"""
파생상품 지수 수집기
출처: 공공데이터포털 금융위원회_파생상품시세정보 (GetDerivativeProductInfoService)
정확한 서비스명: 이전 코드는 GetMarketIndexInfoService/getDerivationProductMarketIndex로 완전히 잘못된 서비스명을 사용했음
2개 오퍼레이션: 선물시세(getStockFuturesPriceInfo), 옵션시세(getOptionsPriceInfo)
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 최신 basDt 값만 채택 (krx_index.py와 동일 패턴)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetDerivativeProductInfoService"

def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')

def collect_futures(begin_date: str) -> list:
    url = f"{BASE_URL}/getStockFuturesPriceInfo"
    params = {'resultType':'json','numOfRows':100,'pageNo':1,'beginBasDt':begin_date}
    try:
        res = data_go_kr_get(url, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning(f"선물시세 {begin_date}~: 데이터 없음")
            return []
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        # 종목(srtnCd)별로 basDt가 가장 최신인 항목만 채택
        latest_by_code = {}
        for item in items:
            code = item.get('srtnCd','')
            cur = latest_by_code.get(code)
            if cur is None or item.get('basDt','') > cur.get('basDt',''):
                latest_by_code[code] = item
        results = []
        for item in latest_by_code.values():
            clpr = float(item.get('clpr',0) or 0)
            vs = float(item.get('vs',0) or 0)
            if clpr <= 0: continue
            results.append({
                'indicator_code': f"DERIV_FUT_{item.get('srtnCd','')}",
                'indicator_name': item.get('itmsNm',''),
                'category': '파생상품',
                'value': clpr,
                'unit': 'pt',
                'signal': 'red' if vs<0 else 'green',
                'source': '금융위원회 (공공데이터포털)',
                'reference_date': today_kst(),
                'summary_text': f"{item.get('prdCtg','')} {clpr:.2f}pt",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"선물시세 수집 오류: {type(e).__name__}")
        return []

def main():
    logger.info("=== 파생상품 시세 수집 시작 ===")
    begin_date = get_recent_date(10)
    results = collect_futures(begin_date)
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 파생상품(선물) {len(results)}건 저장")
    logger.info("=== 파생상품 시세 수집 완료 ===")

if __name__ == '__main__': main()

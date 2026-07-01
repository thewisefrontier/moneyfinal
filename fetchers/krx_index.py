"""
KRX 주식 지수 수집기
출처: 공공데이터포털 금융위원회_지수시세정보
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 최신 basDt 값만 채택 (실측 확인된 이슈)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"

INDICES = [
    {'idxNm': '코스피',     'indicator_code': 'KOSPI',    'indicator_name': '코스피 지수'},
    {'idxNm': '코스닥',     'indicator_code': 'KOSDAQ',   'indicator_name': '코스닥 지수'},
    {'idxNm': '코스피 200', 'indicator_code': 'KOSPI200', 'indicator_name': '코스피 200'},
]

def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')

def fetch_index(index: dict, begin_date: str) -> dict | None:
    params = {'resultType':'json','numOfRows':30,'pageNo':1,'beginBasDt':begin_date,'idxNm':index['idxNm']}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            logger.warning(f"{index['idxNm']}: 데이터 없음")
            return None
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        # basDt가 가장 최신인 항목 채택
        item = max(items, key=lambda x: x.get('basDt',''))
        value = float(item.get('clpr',0) or 0)
        vs = float(item.get('vs',0) or 0)
        flt_rt = float(item.get('fltRt',0) or 0)
        return {
            'indicator_code': index['indicator_code'],
            'indicator_name': index['indicator_name'],
            'category': '주식지수',
            'value': value,
            'prev_value': round(value-vs,2),
            'unit': 'pt',
            'signal': 'red' if flt_rt<=-3 else 'yellow' if flt_rt<=-1 else 'green',
            'source': '금융위원회 (공공데이터포털)',
            'reference_date': today_kst(),
            'summary_text': f"{index['idxNm']} {value:.2f}pt ({flt_rt:+.2f}%)",
            'fetched_at': now_kst()
        }
    except Exception as e:
        logger.error(f"{index['idxNm']} 오류: {e}")
        return None

def main():
    logger.info("=== KRX 지수 수집 시작 ===")
    begin_date = get_recent_date(10)
    logger.info(f"조회 시작일: {begin_date}")
    results = [r for idx in INDICES if (r:=fetch_index(idx,begin_date))]
    if results: supabase_upsert('market_indicators', results)
    logger.info(f"=== KRX 수집 완료: {len(results)}/{len(INDICES)}건 ===")

if __name__ == '__main__': main()

"""
KRX 주식 지수 수집기
1차 출처: 공공데이터포털 금융위원회_지수시세정보
2차(폴백) 출처: Yahoo Finance (^KS11/^KQ11/^KS200) - 1차 API가 장애/차단되어
데이터를 못 가져온 경우에만 사용. [[moneyfinal_krx_backup_pipeline_research]] 조사 결과에 따른 백업.
- basDt는 정확일치 파라미터라 그날 데이터가 아직 게시 안 됐으면 0건이 됨
  -> beginBasDt 범위 조회 후 최신 basDt 값만 채택 (실측 확인된 이슈)
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get
import yfinance as yf

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"

INDICES = [
    {'idxNm': '코스피',     'indicator_code': 'KOSPI',    'indicator_name': '코스피 지수', 'yf_symbol': '^KS11'},
    {'idxNm': '코스닥',     'indicator_code': 'KOSDAQ',   'indicator_name': '코스닥 지수', 'yf_symbol': '^KQ11'},
    {'idxNm': '코스피 200', 'indicator_code': 'KOSPI200', 'indicator_name': '코스피 200', 'yf_symbol': '^KS200'},
]

def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')

def build_result(index: dict, value: float, flt_rt: float, source: str) -> dict:
    return {
        'indicator_code': index['indicator_code'],
        'indicator_name': index['indicator_name'],
        'category': '주식지수',
        'value': value,
        'prev_value': round(value / (1 + flt_rt / 100), 2) if flt_rt else value,
        'unit': 'pt',
        'signal': 'red' if flt_rt<=-3 else 'yellow' if flt_rt<=-1 else 'green',
        'source': source,
        'reference_date': today_kst(),
        'summary_text': f"{index['idxNm']} {value:.2f}pt ({flt_rt:+.2f}%)",
        'fetched_at': now_kst()
    }

def fetch_index_primary(index: dict, begin_date: str) -> dict | None:
    params = {'resultType':'json','numOfRows':30,'pageNo':1,'beginBasDt':begin_date,'idxNm':index['idxNm']}
    try:
        res = data_go_kr_get(BASE_URL, API_KEY, params)
        res.raise_for_status()
        body = res.json().get('response',{}).get('body',{})
        if not body.get('totalCount',0):
            return None
        items = body.get('items',{}).get('item',[])
        if isinstance(items,dict): items=[items]
        item = max(items, key=lambda x: x.get('basDt',''))
        value = float(item.get('clpr',0) or 0)
        flt_rt = float(item.get('fltRt',0) or 0)
        return build_result(index, value, flt_rt, '금융위원회 (공공데이터포털)')
    except Exception as e:
        logger.warning(f"{index['idxNm']} 1차(data.go.kr) 실패: {type(e).__name__}")
        return None

def fetch_index_fallback(index: dict) -> dict | None:
    try:
        hist = yf.Ticker(index['yf_symbol']).history(period='5d')
        if hist.empty or len(hist) < 1:
            return None
        closes = hist['Close']
        value = float(closes.iloc[-1])
        prev = float(closes.iloc[-2]) if len(closes) >= 2 else value
        flt_rt = (value - prev) / prev * 100 if prev else 0
        return build_result(index, round(value, 2), round(flt_rt, 2), 'Yahoo Finance (data.go.kr 장애 시 폴백)')
    except Exception as e:
        logger.error(f"{index['idxNm']} 2차(Yahoo) 실패: {type(e).__name__}")
        return None

def fetch_index(index: dict, begin_date: str) -> dict | None:
    result = fetch_index_primary(index, begin_date)
    if result:
        return result
    logger.warning(f"{index['idxNm']}: 1차 실패 -> Yahoo Finance 폴백 시도")
    result = fetch_index_fallback(index)
    if result:
        logger.info(f"✅ {index['idxNm']}: 폴백으로 수집 성공")
    else:
        logger.error(f"❌ {index['idxNm']}: 1차/2차 모두 실패")
    return result

def main():
    logger.info("=== KRX 지수 수집 시작 ===")
    begin_date = get_recent_date(10)
    logger.info(f"조회 시작일: {begin_date}")
    results = [r for idx in INDICES if (r:=fetch_index(idx,begin_date))]
    if results: supabase_upsert('market_indicators', results)
    logger.info(f"=== KRX 수집 완료: {len(results)}/{len(INDICES)}건 ===")

if __name__ == '__main__': main()

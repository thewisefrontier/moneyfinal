"""
주식 시세 및 상장종목 수집기
출처: 공공데이터포털 금융위원회 (오픈API_활용자가이드_금융위원회_주식시세정보 검증 완료)
- 일반 실행: 직전 거래일 1일치 전 종목 수집 (basDt)
- 백필 실행: python fetchers/stock_prices.py backfill [일수]
  → beginBasDt/endBasDt 범위 조회 (가이드 공식 지원 파라미터), 기본 35일
"""
import logging, os, sys
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service"
PAGE_SIZE = 5000  # numOfRows 항목크기 4자리(최대 9999)


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_price_pages(market: str, date_params: dict) -> list:
    """getStockPriceInfo 페이징 조회 (전 종목 커버)"""
    url = f"{BASE_URL}/GetStockSecuritiesInfoService/getStockPriceInfo"
    all_items, page = [], 1
    while True:
        params = {'resultType': 'json', 'numOfRows': PAGE_SIZE, 'pageNo': page,
                  'mrktCls': market, **date_params}
        try:
            res = data_go_kr_get(url, API_KEY, params, timeout=30)
            res.raise_for_status()
            body = res.json().get('response', {}).get('body', {})
            total = int(body.get('totalCount', 0) or 0)
            items = body.get('items', {}).get('item', [])
            if isinstance(items, dict): items = [items]
            all_items.extend(items)
            if not items or page * PAGE_SIZE >= total:
                break
            page += 1
        except Exception as e:
            logger.error(f"{market} 시세 수집 오류 (page {page}): {type(e).__name__}")
            break
    return all_items


def process_stock_prices(items: list, market: str) -> list:
    """basDt는 응답 항목에서 직접 읽음 (백필 시 다중 날짜 대응)"""
    results = []
    for item in items:
        try:
            bd = str(item.get('basDt', ''))
            if len(bd) != 8: continue
            results.append({
                'stock_code':   item.get('srtnCd', ''),
                'stock_name':   item.get('itmsNm', ''),
                'base_date':    f"{bd[:4]}-{bd[4:6]}-{bd[6:8]}",
                'close_price':  float(item.get('clpr', 0) or 0),
                'open_price':   float(item.get('mkp', 0) or 0),
                'high_price':   float(item.get('hipr', 0) or 0),
                'low_price':    float(item.get('lopr', 0) or 0),
                'vs':           float(item.get('vs', 0) or 0),
                'flt_rt':       float(item.get('fltRt', 0) or 0),
                'volume':       int(item.get('trqu', 0) or 0),
                'trade_amount': int(item.get('trPrc', 0) or 0),
                'market_cap':   int(item.get('mrktTotAmt', 0) or 0),
                'shares_out':   int(item.get('lstgStCnt', 0) or 0),
                'market_type':  market,
                'fetched_at':   now_kst()
            })
        except Exception as e:
            logger.error(f"종목 처리 오류: {e}")
    return results


def dedupe(rows: list) -> list:
    """배치 내 conflict key 중복 제거 (ON CONFLICT 오류 예방)"""
    seen = {}
    for r in rows:
        seen[(r['stock_code'], r['base_date'], r['market_type'])] = r
    return list(seen.values())


def upsert_batched(rows: list, batch: int = 1000):
    for i in range(0, len(rows), batch):
        supabase_upsert('stock_prices', rows[i:i + batch])


def fetch_krx_stocks() -> list:
    url = f"{BASE_URL}/GetKrxListedInfoService/getItemInfo"
    results = []
    for market in ['KOSPI', 'KOSDAQ']:
        params = {'resultType': 'json', 'numOfRows': 2000, 'pageNo': 1, 'mrktCtg': market}
        try:
            res = data_go_kr_get(url, API_KEY, params, timeout=20)
            res.raise_for_status()
            body = res.json().get('response', {}).get('body', {})
            items = body.get('items', {}).get('item', [])
            if isinstance(items, dict): items = [items]
            for item in items:
                sc = item.get('srtnCd', '')
                if not sc: continue
                results.append({'isin_code': item.get('isinCd', ''), 'stock_code': sc, 'stock_name': item.get('itmsNm', ''), 'market_type': market, 'corp_name': item.get('corpNm', item.get('itmsNm', '')), 'listed_date': item.get('lstgDt', None), 'fetched_at': now_kst()})
            logger.info(f"{market} 상장종목 {len(items)}건")
        except Exception as e:
            logger.error(f"{market} 종목 수집 오류: {type(e).__name__}")
    # stocks 테이블 conflict 컬럼(stock_code) 기준 중복 제거
    # (KOSPI/KOSDAQ 응답 사이 이전상장 종목 등 겹칠 때 ON CONFLICT 배치 오류 예방)
    seen = {}
    for r in results:
        seen[r['stock_code']] = r
    return list(seen.values())


def run_daily():
    base_date = get_base_date()
    logger.info(f"기준일: {base_date}")
    all_prices = []
    for market in ['KOSPI', 'KOSDAQ']:
        items = fetch_price_pages(market, {'basDt': base_date})
        if items:
            all_prices.extend(process_stock_prices(items, market))
            logger.info(f"✅ {market}: {len(items)}건")
        else:
            logger.warning(f"❌ {market}: 데이터 없음")
    if all_prices:
        upsert_batched(dedupe(all_prices))
    stocks = fetch_krx_stocks()
    if stocks:
        supabase_upsert('stocks', stocks)
        logger.info(f"✅ 상장종목 {len(stocks)}건")


def run_backfill(days: int = 35):
    """RSI 계산용 과거 시세 백필. endBasDt는 '검색값보다 작은' 조건이므로 내일 날짜 사용"""
    now = datetime.now(KST)
    begin = (now - timedelta(days=days)).strftime('%Y%m%d')
    end = (now + timedelta(days=1)).strftime('%Y%m%d')
    logger.info(f"백필 범위: {begin} ~ {end} (미만)")
    for market in ['KOSPI', 'KOSDAQ']:
        items = fetch_price_pages(market, {'beginBasDt': begin, 'endBasDt': end})
        if not items:
            logger.warning(f"❌ {market}: 백필 데이터 없음")
            continue
        rows = dedupe(process_stock_prices(items, market))
        upsert_batched(rows)
        logger.info(f"✅ {market} 백필: {len(rows)}건")


def main():
    logger.info("=== 주식 시세 수집 시작 ===")
    if len(sys.argv) > 1 and sys.argv[1] == 'backfill':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 35
        run_backfill(days)
    else:
        run_daily()
    logger.info("=== 주식 시세 수집 완료 ===")


if __name__ == '__main__': main()

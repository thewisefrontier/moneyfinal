"""
주식 시세 및 상장종목 수집기
1차 출처: 공공데이터포털 금융위원회 (오픈API_활용자가이드_금융위원회_주식시세정보 검증 완료)
- 일반 실행: beginBasDt 범위조회(최근 10일)로 전 종목 수집
  (basDt 정확일치는 발행 시차로 대부분 0건 - 실측 확인: 5주 이상 전체 무갱신 상태였음)
- 백필 실행: python fetchers/stock_prices.py backfill [일수]
  → beginBasDt/endBasDt 범위 조회 (가이드 공식 지원 파라미터), 기본 35일
- 실측: GitHub Actions 러너 -> data.go.kr 구간에서 ConnectTimeout이 간헐적으로
  발생(로컬에서는 같은 요청이 1초 내 응답 - 페이로드 크기가 아니라 네트워크
  경로 문제). 타임아웃을 늘리는 대신 페이지당 짧은 타임아웃 + 재시도로 대응.

2차(폴백) 출처: Yahoo Finance (.KS/.KQ 티커) - 1차 API가 장애/차단된 경우에만 사용.
[[moneyfinal_krx_backup_pipeline_research]] 조사 결과에 따른 백업. Yahoo는 "전종목
스캔"이 안 되므로, 직전 성공한 stock_prices 스냅샷에서 시가총액 상위 종목 코드를
가져와 그 종목들만 개별 조회한다(시가총액 자체는 그 스냅샷 값을 그대로 이월 - 장애
당일에는 갱신 안 됨, 종가/등락률/거래량만 최신화).
"""
import logging, os, sys, time
from datetime import datetime, timedelta
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, supabase_select, now_kst, data_go_kr_get
import yfinance as yf

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service"
PAGE_SIZE = 5000  # numOfRows 항목크기 4자리(최대 9999)
MAX_RETRIES = 3
RETRY_TIMEOUT = 20


def get_recent_date(days_back: int = 10) -> str:
    now = datetime.now(KST)
    return (now - timedelta(days=days_back)).strftime('%Y%m%d')


def fetch_page_with_retry(url: str, params: dict, market: str, page: int):
    """ConnectTimeout은 페이로드 크기가 아니라 네트워크 경로 문제라 매 시도마다
    새 커넥션을 짧은 타임아웃으로 재시도하는 편이 긴 타임아웃 1회보다 안정적."""
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = data_go_kr_get(url, API_KEY, params, timeout=RETRY_TIMEOUT)
            res.raise_for_status()
            return res
        except Exception as e:
            last_err = e
            logger.warning(f"{market} page {page} 시도 {attempt}/{MAX_RETRIES} 실패: {type(e).__name__}")
            if attempt < MAX_RETRIES:
                time.sleep(3)
    logger.error(f"{market} 시세 수집 오류 (page {page}): {type(last_err).__name__} - {MAX_RETRIES}회 재시도 모두 실패")
    return None


def fetch_price_pages(market: str, date_params: dict) -> list:
    """getStockPriceInfo 페이징 조회 (전 종목 커버)"""
    url = f"{BASE_URL}/GetStockSecuritiesInfoService/getStockPriceInfo"
    all_items, page = [], 1
    while True:
        params = {'resultType': 'json', 'numOfRows': PAGE_SIZE, 'pageNo': page,
                  'mrktCls': market, **date_params}
        res = fetch_page_with_retry(url, params, market, page)
        if res is None:
            break
        body = res.json().get('response', {}).get('body', {})
        total = int(body.get('totalCount', 0) or 0)
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict): items = [items]
        all_items.extend(items)
        if not items or page * PAGE_SIZE >= total:
            break
        page += 1
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


def fetch_market_fallback(market: str, top_n: int = 100) -> list:
    """1차 API 실패 시 직전 성공 스냅샷의 상위 top_n 종목만 Yahoo Finance로 갱신."""
    ref_rows = supabase_select('stock_prices', {
        'select': 'stock_code,stock_name,market_cap,shares_out',
        'market_type': f'eq.{market}',
        'order': 'base_date.desc,market_cap.desc',
        'limit': str(top_n * 3)  # 종목당 여러 날짜 섞여 나올 수 있어 여유있게 조회 후 dedupe
    })
    seen, refs = set(), []
    for r in ref_rows:
        code = r.get('stock_code')
        if not code or code in seen:
            continue
        seen.add(code)
        refs.append(r)
        if len(refs) >= top_n:
            break
    if not refs:
        logger.warning(f"{market} 폴백: 참조할 직전 스냅샷 없음 (최초 실행이거나 데이터 없음)")
        return []

    suffix = '.KS' if market == 'KOSPI' else '.KQ'
    results = []
    for r in refs:
        code = r['stock_code']
        try:
            hist = yf.Ticker(f"{code}{suffix}").history(period='5d')
            # 당일 장중이면 마지막 행의 종가가 아직 NaN인 채로 올 수 있어(거래량만
            # 부분 채워짐) - 종가가 확정된 가장 최근 행만 쓴다 (실측으로 발견,
            # 2026-09-03: NaN * volume을 int()하다 ValueError로 전종목 폴백 실패했음).
            hist = hist.dropna(subset=['Close'])
            if hist.empty:
                continue
            close = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else close
            vs = round(close - prev, 2)
            flt_rt = round(vs / prev * 100, 2) if prev else 0
            base_date = hist.index[-1].strftime('%Y-%m-%d')
            results.append({
                'stock_code': code,
                'stock_name': r.get('stock_name', ''),
                'base_date': base_date,
                'close_price': close,
                'open_price': float(hist['Open'].iloc[-1]),
                'high_price': float(hist['High'].iloc[-1]),
                'low_price': float(hist['Low'].iloc[-1]),
                'vs': vs,
                'flt_rt': flt_rt,
                'volume': int(hist['Volume'].iloc[-1]),
                'trade_amount': int(hist['Volume'].iloc[-1] * close),
                'market_cap': r.get('market_cap') or 0,
                'shares_out': r.get('shares_out') or 0,
                'market_type': market,
                'fetched_at': now_kst()
            })
        except Exception as e:
            logger.warning(f"{market} 폴백 {code} 실패: {type(e).__name__}")
    return results


def run_daily():
    """최근 10일 범위조회 - 정확일치(basDt)는 발행 시차로 대부분 0건이 되므로
    범위조회로 그날그날 게시된 만큼 가져오고 upsert로 자연 dedupe (기존일 재작성은 무해)."""
    begin_date = get_recent_date(10)
    logger.info(f"조회 시작일: {begin_date}")
    all_prices = []
    for market in ['KOSPI', 'KOSDAQ']:
        items = fetch_price_pages(market, {'beginBasDt': begin_date})
        if items:
            all_prices.extend(process_stock_prices(items, market))
            logger.info(f"✅ {market}: {len(items)}건")
        else:
            logger.warning(f"❌ {market}: 1차 데이터 없음 -> Yahoo Finance 폴백 시도")
            fallback_rows = fetch_market_fallback(market)
            if fallback_rows:
                all_prices.extend(fallback_rows)
                logger.info(f"✅ {market} 폴백: {len(fallback_rows)}건 (Yahoo Finance)")
            else:
                logger.error(f"❌ {market}: 1차/2차 모두 실패")
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

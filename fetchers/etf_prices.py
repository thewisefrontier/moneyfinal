"""
배당ETF 계산기용 실시간 시세 수집기 (Finnhub /quote)
출처: finnhub.io - us_stocks.py와 동일 엔드포인트/키, 무료티어 분당 60회.
config/etf_dividend_tickers.py의 67개 티커는 하루 1회 전체 조회해도 한도에
여유가 있어 배당 이력(etf_dividends.py)처럼 로테이션할 필요가 없다.
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst
from config.etf_dividend_tickers import SYMBOLS
import requests

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FINNHUB_API_KEY', '')
BASE_URL = "https://finnhub.io/api/v1"


def fetch_quote(symbol: str) -> dict | None:
    try:
        res = requests.get(f"{BASE_URL}/quote", params={'symbol': symbol, 'token': API_KEY}, timeout=10)
        if res.status_code >= 400:
            logger.error(f"{symbol} quote 오류 HTTP {res.status_code}: {res.text[:200]}")
            return None
        data = res.json()
        if not data or data.get('c') in (None, 0):
            return None
        return data
    except Exception as e:
        logger.error(f"{symbol} quote 예외: {type(e).__name__}")
        return None


def main():
    logger.info("=== 배당ETF 실시간 시세 수집 시작 (Finnhub) ===")
    results = []
    for symbol in SYMBOLS:
        quote = fetch_quote(symbol)
        if not quote:
            logger.warning(f"❌ {symbol}: 시세 없음")
            time.sleep(1)
            continue
        close = float(quote.get('c', 0) or 0)
        results.append({
            'stock_code':   symbol,
            'stock_name':   symbol,
            'base_date':    today_kst(),
            'close_price':  close,
            'open_price':   float(quote.get('o', 0) or 0),
            'high_price':   float(quote.get('h', 0) or 0),
            'low_price':    float(quote.get('l', 0) or 0),
            'vs':           float(quote.get('d', 0) or 0),
            'flt_rt':       float(quote.get('dp', 0) or 0),
            'volume':       0,
            'trade_amount': 0,
            'market_cap':   0,
            'shares_out':   0,
            'market_type':  'ETF',
            'fetched_at':   now_kst()
        })
        logger.info(f"✅ {symbol} ${close}")
        time.sleep(1)  # 분당 60회 한도 안전 마진

    if results:
        supabase_upsert('stock_prices', results)
        logger.info(f"✅ 배당ETF 시세 {len(results)}건 저장")
    logger.info("=== 배당ETF 실시간 시세 수집 완료 ===")


if __name__ == '__main__':
    main()

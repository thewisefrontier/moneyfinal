"""
미국 주식 시세 수집기 (Finnhub)
출처: finnhub.io - /quote, /stock/profile2 (공식 필드, 다수 공식예제 교차확인됨)
무료티어: 분당 60회
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst
import requests

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FINNHUB_API_KEY', '')
BASE_URL = "https://finnhub.io/api/v1"

US_TICKERS = [
    ('AAPL','Apple'),('MSFT','Microsoft'),('GOOGL','Alphabet'),('AMZN','Amazon'),
    ('NVDA','NVIDIA'),('META','Meta'),('TSLA','Tesla'),('AVGO','Broadcom'),
    ('JPM','JPMorgan'),('V','Visa'),
]


def fetch_quote(symbol: str) -> dict | None:
    try:
        res = requests.get(f"{BASE_URL}/quote", params={'symbol':symbol,'token':API_KEY}, timeout=10)
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


def fetch_profile(symbol: str) -> dict:
    try:
        res = requests.get(f"{BASE_URL}/stock/profile2", params={'symbol':symbol,'token':API_KEY}, timeout=10)
        if res.status_code >= 400:
            return {}
        return res.json() or {}
    except Exception:
        return {}


def main():
    logger.info("=== 미국 주식 시세 수집 시작 (Finnhub) ===")
    results = []
    for symbol, name_fallback in US_TICKERS:
        quote = fetch_quote(symbol)
        if not quote:
            logger.warning(f"❌ {symbol}: 시세 없음")
            time.sleep(1)
            continue
        profile = fetch_profile(symbol)
        time.sleep(1)  # 분당 60회 한도 안전 마진

        close = float(quote.get('c',0) or 0)
        change = float(quote.get('d',0) or 0)
        change_pct = float(quote.get('dp',0) or 0)

        results.append({
            'stock_code':   symbol,
            'stock_name':   profile.get('name', name_fallback),
            'base_date':    today_kst(),
            'close_price':  close,
            'open_price':   float(quote.get('o',0) or 0),
            'high_price':   float(quote.get('h',0) or 0),
            'low_price':    float(quote.get('l',0) or 0),
            'vs':           change,
            'flt_rt':       change_pct,
            'volume':       0,
            'trade_amount': 0,
            'market_cap':   int(float(profile.get('marketCapitalization',0) or 0) * 1_000_000),  # 백만달러 → 달러
            'shares_out':   0,
            'market_type':  'US',
            'fetched_at':   now_kst()
        })
        logger.info(f"✅ {symbol} ${close} ({change_pct:+.2f}%)")

    if results:
        supabase_upsert('stock_prices', results)
        logger.info(f"✅ 미국주식 {len(results)}건 저장")
    logger.info("=== 미국 주식 시세 수집 완료 ===")


if __name__ == '__main__': main()

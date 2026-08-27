"""
ETF 프로필 정보 수집기 (Alpha Vantage ETF_PROFILE)
출처: alphavantage.co - net_assets(운용규모), net_expense_ratio(보수율),
dividend_yield, inception_date, sectors(섹터비중), holdings(상위 구성종목).

us_technical.py(RSI, 하루 5회)와 같은 키(ALPHA_VANTAGE_API_KEY)를 쓰되,
운용사 프로필은 분기 단위로만 바뀌는 정보라 매일 전체를 돌 필요가 없다.
남는 하루 여유분(~20회) 안에서 로테이션으로 순회한다.
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from utils.common import supabase_upsert, now_kst, KST
from config.etf_dividend_tickers import SYMBOLS
import requests

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
BASE_URL = "https://www.alphavantage.co/query"

BATCH_SIZE = 18
TOP_HOLDINGS = 10


def get_today_batch() -> list:
    num_batches = -(-len(SYMBOLS) // BATCH_SIZE)
    day_index = datetime.now(KST).timetuple().tm_yday % num_batches
    start = day_index * BATCH_SIZE
    return SYMBOLS[start:start + BATCH_SIZE]


def fetch_profile(symbol: str) -> dict | None:
    params = {'function': 'ETF_PROFILE', 'symbol': symbol, 'apikey': API_KEY}
    try:
        res = requests.get(BASE_URL, params=params, timeout=15)
        if res.status_code >= 400:
            logger.error(f"{symbol} 프로필 오류 HTTP {res.status_code}")
            return None
        data = res.json()
        if 'Note' in data or 'Information' in data or not data.get('net_assets'):
            logger.warning(f"{symbol}: 호출한도 도달 또는 데이터 없음 - {data.get('Note') or data.get('Information') or '빈 응답'}")
            return None
        return data
    except Exception as e:
        logger.error(f"{symbol} 프로필 예외: {type(e).__name__}")
        return None


def main():
    logger.info("=== ETF 프로필 수집 시작 (Alpha Vantage) ===")
    batch = get_today_batch()
    logger.info(f"오늘 처리 대상 {len(batch)}개: {batch}")

    results = []
    for symbol in batch:
        p = fetch_profile(symbol)
        if not p:
            logger.warning(f"❌ {symbol}: 프로필 없음")
            time.sleep(12)
            continue
        sectors = sorted(p.get('sectors', []), key=lambda s: float(s.get('weight', 0) or 0), reverse=True)
        holdings = p.get('holdings', [])[:TOP_HOLDINGS]
        results.append({
            'ticker': symbol,
            'net_assets': float(p.get('net_assets', 0) or 0),
            'expense_ratio': float(p.get('net_expense_ratio', 0) or 0),
            'dividend_yield': float(p.get('dividend_yield', 0) or 0),
            'inception_date': p.get('inception_date') or None,
            'sectors': sectors,
            'top_holdings': holdings,
            'fetched_at': now_kst()
        })
        logger.info(f"✅ {symbol} 프로필 수집 (운용규모 {p.get('net_assets')})")
        time.sleep(12)

    if results:
        supabase_upsert('etf_profiles', results)
        logger.info(f"✅ ETF 프로필 {len(results)}건 저장")
    logger.info("=== ETF 프로필 수집 완료 ===")


if __name__ == '__main__':
    main()

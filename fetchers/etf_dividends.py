"""
ETF/종목 배당금 이력 수집기 (Alpha Vantage DIVIDENDS)
출처: alphavantage.co - DIVIDENDS 함수 (ex_dividend_date, declaration_date, record_date, payment_date, amount)

us_technical.py(RSI)와 쿼터를 나누기 위해 별도 키(ALPHA_VANTAGE_API_KEY_2) 사용.
무료티어 25회/일 한도 안에서, config/etf_dividend_tickers.py의 전체 티커를
BATCH_SIZE개씩 로테이션으로 순회한다 (배당 정보는 월 1회 안팎으로만 갱신되므로
매일 전체를 돌 필요가 없고, 며칠 주기로 한 바퀴 도는 것으로 충분).
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from utils.common import supabase_upsert, now_kst, KST
from config.etf_dividend_tickers import SYMBOLS
import requests

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY_2', '')
BASE_URL = "https://www.alphavantage.co/query"

BATCH_SIZE = 25
KEEP_LATEST = 30  # 티커당 보관할 최근 배당 이력 건수 (월배당 기준 약 2년치)


def get_today_batch() -> list:
    """일자 기반 로테이션으로 오늘 처리할 티커 묶음을 결정."""
    num_batches = -(-len(SYMBOLS) // BATCH_SIZE)  # ceil division
    day_index = datetime.now(KST).timetuple().tm_yday % num_batches
    start = day_index * BATCH_SIZE
    return SYMBOLS[start:start + BATCH_SIZE]


def fetch_dividends(symbol: str) -> list:
    params = {'function': 'DIVIDENDS', 'symbol': symbol, 'apikey': API_KEY}
    try:
        res = requests.get(BASE_URL, params=params, timeout=15)
        if res.status_code >= 400:
            logger.error(f"{symbol} 배당 오류 HTTP {res.status_code}")
            return []
        data = res.json()
        if 'Note' in data or 'Information' in data:
            logger.warning(f"{symbol}: 호출한도 도달 또는 상태메시지 - {data.get('Note') or data.get('Information')}")
            return []
        return data.get('data', [])[:KEEP_LATEST]
    except Exception as e:
        logger.error(f"{symbol} 배당 예외: {type(e).__name__}")
        return []


def main():
    logger.info("=== ETF/종목 배당금 이력 수집 시작 (Alpha Vantage) ===")
    batch = get_today_batch()
    logger.info(f"오늘 처리 대상 {len(batch)}개: {batch}")

    results = []
    for symbol in batch:
        entries = fetch_dividends(symbol)
        if not entries:
            logger.warning(f"❌ {symbol}: 배당 데이터 없음")
            time.sleep(12)
            continue
        for e in entries:
            ex_date = e.get('ex_dividend_date')
            amount = e.get('amount')
            if not ex_date or amount in (None, 'None', ''):
                continue
            results.append({
                'ticker': symbol,
                'ex_dividend_date': ex_date,
                'declaration_date': e.get('declaration_date') if e.get('declaration_date') not in (None, 'None') else None,
                'record_date': e.get('record_date') if e.get('record_date') not in (None, 'None') else None,
                'payment_date': e.get('payment_date') if e.get('payment_date') not in (None, 'None') else None,
                'amount': float(amount),
                'fetched_at': now_kst()
            })
        logger.info(f"✅ {symbol} 배당 {len(entries)}건")
        time.sleep(12)

    if results:
        supabase_upsert('etf_dividends', results)
        logger.info(f"✅ 배당 이력 {len(results)}건 저장")
    logger.info("=== ETF/종목 배당금 이력 수집 완료 ===")


if __name__ == '__main__':
    main()

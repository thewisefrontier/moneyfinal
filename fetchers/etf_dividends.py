"""
ETF/종목 배당금 이력 수집기 (Yahoo Finance, yfinance)
출처: finance.yahoo.com (비공식 엔드포인트, yfinance 라이브러리 경유)

기존 Alpha Vantage DIVIDENDS 함수는 무료 티어가 키당 25회/일이라
RSI(us_technical.py)·프로필 수집과 한도를 나눠 쓰면서 여유가 거의 없었고,
수동 재실행 한 번만 해도 바로 한도 초과가 나는 문제가 있었다.
yfinance는 API 키가 필요 없고 공식적인 일일 호출 한도가 없어(비공식
엔드포인트라 과도한 버스트 시 429는 날 수 있음 - 요청 간 sleep으로 대응),
82개 티커 전체를 매일 갱신할 수 있다 (로테이션 불필요).

declaration_date/record_date는 yfinance가 제공하지 않아 None으로 둔다
(프론트엔드에서 실제로 쓰이지 않는 필드 - dividend-*.html은 ex_dividend_date/
payment_date/amount만 사용, payment_date도 없으면 '-'로 표시).
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst
from config.etf_dividend_tickers import SYMBOLS
import yfinance as yf

logger = logging.getLogger(__name__)
KEEP_LATEST = 30  # 티커당 보관할 최근 배당 이력 건수 (월배당 기준 약 2년치)
REQUEST_SLEEP = 0.5  # 비공식 엔드포인트 429 방지용 요청 간 간격


def fetch_dividends(symbol: str) -> list:
    try:
        div = yf.Ticker(symbol).dividends
        if div.empty:
            return []
        div = div.tail(KEEP_LATEST)
        return [{'ex_date': idx.strftime('%Y-%m-%d'), 'amount': float(val)} for idx, val in div.items()]
    except Exception as e:
        logger.error(f"{symbol} 배당 예외: {type(e).__name__}")
        return []


def main():
    logger.info("=== ETF/종목 배당금 이력 수집 시작 (Yahoo Finance) ===")
    logger.info(f"오늘 처리 대상 {len(SYMBOLS)}개 (전체)")

    results = []
    for symbol in SYMBOLS:
        entries = fetch_dividends(symbol)
        if not entries:
            logger.warning(f"❌ {symbol}: 배당 데이터 없음")
            time.sleep(REQUEST_SLEEP)
            continue
        for e in entries:
            results.append({
                'ticker': symbol,
                'ex_dividend_date': e['ex_date'],
                'declaration_date': None,
                'record_date': None,
                'payment_date': None,
                'amount': e['amount'],
                'fetched_at': now_kst()
            })
        logger.info(f"✅ {symbol} 배당 {len(entries)}건")
        time.sleep(REQUEST_SLEEP)

    if results:
        supabase_upsert('etf_dividends', results)
        logger.info(f"✅ 배당 이력 {len(results)}건 저장")
    logger.info("=== ETF/종목 배당금 이력 수집 완료 ===")


if __name__ == '__main__':
    main()

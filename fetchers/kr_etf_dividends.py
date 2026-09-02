"""
국내 상장 배당 ETF 분배금 이력 + 실시간 시세 수집기 (Yahoo Finance, yfinance)
출처: finance.yahoo.com (비공식 엔드포인트, yfinance 경유). API 키 불필요, 일일 한도 없음.

실측 확인(2026-09-02): 국내 ETF는 가격(.history())·분배금(.dividends) 데이터는
정상 제공되지만, 프로필(.info의 netAssets/yield/funds_data 등)은 전부 None -
"No Fund data found" 에러가 남. 그래서 이 fetcher는 분배금+가격만 수집하고
운용규모/보수율 등 프로필은 애초에 시도하지 않는다(미국 ETF와 달리 제공 불가).

declaration_date/record_date/payment_date도 yfinance가 안 줘서 US 배당
계산기(etf_dividends.py)보다 필드가 단순함(ex_date+amount만).
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst
from config.kr_dividend_etf_tickers import SYMBOLS
import yfinance as yf

logger = logging.getLogger(__name__)
KEEP_LATEST = 30
REQUEST_SLEEP = 0.5


def fetch_one(code: str) -> tuple[list, dict | None]:
    ticker = yf.Ticker(f"{code}.KS")
    div_rows = []
    try:
        div = ticker.dividends
        if not div.empty:
            for idx, val in div.tail(KEEP_LATEST).items():
                div_rows.append({
                    'ticker': code,
                    'ex_dividend_date': idx.strftime('%Y-%m-%d'),
                    'amount': float(val),
                    'fetched_at': now_kst()
                })
    except Exception as e:
        logger.error(f"{code} 배당 예외: {type(e).__name__}")

    price_row = None
    try:
        hist = ticker.history(period='5d')
        if not hist.empty:
            close = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else close
            price_row = {
                'ticker': code,
                'price': close,
                'change': round(close - prev, 2),
                'change_pct': round((close - prev) / prev * 100, 2) if prev else 0,
                'base_date': hist.index[-1].strftime('%Y-%m-%d'),
                'fetched_at': now_kst()
            }
    except Exception as e:
        logger.error(f"{code} 시세 예외: {type(e).__name__}")

    return div_rows, price_row


def main():
    logger.info("=== 국내 배당ETF 분배금+시세 수집 시작 (Yahoo Finance) ===")
    all_divs, all_prices = [], []
    for code in SYMBOLS:
        divs, price = fetch_one(code)
        if divs:
            all_divs.extend(divs)
            logger.info(f"✅ {code} 배당 {len(divs)}건")
        else:
            logger.warning(f"❌ {code}: 배당 데이터 없음")
        if price:
            all_prices.append(price)
        time.sleep(REQUEST_SLEEP)

    if all_divs:
        supabase_upsert('kr_etf_dividends', all_divs)
        logger.info(f"✅ 국내 ETF 배당 이력 {len(all_divs)}건 저장")
    if all_prices:
        supabase_upsert('kr_etf_prices', all_prices)
        logger.info(f"✅ 국내 ETF 시세 {len(all_prices)}건 저장")
    logger.info("=== 국내 배당ETF 분배금+시세 수집 완료 ===")


if __name__ == '__main__':
    main()

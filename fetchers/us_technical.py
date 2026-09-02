"""
미국 주식 기술지표 수집기 (yfinance 기반 자체 계산)
출처: Yahoo Finance 가격 이력으로 Wilder RSI(14)를 직접 계산.
2026-09-02 Alpha Vantage에서 전환: 무료키를 etf_profile.py와 나눠 쓰던 시절엔
한도가 빡빡했으나, etf_profile.py가 yfinance로 이전하며 더 이상 급하진 않음.
다만 소스를 하나(Yahoo Finance)로 통일하는 게 유지보수에 낫다고 판단해 같이 전환.
RSI는 표준 Wilder 스무딩(EWM alpha=1/14, adjust=False) 공식이며, 초기화 방식에
따른 오차가 수렴하도록 6개월치 데이터를 받아 마지막 값만 사용한다.
"""
import logging, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst
import yfinance as yf

logger = logging.getLogger(__name__)

US_TICKERS = ['AAPL','MSFT','GOOGL','NVDA','TSLA']
RSI_PERIOD = 14


def fetch_rsi(symbol: str) -> float | None:
    try:
        df = yf.Ticker(symbol).history(period='6mo', interval='1d')
        close = df['Close']
        if len(close) < RSI_PERIOD + 1:
            return None
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD).mean()
        avg_loss = loss.ewm(alpha=1 / RSI_PERIOD, adjust=False, min_periods=RSI_PERIOD).mean()
        last_gain, last_loss = avg_gain.iloc[-1], avg_loss.iloc[-1]
        if last_loss == 0:
            return 100.0
        rs = last_gain / last_loss
        return float(100 - (100 / (1 + rs)))
    except Exception as e:
        logger.error(f"{symbol} RSI 예외: {type(e).__name__} - {e}")
        return None


def main():
    logger.info("=== 미국 주식 RSI 수집 시작 (Yahoo Finance) ===")
    results = []
    for symbol in US_TICKERS:
        rsi = fetch_rsi(symbol)
        if rsi is None:
            logger.warning(f"❌ {symbol}: RSI 없음")
            continue
        results.append({
            'indicator_code': f"US_RSI_{symbol}",
            'indicator_name': f"{symbol} RSI(14)",
            'category': '미국주식기술지표',
            'value': rsi,
            'unit': '',
            'signal': 'red' if rsi>=70 else 'yellow' if rsi<=30 else 'green',
            'source': 'Yahoo Finance',
            'reference_date': today_kst(),
            'summary_text': f"{'과매수' if rsi>=70 else '과매도' if rsi<=30 else '중립'} 구간",
            'fetched_at': now_kst()
        })
        logger.info(f"✅ {symbol} RSI {rsi:.1f}")

    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ RSI {len(results)}건 저장")
    logger.info("=== 미국 주식 RSI 수집 완료 ===")


if __name__ == '__main__': main()

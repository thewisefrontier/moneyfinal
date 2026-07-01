"""
미국 주식 기술지표 수집기 (Alpha Vantage)
출처: alphavantage.co - RSI (공식 필드, 다수 공식예제 교차확인됨)
주의: 무료티어 일일 한도가 문서마다 25회/500회로 상이하게 확인됨 → 가장 보수적인 25회 기준으로 설계.
분당 5회 제한도 문서화되어 있어 호출 간 12초 대기.
하루에 종목 5개만 처리 (RSI만 수집, 매일 돌려도 한도 안에 들도록).
"""
import logging, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst
import requests

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
BASE_URL = "https://www.alphavantage.co/query"

US_TICKERS = ['AAPL','MSFT','GOOGL','NVDA','TSLA']


def fetch_rsi(symbol: str) -> float | None:
    params = {
        'function': 'RSI',
        'symbol': symbol,
        'interval': 'daily',
        'time_period': 14,
        'series_type': 'close',
        'apikey': API_KEY
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=15)
        if res.status_code >= 400:
            logger.error(f"{symbol} RSI 오류 HTTP {res.status_code}")
            return None
        data = res.json()
        if 'Note' in data or 'Information' in data:
            logger.warning(f"{symbol}: 호출한도 도달 또는 상태메시지 - {data.get('Note') or data.get('Information')}")
            return None
        series = data.get('Technical Analysis: RSI', {})
        if not series:
            return None
        latest_date = sorted(series.keys(), reverse=True)[0]
        return float(series[latest_date].get('RSI', 0) or 0)
    except Exception as e:
        logger.error(f"{symbol} RSI 예외: {type(e).__name__}")
        return None


def main():
    logger.info("=== 미국 주식 RSI 수집 시작 (Alpha Vantage) ===")
    results = []
    for symbol in US_TICKERS:
        rsi = fetch_rsi(symbol)
        if rsi is None:
            logger.warning(f"❌ {symbol}: RSI 없음")
            time.sleep(12)
            continue
        results.append({
            'indicator_code': f"US_RSI_{symbol}",
            'indicator_name': f"{symbol} RSI(14)",
            'category': '미국주식기술지표',
            'value': rsi,
            'unit': '',
            'signal': 'red' if rsi>=70 else 'yellow' if rsi<=30 else 'green',
            'source': 'Alpha Vantage',
            'reference_date': today_kst(),
            'summary_text': f"{'과매수' if rsi>=70 else '과매도' if rsi<=30 else '중립'} 구간",
            'fetched_at': now_kst()
        })
        logger.info(f"✅ {symbol} RSI {rsi:.1f}")
        time.sleep(12)

    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ RSI {len(results)}건 저장")
    logger.info("=== 미국 주식 RSI 수집 완료 ===")


if __name__ == '__main__': main()

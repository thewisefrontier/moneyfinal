"""
암호화폐 시세 수집기
출처: CoinGecko 공개 API (무료, 키 불필요, 상업적 이용 가능)
https://api.coingecko.com/api/v3/coins/markets

시가총액 상위 20개를 한 번에 받아서:
1) crypto_prices 테이블에 전체 저장 (전용 페이지 crypto.html용)
2) 그중 BTC/ETH는 기존처럼 market_indicators에도 저장 (market.html 위젯,
   기존 동작 그대로 유지 - 이전엔 별도 simple/price 호출이었는데 같은
   markets() 응답에서 뽑아 쓰도록 통합해 API 호출을 1회로 줄임)
"""
import logging, os, sys
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"
TOP_N = 20
INDICATOR_CODES = {'bitcoin': ('BTC', '비트코인'), 'ethereum': ('ETH', '이더리움')}


def fetch_markets() -> list:
    params = {
        'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': TOP_N, 'page': 1,
        'price_change_percentage': '24h,7d'
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"암호화폐 시세 수집 오류: {type(e).__name__} - {e}")
        return []


def to_crypto_row(c: dict) -> dict:
    return {
        'id': c.get('id'),
        'symbol': (c.get('symbol') or '').upper(),
        'name': c.get('name'),
        'image_url': c.get('image'),
        'current_price': c.get('current_price'),
        'market_cap': c.get('market_cap'),
        'market_cap_rank': c.get('market_cap_rank'),
        'total_volume': c.get('total_volume'),
        'high_24h': c.get('high_24h'),
        'low_24h': c.get('low_24h'),
        'change_pct_24h': c.get('price_change_percentage_24h_in_currency'),
        'change_pct_7d': c.get('price_change_percentage_7d_in_currency'),
        'circulating_supply': c.get('circulating_supply'),
        'ath': c.get('ath'),
        'ath_date': c.get('ath_date'),
        'fetched_at': now_kst()
    }


def to_indicator_row(c: dict, code: str, name: str) -> dict:
    value = float(c.get('current_price') or 0)
    change = float(c.get('price_change_percentage_24h_in_currency') or 0)
    return {
        'indicator_code': code,
        'indicator_name': name,
        'category': '암호화폐',
        'value': value,
        'unit': 'USD',
        'signal': 'red' if change <= -5 else 'yellow' if change <= -2 else 'green',
        'source': 'CoinGecko',
        'reference_date': today_kst(),
        'summary_text': f"{name} ${value:,.2f} ({change:+.2f}%)",
        'fetched_at': now_kst()
    }


def main():
    logger.info("=== 암호화폐 시세 수집 시작 ===")
    coins = fetch_markets()
    if not coins:
        logger.warning("수집된 코인 없음. 종료.")
        return

    crypto_rows = [to_crypto_row(c) for c in coins if c.get('id')]
    if crypto_rows:
        supabase_upsert('crypto_prices', crypto_rows)
        logger.info(f"✅ 코인 시세 {len(crypto_rows)}건 저장")

    indicator_rows = []
    for c in coins:
        meta = INDICATOR_CODES.get(c.get('id'))
        if meta:
            indicator_rows.append(to_indicator_row(c, meta[0], meta[1]))
    if indicator_rows:
        supabase_upsert('market_indicators', indicator_rows)
        logger.info(f"✅ 암호화폐 지표(티커용) {len(indicator_rows)}건 저장")
    logger.info("=== 암호화폐 시세 수집 완료 ===")


if __name__ == '__main__':
    main()

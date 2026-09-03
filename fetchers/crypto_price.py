"""
암호화폐 시세 수집기
1차: CoinGecko 공개 API (무료 Demo 플랜, 키 불필요)
    https://api.coingecko.com/api/v3/coins/markets
    ⚠️ CoinGecko Demo 플랜 약관은 "Personal Use only, not for any commercial
    purpose"로 명시돼 있음(2026-09-04 공식 약관 페이지 확인). moneyfinal은
    광고/제휴 없는 무료 정보 사이트라 상업적 이용으로 보기 어렵다고 판단해
    1차로 유지하지만, 만일을 대비해 2차 폴백을 아래에 붙여둔다.
2차 폴백: yfinance (BTC-USD 등 Yahoo Finance 암호화폐 티커, 키 불필요,
    이번 세션에 이미 여러 fetcher에서 문제없이 검증된 소스)
    필드가 1차보다 적음(7일 변동률 등은 안 채움 - DB 컬럼 다 nullable이라 무해).
3차 폴백: CoinMarketCap 무료 Basic 플랜 (무료 API 키 필요, 상업적 이용 명시
    허용 - moneyfinal이 나중에 광고/제휴 등으로 상업화되면 이쪽을 1차로
    승격하는 걸 권장. 월 15,000회/분당 50회 한도라 1차로 매일 쓰기에도 충분함)
1차/2차가 둘 다 실패했을 때만 호출됨.

시가총액 상위 20개를 한 번에 받아서:
1) crypto_prices 테이블에 전체 저장 (전용 페이지 crypto.html용)
2) 그중 BTC/ETH는 기존처럼 market_indicators에도 저장 (market.html 위젯)

2026-09-04 검토했지만 채택 안 한 것:
- CoinCap: v2(keyless 무료)는 완전히 폐지됨, v3부터 키 필수 + 크립토 결제
  기반 크레딧 시스템으로 전환(2025) - 지금 용도엔 과함
"""
import logging, os, sys
import requests
import yfinance as yf
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
CMC_API_KEY = os.environ.get('CMC_API_KEY', '')
TOP_N = 20
INDICATOR_CODES = {'bitcoin': ('BTC', '비트코인'), 'ethereum': ('ETH', '이더리움')}

# coingecko id를 기본키로 계속 쓰기 위해, 폴백에서도 같은 id로 upsert되도록 매핑.
YF_FALLBACK_COINS = [
    ('bitcoin', 'BTC-USD', 'BTC', 'Bitcoin'),
    ('ethereum', 'ETH-USD', 'ETH', 'Ethereum'),
    ('ripple', 'XRP-USD', 'XRP', 'XRP'),
    ('binancecoin', 'BNB-USD', 'BNB', 'BNB'),
    ('solana', 'SOL-USD', 'SOL', 'Solana'),
    ('dogecoin', 'DOGE-USD', 'DOGE', 'Dogecoin'),
    ('cardano', 'ADA-USD', 'ADA', 'Cardano'),
    ('tron', 'TRX-USD', 'TRX', 'TRON'),
    ('chainlink', 'LINK-USD', 'LINK', 'Chainlink'),
    ('avalanche-2', 'AVAX-USD', 'AVAX', 'Avalanche'),
    ('the-open-network', 'TON-USD', 'TON', 'Toncoin'),
    ('shiba-inu', 'SHIB-USD', 'SHIB', 'Shiba Inu'),
    ('polkadot', 'DOT-USD', 'DOT', 'Polkadot'),
    ('litecoin', 'LTC-USD', 'LTC', 'Litecoin'),
    ('bitcoin-cash', 'BCH-USD', 'BCH', 'Bitcoin Cash'),
    ('stellar', 'XLM-USD', 'XLM', 'Stellar'),
    ('uniswap', 'UNI-USD', 'UNI', 'Uniswap'),
    ('near', 'NEAR-USD', 'NEAR', 'NEAR Protocol'),
    ('ethereum-classic', 'ETC-USD', 'ETC', 'Ethereum Classic'),
    ('internet-computer', 'ICP-USD', 'ICP', 'Internet Computer'),
]


def fetch_markets_primary() -> list:
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
        logger.warning(f"CoinGecko 수집 실패, yfinance 폴백 시도: {type(e).__name__} - {e}")
        return []


def fetch_markets_fallback() -> list:
    results = []
    for cg_id, symbol, code, name in YF_FALLBACK_COINS:
        try:
            info = yf.Ticker(symbol).info
            price = info.get('regularMarketPrice')
            if not price:
                continue
            results.append({
                'id': cg_id, 'symbol': code, 'name': name, 'image': None,
                'current_price': price,
                'market_cap': info.get('marketCap'),
                'market_cap_rank': None,
                'total_volume': info.get('volume24Hr') or info.get('regularMarketVolume'),
                'high_24h': None,  # yfinance dayHigh/dayLow는 코인에서 신뢰도가 낮아 비움
                'low_24h': None,
                'price_change_percentage_24h_in_currency': info.get('regularMarketChangePercent'),
                'price_change_percentage_7d_in_currency': None,
                'circulating_supply': info.get('circulatingSupply'),
                'ath': None, 'ath_date': None,
                '_source': 'Yahoo Finance'
            })
        except Exception as e:
            logger.warning(f"{symbol} yfinance 폴백 실패: {type(e).__name__}")
    # market_cap 기준으로 순위 매김 (1차 API의 market_cap_rank 대체)
    results.sort(key=lambda c: c.get('market_cap') or 0, reverse=True)
    for i, c in enumerate(results, 1):
        c['market_cap_rank'] = i
    return results


def fetch_markets_cmc() -> list:
    if not CMC_API_KEY:
        return []
    try:
        res = requests.get(
            CMC_URL,
            headers={'X-CMC_PRO_API_KEY': CMC_API_KEY},
            params={'limit': TOP_N, 'convert': 'USD'},
            timeout=15
        )
        res.raise_for_status()
        data = res.json().get('data', [])
    except Exception as e:
        logger.warning(f"CoinMarketCap 폴백 실패: {type(e).__name__} - {e}")
        return []
    results = []
    for c in data:
        q = (c.get('quote') or {}).get('USD') or {}
        results.append({
            'id': c.get('slug'),
            'symbol': c.get('symbol'),
            'name': c.get('name'),
            'image': None,
            'current_price': q.get('price'),
            'market_cap': q.get('market_cap'),
            'market_cap_rank': c.get('cmc_rank'),
            'total_volume': q.get('volume_24h'),
            'high_24h': None,
            'low_24h': None,
            'price_change_percentage_24h_in_currency': q.get('percent_change_24h'),
            'price_change_percentage_7d_in_currency': q.get('percent_change_7d'),
            'circulating_supply': c.get('circulating_supply'),
            'ath': None, 'ath_date': None,
        })
    return results


def fetch_markets() -> tuple[list, str]:
    coins = fetch_markets_primary()
    if coins:
        return coins, 'CoinGecko'
    coins = fetch_markets_fallback()
    if coins:
        logger.info("yfinance 폴백으로 수집 완료")
        return coins, 'Yahoo Finance'
    coins = fetch_markets_cmc()
    if coins:
        logger.info("CoinMarketCap 폴백으로 수집 완료")
    return coins, 'CoinMarketCap'


def to_crypto_row(c: dict, source: str) -> dict:
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
        'source': source,
        'fetched_at': now_kst()
    }


def to_indicator_row(c: dict, code: str, name: str, source: str) -> dict:
    value = float(c.get('current_price') or 0)
    change = float(c.get('price_change_percentage_24h_in_currency') or 0)
    return {
        'indicator_code': code,
        'indicator_name': name,
        'category': '암호화폐',
        'value': value,
        'unit': 'USD',
        'signal': 'red' if change <= -5 else 'yellow' if change <= -2 else 'green',
        'source': source,
        'reference_date': today_kst(),
        'summary_text': f"{name} ${value:,.2f} ({change:+.2f}%)",
        'fetched_at': now_kst()
    }


def main():
    logger.info("=== 암호화폐 시세 수집 시작 ===")
    coins, source = fetch_markets()
    if not coins:
        logger.warning("수집된 코인 없음(1차/2차 모두 실패). 종료.")
        return

    crypto_rows = [to_crypto_row(c, source) for c in coins if c.get('id')]
    if crypto_rows:
        supabase_upsert('crypto_prices', crypto_rows)
        logger.info(f"✅ 코인 시세 {len(crypto_rows)}건 저장 (출처: {source})")

    indicator_rows = []
    for c in coins:
        meta = INDICATOR_CODES.get(c.get('id'))
        if meta:
            indicator_rows.append(to_indicator_row(c, meta[0], meta[1], source))
    if indicator_rows:
        supabase_upsert('market_indicators', indicator_rows)
        logger.info(f"✅ 암호화폐 지표(티커용) {len(indicator_rows)}건 저장")
    logger.info("=== 암호화폐 시세 수집 완료 ===")


if __name__ == '__main__':
    main()

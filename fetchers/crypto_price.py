"""
암호화폐 시세 수집기
출처: CoinGecko 공개 API (무료, 키 불필요, 상업적 이용 가능)
https://api.coingecko.com/api/v3/simple/price
"""
import logging, os, sys
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst

logger = logging.getLogger(__name__)
BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

COINS = [
    {'id': 'bitcoin', 'indicator_code': 'BTC', 'indicator_name': '비트코인'},
    {'id': 'ethereum', 'indicator_code': 'ETH', 'indicator_name': '이더리움'},
]


def fetch_prices() -> list:
    ids = ','.join(c['id'] for c in COINS)
    params = {'ids': ids, 'vs_currencies': 'usd', 'include_24hr_change': 'true'}
    try:
        res = requests.get(BASE_URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        results = []
        for coin in COINS:
            info = data.get(coin['id'])
            if not info or 'usd' not in info:
                logger.warning(f"{coin['indicator_name']}: 데이터 없음")
                continue
            value = float(info['usd'])
            change = float(info.get('usd_24h_change', 0) or 0)
            results.append({
                'indicator_code': coin['indicator_code'],
                'indicator_name': coin['indicator_name'],
                'category': '암호화폐',
                'value': value,
                'unit': 'USD',
                'signal': 'red' if change <= -5 else 'yellow' if change <= -2 else 'green',
                'source': 'CoinGecko',
                'reference_date': today_kst(),
                'summary_text': f"{coin['indicator_name']} ${value:,.2f} ({change:+.2f}%)",
                'fetched_at': now_kst()
            })
        return results
    except Exception as e:
        logger.error(f"암호화폐 시세 수집 오류: {type(e).__name__}")
        return []


def main():
    logger.info("=== 암호화폐 시세 수집 시작 ===")
    results = fetch_prices()
    if results:
        supabase_upsert('market_indicators', results)
        logger.info(f"✅ 암호화폐 {len(results)}건 저장")
    logger.info("=== 암호화폐 시세 수집 완료 ===")


if __name__ == '__main__':
    main()

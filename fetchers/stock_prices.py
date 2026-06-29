"""
주식 시세 및 기업정보 수집기
- 금융위원회_주식시세정보 (공공데이터포털)
- 금융위원회_KRX상장종목정보 (공공데이터포털)
출처: data.go.kr
"""
import logging
import os
import sys
from datetime import datetime, timedelta
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common import supabase_upsert, now_kst, today_kst, data_go_kr_get

logger = logging.getLogger(__name__)
API_KEY = os.environ.get('FSS_API_KEY', '')
KST = pytz.timezone('Asia/Seoul')
BASE_URL = "https://apis.data.go.kr/1160100/service"


def get_base_date() -> str:
    now = datetime.now(KST)
    if now.weekday() == 0:   base = now - timedelta(days=3)
    elif now.weekday() == 6: base = now - timedelta(days=2)
    elif now.weekday() == 5: base = now - timedelta(days=1)
    else:                    base = now - timedelta(days=1)
    return base.strftime('%Y%m%d')


def fetch_stock_prices(market: str, base_date: str, num_rows: int = 200) -> list:
    url = f"{BASE_URL}/GetStockSecuritiesInfoService/getStockPriceInfo"
    params = {
        'resultType': 'json',
        'numOfRows': num_rows,
        'pageNo': 1,
        'basDt': base_date,
        'mrktCls': market,
    }
    try:
        res = data_go_kr_get(url, API_KEY, params, timeout=20)
        res.raise_for_status()
        data = res.json()
        body = data.get('response', {}).get('body', {})
        if not body.get('totalCount', 0):
            logger.warning(f"{market} 시세: 데이터 없음")
            return []
        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        return items
    except Exception as e:
        logger.error(f"{market} 시세 수집 오류: {type(e).__name__}")
        return []


def process_stock_prices(items: list, market: str, base_date: str) -> list:
    results = []
    for item in items:
        try:
            results.append({
                'stock_code':   item.get('srtnCd', ''),
                'stock_name':   item.get('itmsNm', ''),
                'base_date':    f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
                'close_price':  float(item.get('clpr', 0) or 0),
                'open_price':   float(item.get('mkp', 0) or 0),
                'high_price':   float(item.get('hipr', 0) or 0),
                'low_price':    float(item.get('lopr', 0) or 0),
                'vs':           float(item.get('vs', 0) or 0),
                'flt_rt':       float(item.get('fltRt', 0) or 0),
                'volume':       int(item.get('trqu', 0) or 0),
                'trade_amount': int(item.get('trPrc', 0) or 0),
                'market_cap':   int(item.get('mrktTotAmt', 0) or 0),
                'shares_out':   int(item.get('lstgStCnt', 0) or 0),
                'market_type':  market,
                'fetched_at':   now_kst()
            })
        except Exception as e:
            logger.error(f"종목 처리 오류: {e}")
    return results


def fetch_krx_stocks() -> list:
    url = f"{BASE_URL}/GetKrxListedInfoService/getItemInfo"
    results = []
    for market in ['KOSPI', 'KOSDAQ']:
        params = {
            'resultType': 'json',
            'numOfRows': 2000,
            'pageNo': 1,
            'mrktCtg': market,
        }
        try:
            res = data_go_kr_get(url, API_KEY, params, timeout=20)
            res.raise_for_status()
            data = res.json()
            body = data.get('response', {}).get('body', {})
            items = body.get('items', {}).get('item', [])
            if isinstance(items, dict):
                items = [items]
            for item in items:
                stock_code = item.get('srtnCd', '')
                if not stock_code:
                    continue
                results.append({
                    'isin_code':   item.get('isinCd', ''),
                    'stock_code':  stock_code,
                    'stock_name':  item.get('itmsNm', ''),
                    'market_type': market,
                    'corp_name':   item.get('corpNm', item.get('itmsNm', '')),
                    'listed_date': item.get('lstgDt', None),
                    'fetched_at':  now_kst()
                })
            logger.info(f"{market} 상장종목 {len(items)}건")
        except Exception as e:
            logger.error(f"{market} 종목 수집 오류: {type(e).__name__}")
    return results


def main():
    logger.info("=== 주식 시세 수집 시작 ===")
    base_date = get_base_date()
    logger.info(f"기준일: {base_date}")
    all_prices = []
    for market in ['KOSPI', 'KOSDAQ']:
        items = fetch_stock_prices(market, base_date)
        if items:
            processed = process_stock_prices(items, market, base_date)
            all_prices.extend(processed)
            logger.info(f"✅ {market}: {len(processed)}건")
        else:
            logger.warning(f"❌ {market}: 데이터 없음")
    if all_prices:
        supabase_upsert('stock_prices', all_prices)
    stocks = fetch_krx_stocks()
    if stocks:
        supabase_upsert('stocks', stocks)
        logger.info(f"✅ 상장종목 {len(stocks)}건")
    logger.info("=== 주식 시세 수집 완료 ===")


if __name__ == '__main__':
    main()
